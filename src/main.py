# -*- coding: utf-8 -*-
"""
Point d'entrée principal pour la machine à cocktails Tipsy Elite
Architecture complète avec interface Art Déco, contrôle hardware et systèmes intelligents
"""
import logging
import sys
import asyncio
import threading
import time
from pathlib import Path

# Configuration des logs
def setup_logging():
    """Configure le système de logging"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configuration complète
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "tipsy.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Logger principal
    logger = logging.getLogger(__name__)
    logger.info("🍸 Démarrage Tipsy Elite - Machine à Cocktails")
    return logger

# Import des modules après configuration du logging
setup_logging()
logger = logging.getLogger(__name__)

try:
    from hardware_config import HardwareValidator
    from tb6612_controller import initialize_pump_system, cleanup_pump_system
    from cocktail_manager import initialize_cocktail_system, get_cocktail_manager
    from cleaning_system import initialize_cleaning_system, get_cleaning_system
    from art_deco_interface import ArtDecoInterface
except ImportError as e:
    logger.error(f"Erreur d'importation: {e}")
    sys.exit(1)

class TipsySystem:
    """Système principal de la machine à cocktails"""
    
    def __init__(self):
        self.interface: ArtDecoInterface = None
        self.cocktail_manager = None
        self.cleaning_system = None
        self.running = False
        self.cleanup_done = False
        
        # Thread pour l'interface
        self.interface_thread = None
        self.main_loop_thread = None
    
    def initialize(self) -> bool:
        """Initialise tous les systèmes"""
        logger.info("🔧 Initialisation des systèmes...")
        
        # 1. Validation de la configuration hardware
        logger.info("📋 Validation configuration hardware...")
        validator = HardwareValidator()
        if not validator.validate_gpio_configuration():
            logger.error("❌ Configuration GPIO invalide")
            return False
        
        if not validator.validate_pump_configuration():
            logger.error("❌ Configuration pompes invalide")
            return False
        
        logger.info("✅ Configuration hardware validée")
        
        # 2. Initialisation du système de pompes
        logger.info("⚙️ Initialisation système de pompes...")
        if not initialize_pump_system():
            logger.error("❌ Échec initialisation pompes")
            return False
        logger.info("✅ Système de pompes initialisé")
        
        # 3. Initialisation du système de cocktails
        logger.info("🍹 Initialisation système de cocktails...")
        if not initialize_cocktail_system():
            logger.error("❌ Échec initialisation cocktails")
            return False
        
        self.cocktail_manager = get_cocktail_manager()
        logger.info("✅ Système de cocktails initialisé")
        
        # 4. Initialisation du système de nettoyage
        logger.info("🧼 Initialisation système de nettoyage...")
        if not initialize_cleaning_system():
            logger.error("❌ Échec initialisation nettoyage")
            return False
        
        self.cleaning_system = get_cleaning_system()
        logger.info("✅ Système de nettoyage initialisé")
        
        # 5. Initialisation de l'interface
        logger.info("🖥️ Initialisation interface utilisateur...")
        self.interface = ArtDecoInterface()
        if not self.interface.initialize():
            logger.error("❌ Échec initialisation interface")
            return False
        logger.info("✅ Interface utilisateur initialisée")
        
        logger.info("🚀 Tous les systèmes sont opérationnels")
        return True
    
    def run(self):
        """Lance le système principal"""
        if not self.initialize():
            logger.error("❌ Échec d'initialisation - Arrêt")
            return
        
        try:
            self.running = True
            logger.info("🏁 Démarrage de l'interface principale")
            
            # Lancer l'interface dans le thread principal (requis pour Pygame)
            self.interface.run()
            
        except KeyboardInterrupt:
            logger.info("⏹️ Arrêt demandé par l'utilisateur")
        except Exception as e:
            logger.error(f"❌ Erreur fatale: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()
    
    def run_async(self):
        """Lance le système avec interface asynchrone"""
        if not self.initialize():
            logger.error("❌ Échec d'initialisation - Arrêt")
            return
        
        try:
            self.running = True
            
            # Lancer l'interface dans un thread séparé
            self.interface_thread = threading.Thread(
                target=self.interface.run, 
                daemon=True,
                name="InterfaceThread"
            )
            self.interface_thread.start()
            
            # Boucle principale asynchrone
            asyncio.run(self.main_async_loop())
            
        except KeyboardInterrupt:
            logger.info("⏹️ Arrêt demandé par l'utilisateur")
        except Exception as e:
            logger.error(f"❌ Erreur fatale: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()
    
    async def main_async_loop(self):
        """Boucle principale asynchrone pour tâches background"""
        logger.info("🔄 Boucle principale démarrée")
        
        last_maintenance_check = 0
        
        while self.running and self.interface.running:
            try:
                current_time = time.time()
                
                # Vérification maintenance toutes les 5 minutes
                if current_time - last_maintenance_check > 300:
                    await self.check_maintenance()
                    last_maintenance_check = current_time
                
                # Attendre avant la prochaine itération
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Erreur boucle principale: {e}")
                await asyncio.sleep(5)
        
        logger.info("🔄 Boucle principale terminée")
    
    async def check_maintenance(self):
        """Vérifie et programme les tâches de maintenance"""
        if not self.cleaning_system:
            return
        
        try:
            maintenance_info = self.cleaning_system.get_maintenance_info()
            
            if maintenance_info['needs_cleaning']:
                mode = maintenance_info['recommended_mode']
                logger.info(f"🧼 Maintenance recommandée: {mode}")
                
                # Ne pas démarrer automatiquement le nettoyage pendant une préparation
                if not self.cocktail_manager.maker.preparation_status == "preparing":
                    # Programmer le nettoyage selon le mode
                    if mode == "quick":
                        logger.info("Démarrage nettoyage rapide automatique")
                        await self.cleaning_system.start_cleaning("quick")
        
        except Exception as e:
            logger.error(f"Erreur vérification maintenance: {e}")
    
    def stop(self):
        """Arrête le système"""
        logger.info("🛑 Arrêt du système demandé")
        self.running = False
        
        if self.interface:
            self.interface.running = False
    
    def cleanup(self):
        """Nettoie toutes les ressources"""
        if self.cleanup_done:
            return
        
        logger.info("🧹 Nettoyage des ressources...")
        
        self.running = False
        
        # Attendre que l'interface se ferme
        if self.interface_thread and self.interface_thread.is_alive():
            logger.info("Attente fermeture interface...")
            self.interface_thread.join(timeout=3)
        
        # Nettoyer l'interface
        if self.interface:
            try:
                self.interface.cleanup()
            except Exception as e:
                logger.error(f"Erreur nettoyage interface: {e}")
        
        # Nettoyer les systèmes hardware
        try:
            cleanup_pump_system()
        except Exception as e:
            logger.error(f"Erreur nettoyage pompes: {e}")
        
        self.cleanup_done = True
        logger.info("✅ Nettoyage terminé")

class TipsyDemoMode:
    """Mode démo pour test sans hardware"""
    
    def __init__(self):
        self.interface = None
    
    def run(self):
        """Lance le mode démo"""
        logger.info("🎭 Démarrage mode démo (sans hardware)")
        
        try:
            # Interface uniquement
            self.interface = ArtDecoInterface()
            if self.interface.initialize():
                self.interface.run()
        except Exception as e:
            logger.error(f"Erreur mode démo: {e}")
        finally:
            if self.interface:
                self.interface.cleanup()

def main():
    """Point d'entrée principal"""
    import argparse
    
    # Arguments en ligne de commande
    parser = argparse.ArgumentParser(description="Tipsy Elite - Machine à Cocktails")
    parser.add_argument("--demo", action="store_true", 
                       help="Lance en mode démo (sans hardware)")
    parser.add_argument("--async-mode", action="store_true",
                       help="Lance en mode asynchrone")
    parser.add_argument("--debug", action="store_true",
                       help="Active le mode debug")
    
    args = parser.parse_args()
    
    # Configuration debug
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Mode debug activé")
    
    # Démarrage selon le mode
    if args.demo:
        demo = TipsyDemoMode()
        demo.run()
    else:
        system = TipsySystem()
        
        # Configuration des signaux pour arrêt propre
        import signal
        def signal_handler(signum, _frame):
            logger.info(f"Signal {signum} reçu")
            system.stop()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Démarrage
        if args.async_mode:
            system.run_async()
        else:
            system.run()

if __name__ == "__main__":
    main()