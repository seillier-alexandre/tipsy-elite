#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════
SYSTÈME DE CONTRÔLE DES POMPES - MACHINE À COCKTAIL KIVY
Gestion GPIO pour TB6612FNG et pompes péristaltiques
Intégration complète avec interface Art Déco
═══════════════════════════════════════════════════════════════
"""

import asyncio
import logging
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager
import threading
from enum import Enum

logger = logging.getLogger(__name__)

# Configuration GPIO par défaut
DEFAULT_GPIO_CONFIG = {
    'pump_1': {'pwm_pin': 18, 'in1_pin': 22, 'in2_pin': 23, 'ingredient': 'Gin', 'flow_rate_ml_s': 2.5},
    'pump_2': {'pwm_pin': 19, 'in1_pin': 24, 'in2_pin': 25, 'ingredient': 'Vodka', 'flow_rate_ml_s': 2.5},
    'pump_3': {'pwm_pin': 13, 'in1_pin': 5, 'in2_pin': 6, 'ingredient': 'Rhum', 'flow_rate_ml_s': 2.5},
    'pump_4': {'pwm_pin': 12, 'in1_pin': 16, 'in2_pin': 20, 'ingredient': 'Whisky', 'flow_rate_ml_s': 2.5},
    'pump_5': {'pwm_pin': 4, 'in1_pin': 17, 'in2_pin': 27, 'ingredient': 'Tequila', 'flow_rate_ml_s': 2.5},
    'pump_6': {'pwm_pin': 21, 'in1_pin': 26, 'in2_pin': 19, 'ingredient': 'Brandy', 'flow_rate_ml_s': 2.5},
    'pump_7': {'pwm_pin': 15, 'in1_pin': 14, 'in2_pin': 2, 'ingredient': 'Sprite', 'flow_rate_ml_s': 3.0},
    'pump_8': {'pwm_pin': 3, 'in1_pin': 9, 'in2_pin': 10, 'ingredient': 'Coca Cola', 'flow_rate_ml_s': 3.0},
    'pump_9': {'pwm_pin': 11, 'in1_pin': 8, 'in2_pin': 7, 'ingredient': 'Jus d\'orange', 'flow_rate_ml_s': 3.0},
    'pump_10': {'pwm_pin': 1, 'in1_pin': 0, 'in2_pin': 28, 'ingredient': 'Grenadine', 'flow_rate_ml_s': 2.0}
}

class PumpStatus(Enum):
    """Statuts possibles d'une pompe"""
    IDLE = "idle"
    PUMPING = "pumping"
    ERROR = "error"
    DISABLED = "disabled"
    CALIBRATING = "calibrating"

@dataclass
class PumpConfig:
    """Configuration d'une pompe"""
    id: str
    pwm_pin: int
    in1_pin: int
    in2_pin: int
    ingredient: str
    flow_rate_ml_s: float = 2.5
    max_volume_ml: float = 1000.0
    calibration_factor: float = 1.0
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class PumpOperation:
    """Opération de pompe en cours"""
    pump_id: str
    target_volume_ml: float
    start_time: float
    estimated_duration_s: float
    current_volume_ml: float = 0.0
    status: PumpStatus = PumpStatus.PUMPING

class MockGPIO:
    """Mock GPIO pour développement sans Raspberry Pi"""
    
    BCM = "BCM"
    OUT = "OUT"
    IN = "IN"
    HIGH = 1
    LOW = 0
    
    def __init__(self):
        self.pins = {}
        self.pwm_instances = {}
        
    def setmode(self, mode):
        logger.debug(f"Mock GPIO: setmode({mode})")
    
    def setup(self, pin, mode, pull_up_down=None):
        self.pins[pin] = {'mode': mode, 'value': self.LOW}
        logger.debug(f"Mock GPIO: setup pin {pin} as {mode}")
    
    def output(self, pin, value):
        if pin in self.pins:
            self.pins[pin]['value'] = value
        logger.debug(f"Mock GPIO: pin {pin} = {value}")
    
    def PWM(self, pin, frequency):
        pwm = MockPWM(pin, frequency)
        self.pwm_instances[pin] = pwm
        logger.debug(f"Mock GPIO: PWM created for pin {pin} at {frequency}Hz")
        return pwm
    
    def cleanup(self):
        logger.debug("Mock GPIO: cleanup")
        self.pins.clear()
        for pwm in self.pwm_instances.values():
            pwm.stop()
        self.pwm_instances.clear()

class MockPWM:
    """Mock PWM pour développement"""
    
    def __init__(self, pin, frequency):
        self.pin = pin
        self.frequency = frequency
        self.running = False
        self.duty_cycle = 0
    
    def start(self, duty_cycle):
        self.duty_cycle = duty_cycle
        self.running = True
        logger.debug(f"Mock PWM: pin {self.pin} started at {duty_cycle}% duty cycle")
    
    def ChangeDutyCycle(self, duty_cycle):
        self.duty_cycle = duty_cycle
        logger.debug(f"Mock PWM: pin {self.pin} duty cycle = {duty_cycle}%")
    
    def stop(self):
        self.running = False
        logger.debug(f"Mock PWM: pin {self.pin} stopped")

class TB6612Controller:
    """Contrôleur pour driver moteur TB6612FNG"""
    
    def __init__(self, pwm_pin: int, in1_pin: int, in2_pin: int, use_mock: bool = False):
        self.pwm_pin = pwm_pin
        self.in1_pin = in1_pin
        self.in2_pin = in2_pin
        self.use_mock = use_mock
        
        # Initialiser GPIO
        try:
            if use_mock:
                self.GPIO = MockGPIO()
                logger.info(f"TB6612 {pwm_pin}: Utilisation Mock GPIO")
            else:
                import RPi.GPIO as GPIO
                self.GPIO = GPIO
                logger.info(f"TB6612 {pwm_pin}: Utilisation GPIO réel")
        except ImportError:
            logger.warning("RPi.GPIO non disponible, utilisation Mock GPIO")
            self.GPIO = MockGPIO()
            self.use_mock = True
        
        self._setup_pins()
        self.pwm = None
        self.is_running = False
        
    def _setup_pins(self):
        """Configure les pins GPIO"""
        try:
            self.GPIO.setmode(self.GPIO.BCM)
            self.GPIO.setup(self.pwm_pin, self.GPIO.OUT)
            self.GPIO.setup(self.in1_pin, self.GPIO.OUT)
            self.GPIO.setup(self.in2_pin, self.GPIO.OUT)
            
            # État initial: arrêt
            self.GPIO.output(self.in1_pin, self.GPIO.LOW)
            self.GPIO.output(self.in2_pin, self.GPIO.LOW)
            
            logger.debug(f"TB6612 {self.pwm_pin}: Pins configurées")
            
        except Exception as e:
            logger.error(f"Erreur configuration pins TB6612 {self.pwm_pin}: {e}")
            raise
    
    def start(self, speed: int = 80, direction: str = "forward"):
        """Démarre la pompe"""
        try:
            if self.is_running:
                self.stop()
            
            # Créer PWM si nécessaire
            if self.pwm is None:
                self.pwm = self.GPIO.PWM(self.pwm_pin, 1000)  # 1kHz
            
            # Configurer direction
            if direction == "forward":
                self.GPIO.output(self.in1_pin, self.GPIO.HIGH)
                self.GPIO.output(self.in2_pin, self.GPIO.LOW)
            else:
                self.GPIO.output(self.in1_pin, self.GPIO.LOW)
                self.GPIO.output(self.in2_pin, self.GPIO.HIGH)
            
            # Démarrer PWM
            speed = max(0, min(100, speed))  # Limiter entre 0-100%
            self.pwm.start(speed)
            self.is_running = True
            
            logger.debug(f"TB6612 {self.pwm_pin}: Démarré (vitesse={speed}%, direction={direction})")
            
        except Exception as e:
            logger.error(f"Erreur démarrage TB6612 {self.pwm_pin}: {e}")
            raise
    
    def stop(self):
        """Arrête la pompe"""
        try:
            if self.pwm:
                self.pwm.stop()
            
            self.GPIO.output(self.in1_pin, self.GPIO.LOW)
            self.GPIO.output(self.in2_pin, self.GPIO.LOW)
            
            self.is_running = False
            logger.debug(f"TB6612 {self.pwm_pin}: Arrêté")
            
        except Exception as e:
            logger.error(f"Erreur arrêt TB6612 {self.pwm_pin}: {e}")
    
    def set_speed(self, speed: int):
        """Modifie la vitesse pendant le fonctionnement"""
        if self.is_running and self.pwm:
            speed = max(0, min(100, speed))
            self.pwm.ChangeDutyCycle(speed)
            logger.debug(f"TB6612 {self.pwm_pin}: Vitesse = {speed}%")
    
    def cleanup(self):
        """Nettoie les ressources"""
        try:
            self.stop()
            if hasattr(self.GPIO, 'cleanup') and not self.use_mock:
                # Ne pas faire cleanup complet, juste arrêter cette pompe
                pass
        except Exception as e:
            logger.error(f"Erreur cleanup TB6612 {self.pwm_pin}: {e}")

class Pump:
    """Pompe péristaltique avec contrôle précis"""
    
    def __init__(self, config: PumpConfig, use_mock: bool = False):
        self.config = config
        self.controller = TB6612Controller(
            config.pwm_pin, config.in1_pin, config.in2_pin, use_mock
        )
        self.status = PumpStatus.IDLE
        self.current_operation: Optional[PumpOperation] = None
        self._lock = asyncio.Lock()
        
    async def pour_volume(self, volume_ml: float, speed: int = 80) -> bool:
        """Verse un volume précis"""
        async with self._lock:
            try:
                if not self.config.enabled:
                    logger.warning(f"Pompe {self.config.id} désactivée")
                    return False
                
                if self.status != PumpStatus.IDLE:
                    logger.warning(f"Pompe {self.config.id} occupée")
                    return False
                
                # Calculer durée
                adjusted_flow_rate = self.config.flow_rate_ml_s * self.config.calibration_factor
                duration_s = volume_ml / adjusted_flow_rate
                
                logger.info(f"Pompe {self.config.id}: Versement {volume_ml}ml ({duration_s:.1f}s)")
                
                # Créer opération
                self.current_operation = PumpOperation(
                    pump_id=self.config.id,
                    target_volume_ml=volume_ml,
                    start_time=time.time(),
                    estimated_duration_s=duration_s
                )
                
                self.status = PumpStatus.PUMPING
                
                # Démarrer pompe
                self.controller.start(speed)
                
                # Attendre durée calculée
                await asyncio.sleep(duration_s)
                
                # Arrêter pompe
                self.controller.stop()
                
                # Finaliser
                self.current_operation.current_volume_ml = volume_ml
                self.status = PumpStatus.IDLE
                
                logger.info(f"Pompe {self.config.id}: Versement terminé")
                return True
                
            except Exception as e:
                logger.error(f"Erreur versement pompe {self.config.id}: {e}")
                self.controller.stop()
                self.status = PumpStatus.ERROR
                return False
            finally:
                self.current_operation = None
    
    async def calibrate(self, expected_ml: float, measured_ml: float) -> bool:
        """Calibre la pompe avec une mesure réelle"""
        try:
            if measured_ml <= 0:
                logger.error("Volume mesuré invalide pour calibration")
                return False
            
            # Calculer nouveau facteur de calibration
            new_factor = expected_ml / measured_ml
            old_factor = self.config.calibration_factor
            
            # Appliquer avec lissage (moyenne pondérée)
            self.config.calibration_factor = (old_factor * 0.7) + (new_factor * 0.3)
            
            logger.info(f"Pompe {self.config.id}: Calibration {old_factor:.3f} -> {self.config.calibration_factor:.3f}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur calibration pompe {self.config.id}: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut de la pompe"""
        return {
            'id': self.config.id,
            'ingredient': self.config.ingredient,
            'status': self.status.value,
            'enabled': self.config.enabled,
            'current_operation': asdict(self.current_operation) if self.current_operation else None,
            'calibration_factor': self.config.calibration_factor
        }
    
    def stop_immediately(self):
        """Arrêt d'urgence"""
        try:
            self.controller.stop()
            self.status = PumpStatus.IDLE
            self.current_operation = None
            logger.warning(f"Pompe {self.config.id}: Arrêt d'urgence")
        except Exception as e:
            logger.error(f"Erreur arrêt urgence pompe {self.config.id}: {e}")
    
    def cleanup(self):
        """Nettoie les ressources"""
        self.controller.cleanup()

class PumpManager:
    """Gestionnaire principal du système de pompes"""
    
    def __init__(self, config_path: str = "config/pumps.json", use_mock: bool = False):
        self.config_path = Path(config_path)
        self.use_mock = use_mock
        self.pumps: Dict[str, Pump] = {}
        self.ingredient_to_pump: Dict[str, str] = {}
        self._lock = asyncio.Lock()
        self.emergency_stop_flag = False
        
        # Charger configuration
        self.load_config()
        
        # Initialiser pompes
        self._initialize_pumps()
    
    def load_config(self):
        """Charge la configuration des pompes"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    self.pump_configs = config_data.get('pumps', DEFAULT_GPIO_CONFIG)
                    logger.info(f"Configuration chargée: {len(self.pump_configs)} pompes")
            else:
                logger.warning("Configuration pompes non trouvée, utilisation par défaut")
                self.pump_configs = DEFAULT_GPIO_CONFIG
                self.save_config()
                
        except Exception as e:
            logger.error(f"Erreur chargement config pompes: {e}")
            self.pump_configs = DEFAULT_GPIO_CONFIG
    
    def save_config(self):
        """Sauvegarde la configuration"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convertir les configs en format JSON
            configs_dict = {}
            for pump_id, pump in self.pumps.items():
                configs_dict[pump_id] = pump.config.to_dict()
            
            config_data = {
                'pumps': configs_dict,
                'last_updated': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
                
            logger.info("Configuration pompes sauvegardée")
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde config: {e}")
    
    def _initialize_pumps(self):
        """Initialise toutes les pompes"""
        try:
            for pump_id, pump_data in self.pump_configs.items():
                try:
                    config = PumpConfig(
                        id=pump_id,
                        pwm_pin=pump_data['pwm_pin'],
                        in1_pin=pump_data['in1_pin'],
                        in2_pin=pump_data['in2_pin'],
                        ingredient=pump_data['ingredient'],
                        flow_rate_ml_s=pump_data.get('flow_rate_ml_s', 2.5)
                    )
                    
                    pump = Pump(config, self.use_mock)
                    self.pumps[pump_id] = pump
                    
                    # Mapper ingrédient -> pompe
                    ingredient_name = config.ingredient.lower()
                    self.ingredient_to_pump[ingredient_name] = pump_id
                    
                    logger.info(f"Pompe {pump_id} initialisée: {config.ingredient}")
                    
                except Exception as e:
                    logger.error(f"Erreur initialisation pompe {pump_id}: {e}")
            
            logger.info(f"Système pompes initialisé: {len(self.pumps)} pompes actives")
            
        except Exception as e:
            logger.error(f"Erreur initialisation système pompes: {e}")
    
    def get_pump_by_ingredient(self, ingredient_name: str) -> Optional[Pump]:
        """Trouve une pompe par nom d'ingrédient"""
        ingredient_key = ingredient_name.lower()
        pump_id = self.ingredient_to_pump.get(ingredient_key)
        
        if pump_id:
            return self.pumps.get(pump_id)
        
        # Recherche partielle si pas de match exact
        for ing_key, p_id in self.ingredient_to_pump.items():
            if ingredient_key in ing_key or ing_key in ingredient_key:
                return self.pumps.get(p_id)
        
        return None
    
    async def pour_ingredient(self, ingredient_name: str, volume_ml: float) -> bool:
        """Verse un ingrédient par son nom"""
        async with self._lock:
            if self.emergency_stop_flag:
                logger.warning("Système en arrêt d'urgence")
                return False
            
            pump = self.get_pump_by_ingredient(ingredient_name)
            if not pump:
                logger.error(f"Aucune pompe trouvée pour: {ingredient_name}")
                return False
            
            return await pump.pour_volume(volume_ml)
    
    def emergency_stop(self):
        """Arrêt d'urgence de toutes les pompes"""
        logger.warning("ARRÊT D'URGENCE SYSTÈME POMPES")
        self.emergency_stop_flag = True
        
        for pump in self.pumps.values():
            pump.stop_immediately()
    
    def reset_emergency(self):
        """Remet le système en service après arrêt d'urgence"""
        logger.info("Remise en service du système pompes")
        self.emergency_stop_flag = False
    
    def get_system_status(self) -> Dict[str, Any]:
        """Retourne le statut complet du système"""
        return {
            'emergency_stop': self.emergency_stop_flag,
            'total_pumps': len(self.pumps),
            'active_pumps': len([p for p in self.pumps.values() if p.status == PumpStatus.PUMPING]),
            'available_ingredients': list(self.ingredient_to_pump.keys()),
            'pumps': [pump.get_status() for pump in self.pumps.values()]
        }
    
    def cleanup(self):
        """Nettoie toutes les ressources"""
        logger.info("Nettoyage système pompes")
        for pump in self.pumps.values():
            pump.cleanup()
        self.pumps.clear()

# Instance globale du gestionnaire
pump_manager: Optional[PumpManager] = None

def initialize_pump_system(use_mock: bool = False) -> PumpManager:
    """Initialise le système de pompes"""
    global pump_manager
    
    try:
        if pump_manager is None:
            pump_manager = PumpManager(use_mock=use_mock)
            logger.info("✅ Système de pompes initialisé")
        return pump_manager
        
    except Exception as e:
        logger.error(f"❌ Erreur initialisation système pompes: {e}")
        raise

def get_pump_manager() -> PumpManager:
    """Récupère l'instance du gestionnaire de pompes"""
    if pump_manager is None:
        raise RuntimeError("Système de pompes non initialisé")
    return pump_manager

@asynccontextmanager
async def pump_operation():
    """Context manager pour opérations de pompe"""
    manager = None
    try:
        manager = get_pump_manager()
        yield manager
    except Exception as e:
        logger.error(f"Erreur opération pompe: {e}")
        if manager:
            manager.emergency_stop()
        raise

# Fonction utilitaire pour Kivy
def create_pump_status_widget():
    """Crée un widget Kivy pour afficher le statut des pompes"""
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.label import Label
    from kivy.uix.progressbar import ProgressBar
    
    class PumpStatusWidget(BoxLayout):
        def __init__(self, **kwargs):
            super().__init__(orientation='vertical', **kwargs)
            self.pump_labels = {}
            self.update_display()
        
        def update_display(self):
            """Met à jour l'affichage du statut"""
            self.clear_widgets()
            
            try:
                manager = get_pump_manager()
                status = manager.get_system_status()
                
                # Titre
                title = Label(
                    text=f"Système Pompes ({'🚨 ARRÊT' if status['emergency_stop'] else '✅ ACTIF'})",
                    size_hint_y=None,
                    height='40dp',
                    color=(1, 0, 0, 1) if status['emergency_stop'] else (0, 1, 0, 1)
                )
                self.add_widget(title)
                
                # Statut par pompe
                for pump_status in status['pumps']:
                    pump_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height='30dp')
                    
                    # Nom ingrédient
                    name_label = Label(
                        text=pump_status['ingredient'][:12],
                        size_hint_x=0.4,
                        halign='left'
                    )
                    
                    # Statut
                    status_color = {
                        'idle': (0.8, 0.8, 0.8, 1),
                        'pumping': (0, 1, 0, 1),
                        'error': (1, 0, 0, 1),
                        'disabled': (0.5, 0.5, 0.5, 1)
                    }.get(pump_status['status'], (1, 1, 1, 1))
                    
                    status_label = Label(
                        text=pump_status['status'].upper(),
                        size_hint_x=0.3,
                        color=status_color
                    )
                    
                    # Calibration
                    cal_label = Label(
                        text=f"{pump_status['calibration_factor']:.2f}",
                        size_hint_x=0.3
                    )
                    
                    pump_layout.add_widget(name_label)
                    pump_layout.add_widget(status_label)
                    pump_layout.add_widget(cal_label)
                    
                    self.add_widget(pump_layout)
                    
            except Exception as e:
                error_label = Label(
                    text=f"Erreur: {str(e)[:50]}",
                    color=(1, 0, 0, 1)
                )
                self.add_widget(error_label)
    
    return PumpStatusWidget()

if __name__ == "__main__":
    # Test du système de pompes
    import asyncio
    
    async def test_pump_system():
        print("🧪 Test du système de pompes...")
        
        # Initialiser avec mock GPIO
        manager = initialize_pump_system(use_mock=True)
        
        # Afficher statut
        status = manager.get_system_status()
        print(f"📊 Pompes disponibles: {len(status['pumps'])}")
        print(f"🧪 Ingrédients: {', '.join(status['available_ingredients'])}")
        
        # Test versement
        print("\n🚰 Test versement Gin 50ml...")
        success = await manager.pour_ingredient("gin", 50.0)
        print(f"Résultat: {'✅' if success else '❌'}")
        
        # Test ingrédient inexistant
        print("\n🚰 Test ingrédient inexistant...")
        success = await manager.pour_ingredient("ingredient_inexistant", 25.0)
        print(f"Résultat: {'✅' if success else '❌'}")
        
        # Test arrêt d'urgence
        print("\n🚨 Test arrêt d'urgence...")
        manager.emergency_stop()
        status = manager.get_system_status()
        print(f"Arrêt d'urgence: {status['emergency_stop']}")
        
        manager.reset_emergency()
        print("🔄 Système remis en service")
        
        # Nettoyage
        manager.cleanup()
        print("✅ Test terminé avec succès!")
    
    # Exécuter tests
    asyncio.run(test_pump_system())