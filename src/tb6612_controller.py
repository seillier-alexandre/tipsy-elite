# -*- coding: utf-8 -*-
"""
Contrôleur TB6612FNG pour machine à cocktails
Gestion avancée des pompes péristaltiques avec contrôle PWM précis
Architecture haute performance et sécurisée
"""
import logging
import time
import threading
from typing import Dict, Optional
from contextlib import contextmanager
from dataclasses import dataclass

try:
    import RPi.GPIO as GPIO
except ImportError:
    # Mode simulation si RPi.GPIO n'est pas disponible
    class MockGPIO:
        BCM = "BCM"
        OUT = "OUT"
        LOW = 0
        HIGH = 1
        PWM = None
        
        @staticmethod
        def setmode(mode): pass
        @staticmethod
        def setwarnings(flag): pass
        @staticmethod
        def setup(pin, mode, **kwargs): pass
        @staticmethod
        def output(pin, value): pass
        @staticmethod
        def cleanup(): pass
    
    GPIO = MockGPIO()
    logger.warning("RPi.GPIO non disponible - Mode simulation activé")

from hardware_config import (
    TB6612_CONTROLLERS, PUMP_CONFIGS, PWM_CONFIG, TIMING_CONFIG,
    TB6612FNGConfig, PumpConfig, get_pump_by_id
)

logger = logging.getLogger(__name__)

@dataclass
class PumpStatus:
    """État d'une pompe"""
    is_running: bool = False
    direction: str = 'forward'  # 'forward', 'reverse', 'stopped'
    speed_percent: int = 0
    volume_dispensed: float = 0.0
    total_runtime: float = 0.0
    last_started: Optional[float] = None
    error_state: bool = False
    error_message: str = ""

class TB6612Controller:
    """Contrôleur pour module TB6612FNG (2 moteurs par module)"""
    
    def __init__(self, config: TB6612FNGConfig, controller_id: int):
        self.config = config
        self.controller_id = controller_id
        self.pwm_a: Optional[GPIO.PWM] = None
        self.pwm_b: Optional[GPIO.PWM] = None
        self.is_initialized = False
        self.standby_active = True
        self._lock = threading.RLock()
        
        # États des moteurs
        self.motor_a_status = PumpStatus()
        self.motor_b_status = PumpStatus()
        
    def initialize(self) -> bool:
        """Initialise le contrôleur TB6612FNG"""
        try:
            with self._lock:
                if self.is_initialized:
                    return True
                
                # Configuration des pins de direction
                GPIO.setup(self.config.ain1, GPIO.OUT, initial=GPIO.LOW)
                GPIO.setup(self.config.ain2, GPIO.OUT, initial=GPIO.LOW)
                GPIO.setup(self.config.bin1, GPIO.OUT, initial=GPIO.LOW)
                GPIO.setup(self.config.bin2, GPIO.OUT, initial=GPIO.LOW)
                GPIO.setup(self.config.stby, GPIO.OUT, initial=GPIO.LOW)
                
                # Configuration des pins PWM
                GPIO.setup(self.config.pwma, GPIO.OUT)
                GPIO.setup(self.config.pwmb, GPIO.OUT)
                
                # Initialisation PWM
                self.pwm_a = GPIO.PWM(self.config.pwma, PWM_CONFIG['frequency'])
                self.pwm_b = GPIO.PWM(self.config.pwmb, PWM_CONFIG['frequency'])
                
                self.pwm_a.start(0)
                self.pwm_b.start(0)
                
                # Sortir du mode standby
                self.enable()
                
                self.is_initialized = True
                logger.info(f"Contrôleur TB6612 {self.controller_id} initialisé")
                return True
                
        except Exception as e:
            logger.error(f"Erreur initialisation contrôleur {self.controller_id}: {e}")
            return False
    
    def enable(self):
        """Active le contrôleur (sort du mode standby)"""
        with self._lock:
            GPIO.output(self.config.stby, GPIO.HIGH)
            self.standby_active = False
            time.sleep(TIMING_CONFIG['pump_startup_delay'])
    
    def disable(self):
        """Désactive le contrôleur (mode standby)"""
        with self._lock:
            self._stop_all_motors()
            GPIO.output(self.config.stby, GPIO.LOW)
            self.standby_active = True
    
    def _stop_all_motors(self):
        """Arrête tous les moteurs du contrôleur"""
        # Arrêt moteur A
        GPIO.output(self.config.ain1, GPIO.LOW)
        GPIO.output(self.config.ain2, GPIO.LOW)
        if self.pwm_a:
            self.pwm_a.ChangeDutyCycle(0)
        self.motor_a_status.is_running = False
        self.motor_a_status.direction = 'stopped'
        self.motor_a_status.speed_percent = 0
        
        # Arrêt moteur B
        GPIO.output(self.config.bin1, GPIO.LOW)
        GPIO.output(self.config.bin2, GPIO.LOW)
        if self.pwm_b:
            self.pwm_b.ChangeDutyCycle(0)
        self.motor_b_status.is_running = False
        self.motor_b_status.direction = 'stopped'
        self.motor_b_status.speed_percent = 0
    
    def set_motor_speed(self, channel: str, speed_percent: int, direction: str = 'forward') -> bool:
        """
        Contrôle un moteur
        Args:
            channel: 'A' ou 'B'
            speed_percent: Vitesse en pourcentage (0-100)
            direction: 'forward' ou 'reverse'
        """
        try:
            with self._lock:
                if not self.is_initialized:
                    logger.error(f"Contrôleur {self.controller_id} non initialisé")
                    return False
                
                if self.standby_active:
                    self.enable()
                
                # Validation des paramètres
                speed_percent = max(0, min(100, speed_percent))
                if speed_percent < PWM_CONFIG['min_duty_cycle'] and speed_percent > 0:
                    speed_percent = PWM_CONFIG['min_duty_cycle']
                
                if channel == 'A':
                    return self._set_motor_a(speed_percent, direction)
                elif channel == 'B':
                    return self._set_motor_b(speed_percent, direction)
                else:
                    logger.error(f"Canal moteur invalide: {channel}")
                    return False
                    
        except Exception as e:
            logger.error(f"Erreur contrôle moteur {channel} contrôleur {self.controller_id}: {e}")
            return False
    
    def _set_motor_a(self, speed_percent: int, direction: str) -> bool:
        """Contrôle le moteur A"""
        if direction == 'forward':
            GPIO.output(self.config.ain1, GPIO.HIGH)
            GPIO.output(self.config.ain2, GPIO.LOW)
        elif direction == 'reverse':
            GPIO.output(self.config.ain1, GPIO.LOW)
            GPIO.output(self.config.ain2, GPIO.HIGH)
        else:  # stop
            GPIO.output(self.config.ain1, GPIO.LOW)
            GPIO.output(self.config.ain2, GPIO.LOW)
            speed_percent = 0
        
        if self.pwm_a:
            self.pwm_a.ChangeDutyCycle(speed_percent)
        
        # Mise à jour du statut
        self.motor_a_status.is_running = speed_percent > 0
        self.motor_a_status.direction = direction if speed_percent > 0 else 'stopped'
        self.motor_a_status.speed_percent = speed_percent
        
        return True
    
    def _set_motor_b(self, speed_percent: int, direction: str) -> bool:
        """Contrôle le moteur B"""
        if direction == 'forward':
            GPIO.output(self.config.bin1, GPIO.HIGH)
            GPIO.output(self.config.bin2, GPIO.LOW)
        elif direction == 'reverse':
            GPIO.output(self.config.bin1, GPIO.LOW)
            GPIO.output(self.config.bin2, GPIO.HIGH)
        else:  # stop
            GPIO.output(self.config.bin1, GPIO.LOW)
            GPIO.output(self.config.bin2, GPIO.LOW)
            speed_percent = 0
        
        if self.pwm_b:
            self.pwm_b.ChangeDutyCycle(speed_percent)
        
        # Mise à jour du statut
        self.motor_b_status.is_running = speed_percent > 0
        self.motor_b_status.direction = direction if speed_percent > 0 else 'stopped'
        self.motor_b_status.speed_percent = speed_percent
        
        return True
    
    def stop_motor(self, channel: str) -> bool:
        """Arrête un moteur spécifique"""
        return self.set_motor_speed(channel, 0, 'stopped')
    
    def stop_all(self):
        """Arrête tous les moteurs du contrôleur"""
        with self._lock:
            self._stop_all_motors()
    
    def get_motor_status(self, channel: str) -> Optional[PumpStatus]:
        """Récupère le statut d'un moteur"""
        if channel == 'A':
            return self.motor_a_status
        elif channel == 'B':
            return self.motor_b_status
        return None
    
    def cleanup(self):
        """Nettoyage des ressources"""
        with self._lock:
            if self.is_initialized:
                self._stop_all_motors()
                if self.pwm_a:
                    self.pwm_a.stop()
                if self.pwm_b:
                    self.pwm_b.stop()
                self.disable()
                self.is_initialized = False

class PumpManager:
    """Gestionnaire principal des pompes avec TB6612FNG"""
    
    def __init__(self):
        self.controllers: Dict[int, TB6612Controller] = {}
        self.pumps: Dict[int, PumpConfig] = {}
        self.is_initialized = False
        self._global_lock = threading.RLock()
        self._emergency_stop = False
        
        # Charger les configurations
        for i, controller_config in enumerate(TB6612_CONTROLLERS):
            self.controllers[i] = TB6612Controller(controller_config, i)
        
        for pump in PUMP_CONFIGS:
            self.pumps[pump.pump_id] = pump
    
    def initialize(self) -> bool:
        """Initialise tous les contrôleurs"""
        try:
            with self._global_lock:
                if self.is_initialized:
                    return True
                
                # Configuration GPIO
                GPIO.setmode(GPIO.BCM)
                GPIO.setwarnings(False)
                
                # Initialiser tous les contrôleurs
                success_count = 0
                for controller in self.controllers.values():
                    if controller.initialize():
                        success_count += 1
                
                if success_count == len(self.controllers):
                    self.is_initialized = True
                    logger.info(f"✅ Tous les contrôleurs TB6612 initialisés ({success_count}/{len(self.controllers)})")
                    return True
                else:
                    logger.error(f"❌ Échec initialisation: {success_count}/{len(self.controllers)} contrôleurs")
                    return False
                    
        except Exception as e:
            logger.error(f"Erreur initialisation PumpManager: {e}")
            return False
    
    def start_pump(self, pump_id: int, speed_percent: int = 100) -> bool:
        """Démarre une pompe"""
        try:
            if self._emergency_stop:
                logger.warning("Arrêt d'urgence activé - pompe non démarrée")
                return False
            
            pump = self.pumps.get(pump_id)
            if not pump:
                logger.error(f"Pompe {pump_id} non trouvée")
                return False
            
            controller = self.controllers.get(pump.tb6612_controller)
            if not controller:
                logger.error(f"Contrôleur {pump.tb6612_controller} non trouvé pour pompe {pump_id}")
                return False
            
            # Ajuster la vitesse selon le calibrage
            adjusted_speed = int(speed_percent * pump.calibration_factor)
            adjusted_speed = max(PWM_CONFIG['min_duty_cycle'], min(PWM_CONFIG['max_duty_cycle'], adjusted_speed))
            
            success = controller.set_motor_speed(pump.motor_channel, adjusted_speed, 'forward')
            
            if success:
                logger.info(f"Pompe {pump_id} ({pump.ingredient}) démarrée à {adjusted_speed}%")
                
                # Marquer l'heure de démarrage
                status = controller.get_motor_status(pump.motor_channel)
                if status:
                    status.last_started = time.time()
            
            return success
            
        except Exception as e:
            logger.error(f"Erreur démarrage pompe {pump_id}: {e}")
            return False
    
    def stop_pump(self, pump_id: int) -> bool:
        """Arrête une pompe"""
        try:
            pump = self.pumps.get(pump_id)
            if not pump:
                logger.error(f"Pompe {pump_id} non trouvée")
                return False
            
            controller = self.controllers.get(pump.tb6612_controller)
            if not controller:
                logger.error(f"Contrôleur {pump.tb6612_controller} non trouvé")
                return False
            
            success = controller.stop_motor(pump.motor_channel)
            
            if success:
                logger.info(f"Pompe {pump_id} ({pump.ingredient}) arrêtée")
                
                # Calculer le temps de fonctionnement
                status = controller.get_motor_status(pump.motor_channel)
                if status and status.last_started:
                    runtime = time.time() - status.last_started
                    status.total_runtime += runtime
                    status.last_started = None
            
            time.sleep(TIMING_CONFIG['pump_shutdown_delay'])
            return success
            
        except Exception as e:
            logger.error(f"Erreur arrêt pompe {pump_id}: {e}")
            return False
    
    def pour_volume(self, pump_id: int, volume_ml: float, speed_percent: int = 100) -> bool:
        """Verse un volume précis avec une pompe"""
        try:
            pump = self.pumps.get(pump_id)
            if not pump:
                logger.error(f"Pompe {pump_id} non trouvée")
                return False
            
            if volume_ml <= 0:
                logger.warning(f"Volume invalide: {volume_ml}ml")
                return True
            
            # Calculer le temps de versement
            pour_time = volume_ml / pump.effective_flow_rate
            
            if pour_time > TIMING_CONFIG['max_pour_time']:
                logger.error(f"Temps versement trop long: {pour_time}s (max: {TIMING_CONFIG['max_pour_time']}s)")
                return False
            
            logger.info(f"Versement {volume_ml}ml de {pump.ingredient} (temps: {pour_time:.2f}s)")
            
            # Démarrer la pompe
            if not self.start_pump(pump_id, speed_percent):
                return False
            
            # Attendre le temps calculé
            time.sleep(pour_time)
            
            # Arrêter la pompe
            if not self.stop_pump(pump_id):
                logger.warning(f"Attention: échec arrêt pompe {pump_id}")
                return False
            
            # Mettre à jour le volume versé
            controller = self.controllers.get(pump.tb6612_controller)
            if controller:
                status = controller.get_motor_status(pump.motor_channel)
                if status:
                    status.volume_dispensed += volume_ml
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur versement pompe {pump_id}: {e}")
            self.stop_pump(pump_id)  # Sécurité
            return False
    
    def emergency_stop(self):
        """Arrêt d'urgence de toutes les pompes"""
        logger.warning("🚨 ARRÊT D'URGENCE ACTIVÉ")
        self._emergency_stop = True
        
        with self._global_lock:
            for controller in self.controllers.values():
                try:
                    controller.stop_all()
                except Exception as e:
                    logger.error(f"Erreur arrêt d'urgence contrôleur {controller.controller_id}: {e}")
    
    def reset_emergency_stop(self):
        """Réinitialise l'arrêt d'urgence"""
        logger.info("Réinitialisation arrêt d'urgence")
        self._emergency_stop = False
    
    def get_pump_status(self, pump_id: int) -> Optional[PumpStatus]:
        """Récupère le statut d'une pompe"""
        pump = self.pumps.get(pump_id)
        if not pump:
            return None
        
        controller = self.controllers.get(pump.tb6612_controller)
        if not controller:
            return None
        
        return controller.get_motor_status(pump.motor_channel)
    
    def get_all_pump_status(self) -> Dict[int, PumpStatus]:
        """Récupère le statut de toutes les pompes"""
        status_dict = {}
        for pump_id in self.pumps.keys():
            status = self.get_pump_status(pump_id)
            if status:
                status_dict[pump_id] = status
        return status_dict
    
    def cleanup(self):
        """Nettoyage complet du système"""
        logger.info("Nettoyage du système de pompes")
        
        with self._global_lock:
            for controller in self.controllers.values():
                try:
                    controller.cleanup()
                except Exception as e:
                    logger.error(f"Erreur nettoyage contrôleur {controller.controller_id}: {e}")
            
            try:
                GPIO.cleanup()
            except Exception as e:
                logger.error(f"Erreur nettoyage GPIO: {e}")
            
            self.is_initialized = False

# Instance globale du gestionnaire de pompes
pump_manager = PumpManager()

@contextmanager
def pump_operation():
    """Context manager pour opérations sécurisées des pompes"""
    try:
        if not pump_manager.is_initialized:
            if not pump_manager.initialize():
                raise RuntimeError("Échec initialisation système de pompes")
        yield pump_manager
    except Exception as e:
        logger.error(f"Erreur opération pompe: {e}")
        pump_manager.emergency_stop()
        raise
    finally:
        # Pas de cleanup automatique ici pour permettre les opérations séquentielles
        pass

def initialize_pump_system() -> bool:
    """Initialise le système de pompes"""
    return pump_manager.initialize()

def cleanup_pump_system():
    """Nettoie le système de pompes"""
    pump_manager.cleanup()

# Gestion des signaux pour nettoyage propre
import atexit
import signal
import sys

def signal_handler(signum, _frame):
    """Gestionnaire de signaux pour arrêt propre"""
    logger.info(f"Signal {signum} reçu - Arrêt du système")
    cleanup_pump_system()
    sys.exit(0)

# Enregistrement des gestionnaires
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
atexit.register(cleanup_pump_system)