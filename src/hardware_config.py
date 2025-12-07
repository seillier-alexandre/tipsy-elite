# -*- coding: utf-8 -*-
"""
Configuration matérielle pour machine à cocktails
Raspberry Pi + TB6612FNG + Pompes péristaltiques + Écran tactile rond
Architecture optimisée pour performances et fiabilité
"""
import logging
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)

@dataclass
class TB6612FNGConfig:
    """Configuration pour un contrôleur TB6612FNG"""
    # Broches de contrôle pour les deux moteurs du TB6612FNG
    ain1: int  # Direction moteur A
    ain2: int  # Direction moteur A
    bin1: int  # Direction moteur B
    bin2: int  # Direction moteur B
    pwma: int  # PWM moteur A
    pwmb: int  # PWM moteur B
    stby: int  # Standby (commun aux deux moteurs)
    
    def __post_init__(self):
        """Validation des pins GPIO"""
        all_pins = [self.ain1, self.ain2, self.bin1, self.bin2, self.pwma, self.pwmb, self.stby]
        if len(set(all_pins)) != len(all_pins):
            raise ValueError("Pins GPIO dupliquées détectées")
        
        # Vérifier que les pins sont dans la plage valide
        for pin in all_pins:
            if not (0 <= pin <= 27):
                raise ValueError(f"Pin GPIO {pin} hors de la plage valide (0-27)")

@dataclass
class PumpConfig:
    """Configuration d'une pompe péristaltique"""
    pump_id: int
    tb6612_controller: int  # Index du contrôleur TB6612FNG (0-5)
    motor_channel: str      # 'A' ou 'B' sur le contrôleur
    ingredient: str
    flow_rate_ml_per_second: float = 2.5  # Débit nominal en ml/s
    calibration_factor: float = 1.0       # Facteur de calibrage individuel
    max_volume_ml: int = 500             # Volume max du réservoir
    
    @property
    def effective_flow_rate(self) -> float:
        """Débit effectif avec calibrage"""
        return self.flow_rate_ml_per_second * self.calibration_factor

# Configuration des contrôleurs TB6612FNG
# Utilisation optimale des GPIO du Raspberry Pi
TB6612_CONTROLLERS: List[TB6612FNGConfig] = [
    # Contrôleur 1 - Pompes 1 & 2
    TB6612FNGConfig(
        ain1=5, ain2=6, bin1=13, bin2=19,
        pwma=12, pwmb=16, stby=26
    ),
    # Contrôleur 2 - Pompes 3 & 4  
    TB6612FNGConfig(
        ain1=20, ain2=21, bin1=22, bin2=23,
        pwma=24, pwmb=25, stby=7
    ),
    # Contrôleur 3 - Pompes 5 & 6
    TB6612FNGConfig(
        ain1=8, ain2=9, bin1=10, bin2=11,
        pwma=17, pwmb=27, stby=4
    ),
    # Contrôleur 4 - Pompes 7 & 8
    TB6612FNGConfig(
        ain1=2, ain2=3, bin1=14, bin2=15,
        pwma=18, pwmb=25, stby=1
    ),
    # Contrôleur 5 - Pompes 9 & 10
    TB6612FNGConfig(
        ain1=0, ain2=1, bin1=28, bin2=29,
        pwma=30, pwmb=31, stby=32
    ),
    # Contrôleur 6 - Pompes 11 & 12 + Pompe de nettoyage
    TB6612FNGConfig(
        ain1=33, ain2=34, bin1=35, bin2=36,
        pwma=37, pwmb=38, stby=39
    ),
]

# Configuration des pompes
PUMP_CONFIGS: List[PumpConfig] = [
    # Spiritueux de base
    PumpConfig(1, 0, 'A', 'Vodka', 2.8, 1.0, 750),
    PumpConfig(2, 0, 'B', 'Gin', 2.8, 1.0, 750),
    PumpConfig(3, 1, 'A', 'Rhum', 2.8, 1.0, 750),
    PumpConfig(4, 1, 'B', 'Whisky', 2.8, 1.0, 750),
    PumpConfig(5, 2, 'A', 'Tequila', 2.8, 1.0, 750),
    PumpConfig(6, 2, 'B', 'Brandy', 2.8, 1.0, 750),
    
    # Mixers et jus
    PumpConfig(7, 3, 'A', 'Jus d\'orange', 3.2, 1.0, 1000),
    PumpConfig(8, 3, 'B', 'Jus de cranberry', 3.2, 1.0, 1000),
    PumpConfig(9, 4, 'A', 'Sprite', 3.5, 1.0, 1000),
    PumpConfig(10, 4, 'B', 'Coca Cola', 3.5, 1.0, 1000),
    
    # Sirops et liqueurs
    PumpConfig(11, 5, 'A', 'Triple Sec', 2.5, 1.0, 500),
    PumpConfig(12, 5, 'B', 'Grenadine', 2.0, 1.0, 500),
]

# Pompe de nettoyage (utilise le canal libre du contrôleur 6)
CLEANING_PUMP_CONFIG = PumpConfig(99, 5, 'B', 'Solution de nettoyage', 4.0, 1.0, 2000)

# Configuration de l'écran tactile rond
SCREEN_CONFIG = {
    'width': 800,
    'height': 800,
    'center_x': 400,
    'center_y': 400,
    'radius': 395,  # Radius effectif pour l'interface circulaire
    'touch_sensitivity': 0.95,
    'fullscreen': True,
    'rotation': 0,  # Rotation en degrés si nécessaire
}

# Pins des capteurs et accessoires
SENSOR_PINS = {
    'level_sensors': [40, 41, 42, 43, 44, 45],  # Capteurs niveau réservoirs
    'flow_sensor': 46,                           # Capteur débit global
    'emergency_stop': 47,                        # Bouton arrêt d'urgence
    'door_sensor': 48,                          # Capteur ouverture porte
    'status_led_r': 49,                         # LED status rouge
    'status_led_g': 50,                         # LED status verte  
    'status_led_b': 51,                         # LED status bleue
}

# Temporisations et paramètres de fonctionnement
TIMING_CONFIG = {
    'pump_startup_delay': 0.1,      # Délai démarrage pompe (s)
    'pump_shutdown_delay': 0.2,     # Délai arrêt pompe (s)
    'cleaning_cycle_time': 30,      # Durée cycle nettoyage (s)
    'purge_time': 2,                # Temps purge avant service (s)
    'max_pour_time': 60,            # Temps max versement (s)
    'safety_timeout': 120,          # Timeout sécurité général (s)
}

# Paramètres PWM pour contrôle précis des pompes
PWM_CONFIG = {
    'frequency': 1000,              # Fréquence PWM (Hz)
    'min_duty_cycle': 30,           # Duty cycle minimum (%)
    'max_duty_cycle': 100,          # Duty cycle maximum (%)
    'acceleration_time': 0.5,       # Temps d'accélération (s)
    'deceleration_time': 0.3,       # Temps de décélération (s)
}

class HardwareValidator:
    """Validation de la configuration matérielle"""
    
    @staticmethod
    def validate_gpio_configuration() -> bool:
        """Valide que tous les pins GPIO sont correctement configurés"""
        used_pins = set()
        
        # Vérifier les contrôleurs TB6612FNG
        for i, controller in enumerate(TB6612_CONTROLLERS):
            controller_pins = [
                controller.ain1, controller.ain2, controller.bin1, controller.bin2,
                controller.pwma, controller.pwmb, controller.stby
            ]
            
            for pin in controller_pins:
                if pin in used_pins:
                    logger.error(f"Pin GPIO {pin} utilisé plusieurs fois (contrôleur {i})")
                    return False
                used_pins.add(pin)
        
        # Vérifier les capteurs
        for sensor, pin in SENSOR_PINS.items():
            if isinstance(pin, list):
                for p in pin:
                    if p in used_pins:
                        logger.error(f"Pin GPIO {p} utilisé plusieurs fois (capteur {sensor})")
                        return False
                    used_pins.add(p)
            else:
                if pin in used_pins:
                    logger.error(f"Pin GPIO {pin} utilisé plusieurs fois (capteur {sensor})")
                    return False
                used_pins.add(pin)
        
        logger.info(f"Configuration GPIO validée - {len(used_pins)} pins utilisés")
        return True
    
    @staticmethod
    def validate_pump_configuration() -> bool:
        """Valide la configuration des pompes"""
        pump_ids = [pump.pump_id for pump in PUMP_CONFIGS]
        if len(set(pump_ids)) != len(pump_ids):
            logger.error("IDs de pompes dupliqués détectés")
            return False
        
        # Vérifier que chaque contrôleur ne dépasse pas 2 pompes
        controller_usage = {}
        for pump in PUMP_CONFIGS:
            if pump.tb6612_controller not in controller_usage:
                controller_usage[pump.tb6612_controller] = []
            controller_usage[pump.tb6612_controller].append(pump.motor_channel)
        
        for controller, channels in controller_usage.items():
            if len(channels) > 2:
                logger.error(f"Contrôleur {controller} surchargé: {len(channels)} pompes")
                return False
            if len(set(channels)) != len(channels):
                logger.error(f"Contrôleur {controller}: canaux dupliqués {channels}")
                return False
        
        logger.info("Configuration pompes validée")
        return True

def get_pump_by_id(pump_id: int) -> Optional[PumpConfig]:
    """Récupère la configuration d'une pompe par son ID"""
    for pump in PUMP_CONFIGS:
        if pump.pump_id == pump_id:
            return pump
    return None

def get_pump_by_ingredient(ingredient: str) -> Optional[PumpConfig]:
    """Récupère la configuration d'une pompe par ingrédient"""
    for pump in PUMP_CONFIGS:
        if pump.ingredient.lower() == ingredient.lower():
            return pump
    return None

def get_controller_for_pump(pump_id: int) -> Optional[TB6612FNGConfig]:
    """Récupère le contrôleur TB6612FNG pour une pompe donnée"""
    pump = get_pump_by_id(pump_id)
    if pump and 0 <= pump.tb6612_controller < len(TB6612_CONTROLLERS):
        return TB6612_CONTROLLERS[pump.tb6612_controller]
    return None

# Validation automatique au chargement du module
if __name__ == "__main__":
    validator = HardwareValidator()
    if validator.validate_gpio_configuration() and validator.validate_pump_configuration():
        logger.info("✅ Configuration matérielle validée avec succès")
    else:
        logger.error("❌ Erreurs détectées dans la configuration matérielle")