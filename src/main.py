#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Point d'entrée principal pour la machine à cocktails Tipsy Elite
Architecture complète avec interface Art Déco, contrôle hardware et systèmes intelligents
Auto-start compatible avec systemd pour Raspberry Pi
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
    logger.info("Démarrage Tipsy Elite - Machine à Cocktails")
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
        logger.info("[INIT] Initialisation des systèmes...")
        
        # 1. Validation de la configuration hardware
        logger.info("[CONFIG] Validation configuration hardware...")
        validator = HardwareValidator()
        if not validator.validate_gpio_configuration():
            logger.error("[ERROR] Configuration GPIO invalide")
            return False
        
        if not validator.validate_pump_configuration():
            logger.error("[ERROR] Configuration pompes invalide")
            return False
        
        logger.info("[OK] Configuration hardware validée")
        
        # 2. Initialisation du système de pompes
        logger.info("[INIT] Initialisation système de pompes...")
        if not initialize_pump_system():
            logger.error("[ERROR] Échec initialisation pompes")
            return False
        logger.info("[OK] Système de pompes initialisé")
        
        # 3. Initialisation du système de cocktails
        logger.info("[INIT] Initialisation système de cocktails...")
        if not initialize_cocktail_system():
            logger.error("[ERROR] Échec initialisation cocktails")
            return False
        
        self.cocktail_manager = get_cocktail_manager()
        logger.info("[OK] Système de cocktails initialisé")
        
        # 4. Initialisation du système de nettoyage
        logger.info("[INIT] Initialisation système de nettoyage...")
        if not initialize_cleaning_system():
            logger.error("[ERROR] Échec initialisation nettoyage")
            return False
        
        self.cleaning_system = get_cleaning_system()
        logger.info("[OK] Système de nettoyage initialisé")
        
        # 5. Initialisation de l'interface
        logger.info("[INIT] Initialisation interface utilisateur...")
        try:
            self.interface = ArtDecoInterface()
            if not self.interface.initialize():
                logger.error("[ERROR] Échec initialisation interface")
                return False
            logger.info("[OK] Interface utilisateur initialisée")
        except Exception as e:
            logger.error(f"[ERROR] Erreur initialisation interface: {e}")
            return False
        
        logger.info("[READY] Tous les systèmes sont opérationnels")
        return True
    
    def run(self):
        """Lance le système principal"""
        if not self.initialize():
            logger.error("[ERROR] Échec d'initialisation - Arrêt")
            return
        
        try:
            self.running = True
            logger.info("[START] Démarrage de l'interface principale")
            
            # Lancer l'interface dans le thread principal (requis pour Pygame)
            self.interface.run()
            
        except KeyboardInterrupt:
            logger.info("[STOP] Arrêt demandé par l'utilisateur")
        except Exception as e:
            logger.error(f"[ERROR] Erreur fatale: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()
    
    def run_async(self):
        """Lance le système avec interface asynchrone"""
        if not self.initialize():
            logger.error("[ERROR] Échec d'initialisation - Arrêt")
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
            logger.info("[STOP] Arrêt demandé par l'utilisateur")
        except Exception as e:
            logger.error(f"[ERROR] Erreur fatale: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()
    
    async def main_async_loop(self):
        """Boucle principale asynchrone pour tâches background"""
        logger.info("[LOOP] Boucle principale démarrée")
        
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
        
        logger.info("[LOOP] Boucle principale terminée")
    
    async def check_maintenance(self):
        """Vérifie et programme les tâches de maintenance"""
        if not self.cleaning_system:
            return
        
        try:
            maintenance_info = self.cleaning_system.get_maintenance_info()
            
            if maintenance_info['needs_cleaning']:
                mode = maintenance_info['recommended_mode']
                logger.info(f"[MAINTENANCE] Maintenance recommandée: {mode}")
                
                # Ne pas démarrer automatiquement le nettoyage pendant une préparation
                if self.cocktail_manager.maker.preparation_status != "preparing":
                    # Programmer le nettoyage selon le mode
                    if mode == "quick":
                        logger.info("Démarrage nettoyage rapide automatique")
                        await self.cleaning_system.start_cleaning("quick")
        
        except Exception as e:
            logger.error(f"Erreur vérification maintenance: {e}")
    
    def stop(self):
        """Arrête le système"""
        logger.info("[STOP] Arrêt du système demandé")
        self.running = False
        
        if self.interface:
            self.interface.running = False
    
    def cleanup(self):
        """Nettoie toutes les ressources"""
        if self.cleanup_done:
            return
        
        logger.info("[CLEANUP] Nettoyage des ressources...")
        
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
        logger.info("[OK] Nettoyage terminé")

class TipsyDemoMode:
    """Mode démo pour test sans hardware"""
    
    def __init__(self):
        self.interface = None
    
    def run(self):
        """Lance le mode démo"""
        logger.info("[DEMO] Démarrage mode démo (sans hardware)")
        
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

class TipsyMultiProcessSystem:
    """Système multi-process avec Pygame + Streamlit"""
    
    def __init__(self):
        self.web_process = None
        self.pygame_process = None
        self.running = False
    
    def start_web_interface(self):
        """Lance l'interface web Streamlit"""
        import subprocess
        import sys
        
        try:
            logger.info("[WEB] Démarrage interface web Streamlit...")
            
            # Commande pour lancer Streamlit
            cmd = [
                sys.executable, "-m", "streamlit", "run",
                "src/web_interface.py",
                "--server.port", "8501",
                "--server.address", "0.0.0.0",
                "--browser.gatherUsageStats", "false",
                "--server.headless", "true"
            ]
            
            self.web_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=Path.cwd()
            )
            
            logger.info("[WEB] Interface web démarrée sur http://localhost:8501")
            return True
            
        except Exception as e:
            logger.error(f"[WEB] Erreur démarrage interface web: {e}")
            return False
    
    def start_pygame_interface(self):
        """Lance l'interface Pygame dans un processus séparé"""
        import subprocess
        import sys
        
        try:
            logger.info("[PYGAME] Démarrage interface tactile...")
            
            # Script pour l'interface Pygame
            pygame_script = """
import sys
sys.path.insert(0, 'src')

from art_deco_interface import ArtDecoInterface
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    interface = ArtDecoInterface()
    if interface.initialize():
        interface.run()
    else:
        logger.error("Échec initialisation interface")
except Exception as e:
    logger.error(f"Erreur interface Pygame: {e}")
"""
            
            self.pygame_process = subprocess.Popen(
                [sys.executable, "-c", pygame_script],
                cwd=Path.cwd()
            )
            
            logger.info("[PYGAME] Interface tactile démarrée")
            return True
            
        except Exception as e:
            logger.error(f"[PYGAME] Erreur démarrage interface tactile: {e}")
            return False
    
    def run(self):
        """Lance les deux interfaces simultanément"""
        try:
            self.running = True
            logger.info("[MULTI] Démarrage système multi-process")
            
            # Démarrer interface web
            if not self.start_web_interface():
                logger.error("[MULTI] Échec démarrage interface web")
                return False
            
            # Attendre que Streamlit soit prêt
            time.sleep(3)
            
            # Démarrer interface Pygame
            if not self.start_pygame_interface():
                logger.error("[MULTI] Échec démarrage interface tactile")
                self.stop()
                return False
            
            logger.info("[MULTI] Toutes les interfaces sont opérationnelles")
            logger.info("[MULTI] Interface Web: http://localhost:8501")
            logger.info("[MULTI] Interface Tactile: Écran principal")
            
            # Surveiller les processus
            self.monitor_processes()
            
        except KeyboardInterrupt:
            logger.info("[MULTI] Arrêt demandé par utilisateur")
            self.stop()
        except Exception as e:
            logger.error(f"[MULTI] Erreur système: {e}")
            self.stop()
    
    def monitor_processes(self):
        """Surveille l'état des processus"""
        try:
            while self.running:
                # Vérifier processus web
                if self.web_process and self.web_process.poll() is not None:
                    logger.warning("[WEB] Processus web terminé")
                    break
                
                # Vérifier processus Pygame
                if self.pygame_process and self.pygame_process.poll() is not None:
                    logger.warning("[PYGAME] Processus tactile terminé")
                    break
                
                time.sleep(2)
                
        except Exception as e:
            logger.error(f"[MULTI] Erreur surveillance: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Arrête tous les processus"""
        logger.info("[MULTI] Arrêt du système multi-process")
        self.running = False
        
        # Arrêter processus web
        if self.web_process:
            try:
                self.web_process.terminate()
                self.web_process.wait(timeout=5)
                logger.info("[WEB] Interface web arrêtée")
            except subprocess.TimeoutExpired:
                self.web_process.kill()
                logger.warning("[WEB] Interface web forcée à s'arrêter")
        
        # Arrêter processus Pygame
        if self.pygame_process:
            try:
                self.pygame_process.terminate()
                self.pygame_process.wait(timeout=5)
                logger.info("[PYGAME] Interface tactile arrêtée")
            except subprocess.TimeoutExpired:
                self.pygame_process.kill()
                logger.warning("[PYGAME] Interface tactile forcée à s'arrêter")

def main():
    """Point d'entrée principal"""
    import argparse
    
    # Arguments en ligne de commande
    parser = argparse.ArgumentParser(description="Tipsy Elite - Machine à Cocktails")
    parser.add_argument("--demo", action="store_true", 
                       help="Lance en mode démo (sans hardware)")
    parser.add_argument("--async-mode", action="store_true",
                       help="Lance en mode asynchrone")
    parser.add_argument("--multi-process", action="store_true",
                       help="Lance en mode multi-process (Pygame + Web)")
    parser.add_argument("--web-only", action="store_true",
                       help="Lance uniquement l'interface web")
    parser.add_argument("--pygame-only", action="store_true",
                       help="Lance uniquement l'interface tactile")
    parser.add_argument("--debug", action="store_true",
                       help="Active le mode debug")
    
    args = parser.parse_args()
    
    # Configuration debug
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Mode debug activé")
    
    # Configuration des signaux pour arrêt propre
    import signal
    current_system = None
    
    def signal_handler(signum, _frame):
        logger.info(f"Signal {signum} reçu")
        if current_system:
            if hasattr(current_system, 'stop'):
                current_system.stop()
            else:
                current_system.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Démarrage selon le mode
    if args.web_only:
        # Interface web uniquement
        logger.info("Démarrage interface web uniquement")
        import subprocess
        import sys
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "src/web_interface.py", "--server.port", "8501"
        ])
        
    elif args.pygame_only:
        # Interface Pygame uniquement
        logger.info("Démarrage interface tactile uniquement")
        if args.demo:
            demo = TipsyDemoMode()
            current_system = demo
            demo.run()
        else:
            system = TipsySystem()
            current_system = system
            if args.async_mode:
                system.run_async()
            else:
                system.run()
                
    elif args.multi_process:
        # Mode multi-process
        logger.info("Démarrage mode multi-process")
        multi_system = TipsyMultiProcessSystem()
        current_system = multi_system
        multi_system.run()
        
    elif args.demo:
        # Mode démo
        demo = TipsyDemoMode()
        current_system = demo
        demo.run()
    else:
        # Mode standard
        system = TipsySystem()
        current_system = system
        
        # Démarrage
        if args.async_mode:
            system.run_async()
        else:
            system.run()

if __name__ == "__main__":
    main()