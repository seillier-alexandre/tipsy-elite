# -*- coding: utf-8 -*-
"""
Tests pour la configuration et contrôleurs hardware
Tests unitaires et d'intégration pour TB6612FNG et pompes
"""
import pytest
import unittest.mock as mock
import time
from src.hardware_config import HardwareValidator, get_pump_by_id, TB6612_CONTROLLERS
from src.tb6612_controller import PumpManager, TB6612Controller

class TestHardwareConfiguration:
    """Tests de validation de la configuration hardware"""
    
    def test_gpio_validation(self):
        """Test validation configuration GPIO"""
        validator = HardwareValidator()
        assert validator.validate_gpio_configuration() is True
    
    def test_pump_configuration(self):
        """Test validation configuration pompes"""
        validator = HardwareValidator()
        assert validator.validate_pump_configuration() is True
    
    def test_pump_retrieval(self):
        """Test récupération pompes par ID"""
        pump = get_pump_by_id(1)
        assert pump is not None
        assert pump.pump_id == 1
        
        # Test pompe inexistante
        pump = get_pump_by_id(999)
        assert pump is None
    
    def test_controller_count(self):
        """Test nombre de contrôleurs configurés"""
        assert len(TB6612_CONTROLLERS) == 6

@pytest.mark.hardware
class TestTB6612Controller:
    """Tests du contrôleur TB6612FNG (nécessite hardware)"""
    
    def setup_method(self):
        """Configuration avant chaque test"""
        self.pump_manager = PumpManager()
    
    def teardown_method(self):
        """Nettoyage après chaque test"""
        if hasattr(self.pump_manager, 'cleanup'):
            self.pump_manager.cleanup()
    
    def test_pump_manager_init(self):
        """Test initialisation du gestionnaire de pompes"""
        assert self.pump_manager is not None
        assert len(self.pump_manager.controllers) == 6
        assert len(self.pump_manager.pumps) > 0
    
    @pytest.mark.skipif(True, reason="Nécessite hardware réel")
    def test_pump_initialization(self):
        """Test initialisation des pompes"""
        success = self.pump_manager.initialize()
        assert success is True
        assert self.pump_manager.is_initialized is True
    
    @pytest.mark.skipif(True, reason="Nécessite hardware réel")
    def test_pump_start_stop(self):
        """Test démarrage/arrêt d'une pompe"""
        self.pump_manager.initialize()
        
        # Test démarrage
        success = self.pump_manager.start_pump(1, 50)
        assert success is True
        
        # Vérifier l'état
        status = self.pump_manager.get_pump_status(1)
        assert status is not None
        assert status.is_running is True
        
        # Test arrêt
        success = self.pump_manager.stop_pump(1)
        assert success is True
        
        # Vérifier l'arrêt
        status = self.pump_manager.get_pump_status(1)
        assert status.is_running is False

class TestPumpManagerMocked:
    """Tests avec GPIO mockés"""
    
    def setup_method(self):
        """Configuration avec mocks"""
        self.gpio_patcher = mock.patch('src.tb6612_controller.GPIO')
        self.mock_gpio = self.gpio_patcher.start()
        
        # Configuration du mock
        self.mock_gpio.BCM = "BCM"
        self.mock_gpio.OUT = "OUT"
        self.mock_gpio.LOW = 0
        self.mock_gpio.HIGH = 1
        
        # Mock PWM
        self.mock_pwm = mock.MagicMock()
        self.mock_gpio.PWM.return_value = self.mock_pwm
        
        self.pump_manager = PumpManager()
    
    def teardown_method(self):
        """Nettoyage des mocks"""
        self.gpio_patcher.stop()
    
    def test_initialization_mocked(self):
        """Test initialisation avec GPIO mocké"""
        success = self.pump_manager.initialize()
        assert success is True
        
        # Vérifier que GPIO.setmode a été appelé
        self.mock_gpio.setmode.assert_called_once()
    
    def test_pump_start_mocked(self):
        """Test démarrage pompe avec GPIO mocké"""
        self.pump_manager.initialize()
        
        success = self.pump_manager.start_pump(1, 75)
        assert success is True
        
        # Vérifier les appels GPIO
        assert self.mock_gpio.output.called
        assert self.mock_pwm.start.called
        assert self.mock_pwm.ChangeDutyCycle.called
    
    def test_emergency_stop_mocked(self):
        """Test arrêt d'urgence avec GPIO mocké"""
        self.pump_manager.initialize()
        self.pump_manager.start_pump(1, 50)
        
        # Arrêt d'urgence
        self.pump_manager.emergency_stop()
        
        # Vérifier que toutes les pompes sont arrêtées
        all_status = self.pump_manager.get_all_pump_status()
        for status in all_status.values():
            assert status.is_running is False
    
    def test_pour_volume_calculation(self):
        """Test calcul du temps de versement"""
        self.pump_manager.initialize()
        
        # Mock du temps
        with mock.patch('time.sleep') as mock_sleep:
            success = self.pump_manager.pour_volume(1, 30.0, 100)
            assert success is True
            
            # Vérifier que sleep a été appelé avec le bon timing
            # 30ml avec un débit de ~2.8ml/s = ~10.7s
            mock_sleep.assert_called()
            sleep_time = mock_sleep.call_args[0][0]
            assert 8 < sleep_time < 15  # Marge pour le calibrage

class TestControllerIndividual:
    """Tests d'un contrôleur TB6612FNG individuel"""
    
    def setup_method(self):
        """Configuration pour tests individuels"""
        with mock.patch('src.tb6612_controller.GPIO'):
            self.controller = TB6612Controller(TB6612_CONTROLLERS[0], 0)
    
    def test_controller_creation(self):
        """Test création d'un contrôleur"""
        assert self.controller.controller_id == 0
        assert self.controller.is_initialized is False
        assert self.controller.standby_active is True
    
    @mock.patch('src.tb6612_controller.GPIO')
    def test_controller_initialization(self, mock_gpio):
        """Test initialisation d'un contrôleur"""
        # Configuration du mock PWM
        mock_pwm = mock.MagicMock()
        mock_gpio.PWM.return_value = mock_pwm
        
        success = self.controller.initialize()
        assert success is True
        assert self.controller.is_initialized is True
        assert self.controller.standby_active is False
        
        # Vérifier les appels GPIO
        assert mock_gpio.setup.called
        assert mock_pwm.start.called
    
    @mock.patch('src.tb6612_controller.GPIO')
    def test_motor_control(self, mock_gpio):
        """Test contrôle des moteurs"""
        # Setup PWM mock
        mock_pwm = mock.MagicMock()
        mock_gpio.PWM.return_value = mock_pwm
        
        self.controller.initialize()
        
        # Test moteur A forward
        success = self.controller.set_motor_speed('A', 75, 'forward')
        assert success is True
        
        # Vérifier l'état du moteur A
        status = self.controller.get_motor_status('A')
        assert status.is_running is True
        assert status.direction == 'forward'
        assert status.speed_percent == 75
        
        # Test moteur A reverse
        success = self.controller.set_motor_speed('A', 50, 'reverse')
        assert success is True
        
        status = self.controller.get_motor_status('A')
        assert status.direction == 'reverse'
        assert status.speed_percent == 50
        
        # Test arrêt moteur A
        success = self.controller.stop_motor('A')
        assert success is True
        
        status = self.controller.get_motor_status('A')
        assert status.is_running is False
        assert status.direction == 'stopped'

@pytest.mark.integration
class TestPumpSystemIntegration:
    """Tests d'intégration du système complet"""
    
    def setup_method(self):
        """Configuration tests d'intégration"""
        self.pump_manager = PumpManager()
    
    def teardown_method(self):
        """Nettoyage"""
        if hasattr(self.pump_manager, 'cleanup'):
            self.pump_manager.cleanup()
    
    @mock.patch('src.tb6612_controller.GPIO')
    def test_multiple_pump_coordination(self, mock_gpio):
        """Test coordination de plusieurs pompes"""
        # Setup
        mock_pwm = mock.MagicMock()
        mock_gpio.PWM.return_value = mock_pwm
        
        self.pump_manager.initialize()
        
        # Démarrer plusieurs pompes simultanément
        pumps_to_test = [1, 2, 3]
        
        for pump_id in pumps_to_test:
            success = self.pump_manager.start_pump(pump_id, 60)
            assert success is True
        
        # Vérifier que toutes tournent
        for pump_id in pumps_to_test:
            status = self.pump_manager.get_pump_status(pump_id)
            assert status.is_running is True
        
        # Arrêter toutes
        for pump_id in pumps_to_test:
            success = self.pump_manager.stop_pump(pump_id)
            assert success is True
        
        # Vérifier l'arrêt
        for pump_id in pumps_to_test:
            status = self.pump_manager.get_pump_status(pump_id)
            assert status.is_running is False
    
    @mock.patch('src.tb6612_controller.GPIO')
    @mock.patch('time.sleep')
    def test_cocktail_simulation(self, mock_sleep, mock_gpio):
        """Test simulation préparation cocktail"""
        # Setup
        mock_pwm = mock.MagicMock()
        mock_gpio.PWM.return_value = mock_pwm
        
        self.pump_manager.initialize()
        
        # Simulation Old Fashioned: Whisky (60ml) + Sirop (5ml)
        cocktail_recipe = [
            (4, 60.0),  # Whisky sur pompe 4
            (11, 5.0),  # Sirop sur pompe 11
        ]
        
        total_time_expected = 0
        
        for pump_id, volume in cocktail_recipe:
            pump = self.pump_manager.pumps.get(pump_id)
            if pump:
                expected_time = volume / pump.effective_flow_rate
                total_time_expected += expected_time
                
                success = self.pump_manager.pour_volume(pump_id, volume, 80)
                assert success is True
        
        # Vérifier que le temps total de sleep correspond approximativement
        total_sleep_time = sum(call[0][0] for call in mock_sleep.call_args_list)
        assert abs(total_sleep_time - total_time_expected) < 2  # Marge de 2 secondes

if __name__ == "__main__":
    # Lancer les tests
    pytest.main([__file__, "-v"])