#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════
MACHINE À COCKTAILS - APPLICATION PRINCIPALE KIVY
Interface Art Déco années 1920 pour écran tactile rond 4"
Application complète avec gestion hardware et animations
═══════════════════════════════════════════════════════════════
"""

import os
import sys
import logging
from pathlib import Path
import argparse

# Ajouter le répertoire src au path pour importer les modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Configuration Kivy AVANT l'import
os.environ['KIVY_WINDOW'] = 'sdl2'
os.environ['KIVY_GL_BACKEND'] = 'gl'

# Désactiver logs Kivy verbeux en production
os.environ['KIVY_LOG_LEVEL'] = 'warning'

# Import Kivy
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, SlideTransition, FadeTransition
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.config import Config
from kivy.logger import Logger

# Configuration Kivy pour écran tactile
Config.set('input', 'mouse', 'mouse,disable_multitouch')
Config.set('kivy', 'keyboard_mode', 'systemandmulti')
Config.set('graphics', 'multisamples', '0')  # Désactiver anti-aliasing pour performance

# Imports locaux
from screens.menu import MenuScreen
from screens.cocktail import CocktailScreen
from screens.cleaning import CleaningScreen
from screens.settings import SettingsScreen
from screens.screensaver import ScreensaverScreen, activate_screensaver_after_delay
from utils.round_display import ROUND_SCREEN_CONFIG

# Configuration du logging
def setup_logging(level=logging.INFO):
    """Configure le système de logging"""
    log_format = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/cocktail_machine.log', encoding='utf-8')
        ]
    )
    
    # Créer le dossier logs si nécessaire
    Path('logs').mkdir(exist_ok=True)
    
    return logging.getLogger(__name__)

class CocktailMachineApp(App):
    """Application principale de la machine à cocktails"""
    
    def __init__(self, hardware_mode=True, demo_mode=False, **kwargs):
        super().__init__(**kwargs)
        self.hardware_mode = hardware_mode
        self.demo_mode = demo_mode
        self.logger = logging.getLogger(__name__)
        self.screensaver_event = None
        
    def build_config(self, config):
        """Configure l'application"""
        config.setdefaults('graphics', {
            'width': '480',
            'height': '480',
            'borderless': '1' if not self.demo_mode else '0',
            'fullscreen': '1' if not self.demo_mode else '0',
            'resizable': '0',
            'top': '0',
            'left': '0'
        })
        
        config.setdefaults('input', {
            'touch_timeout': '300',
            'inactivity_timeout': '300'
        })
    
    def build(self):
        """Construit l'interface de l'application"""
        self.title = "Cocktail Machine Art Déco"
        self.icon = "assets/images/icon.png"
        
        # Configuration fenêtre pour écran rond
        self._setup_window()
        
        # Initialiser les systèmes
        self._initialize_systems()
        
        # Créer le gestionnaire d'écrans
        self.screen_manager = ScreenManager(
            transition=SlideTransition(duration=0.3)
        )
        
        # Ajouter tous les écrans
        self._create_screens()
        
        # Écran initial
        self.screen_manager.current = 'menu'
        
        # Programmer l'économiseur d'écran
        self._setup_screensaver()
        
        # Gestion des événements globaux
        self._setup_event_handlers()
        
        self.logger.info("🍸 Application Cocktail Machine démarrée")
        return self.screen_manager
    
    def _setup_window(self):
        """Configure la fenêtre selon l'écran rond"""
        config = ROUND_SCREEN_CONFIG
        
        # Taille de fenêtre
        Window.size = config['resolution']
        
        if not self.demo_mode:
            # Mode production sur Raspberry Pi
            Window.fullscreen = True
            Window.borderless = True
            Window.show_cursor = False
        else:
            # Mode développement
            Window.fullscreen = False
            Window.borderless = False
            Window.show_cursor = True
        
        # Couleur de fond
        Window.clearcolor = (0.04, 0.04, 0.04, 1)  # Noir charbon
        
        self.logger.info(f"Fenêtre configurée: {Window.size}")
    
    def _initialize_systems(self):
        """Initialise les sous-systèmes"""
        try:
            # Initialiser le système de cocktails
            from cocktail_manager import initialize_cocktail_system
            if initialize_cocktail_system():
                self.logger.info("✅ Système cocktails initialisé")
            else:
                self.logger.warning("⚠️ Système cocktails en mode dégradé")
            
            # Initialiser le système de pompes si hardware activé
            if self.hardware_mode and not self.demo_mode:
                from hardware.pumps import initialize_pump_system
                try:
                    initialize_pump_system(use_mock=False)
                    self.logger.info("✅ Système pompes hardware initialisé")
                except Exception as e:
                    self.logger.warning(f"⚠️ Hardware pompes indisponible: {e}")
                    # Basculer en mode mock
                    initialize_pump_system(use_mock=True)
                    self.logger.info("✅ Système pompes mock initialisé")
            elif self.demo_mode:
                from hardware.pumps import initialize_pump_system
                initialize_pump_system(use_mock=True)
                self.logger.info("✅ Système pompes démo initialisé")
            
        except ImportError as e:
            self.logger.warning(f"⚠️ Modules hardware non disponibles: {e}")
        except Exception as e:
            self.logger.error(f"❌ Erreur initialisation systèmes: {e}")
    
    def _create_screens(self):
        """Crée et ajoute tous les écrans"""
        try:
            # Menu principal
            menu_screen = MenuScreen()
            self.screen_manager.add_widget(menu_screen)
            
            # Détail cocktail
            cocktail_screen = CocktailScreen()
            self.screen_manager.add_widget(cocktail_screen)
            
            # Nettoyage
            cleaning_screen = CleaningScreen()
            self.screen_manager.add_widget(cleaning_screen)
            
            # Réglages
            settings_screen = SettingsScreen()
            self.screen_manager.add_widget(settings_screen)
            
            # Économiseur d'écran
            screensaver_screen = ScreensaverScreen()
            self.screen_manager.add_widget(screensaver_screen)
            
            self.logger.info("✅ Tous les écrans créés")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur création écrans: {e}")
            raise
    
    def _setup_screensaver(self):
        """Configure l'économiseur d'écran"""
        # Délai d'inactivité (5 minutes par défaut)
        inactivity_timeout = 300
        
        if self.demo_mode:
            inactivity_timeout = 60  # 1 minute en mode démo
        
        def reset_screensaver(*args):
            """Remet le timer de l'économiseur à zéro"""
            if self.screensaver_event:
                self.screensaver_event.cancel()
            
            if self.screen_manager.current != 'screensaver':
                self.screensaver_event = activate_screensaver_after_delay(
                    self.screen_manager, inactivity_timeout
                )
        
        # Touch ou touche remet le timer à zéro
        Window.bind(on_touch_down=reset_screensaver)
        Window.bind(on_key_down=reset_screensaver)
        
        # Démarrer le timer initial
        reset_screensaver()
        
        self.logger.info(f"Économiseur configuré: {inactivity_timeout}s d'inactivité")
    
    def _setup_event_handlers(self):
        """Configure les gestionnaires d'événements globaux"""
        
        # Changement d'écran
        def on_screen_change(instance, screen):
            self.logger.debug(f"Changement écran: {screen.name}")
            
            # Réinitialiser économiseur sauf si on va vers screensaver
            if screen.name != 'screensaver' and self.screensaver_event:
                self.screensaver_event.cancel()
                self.screensaver_event = activate_screensaver_after_delay(
                    self.screen_manager, 300
                )
        
        self.screen_manager.bind(current_screen=on_screen_change)
        
        # Gestion des touches de fonction (pour debug)
        def on_key_down(instance, keycode, *args):
            key = keycode[1] if len(keycode) > 1 else str(keycode[0])
            
            if key == 'escape':
                # Échap pour quitter (développement)
                if self.demo_mode:
                    self.stop()
                return True
            elif key == 'f11':
                # F11 pour basculer plein écran
                Window.fullscreen = not Window.fullscreen
                return True
            elif key == 's' and 'ctrl' in [k for k in args[2]]:
                # Ctrl+S pour forcer économiseur
                self.screen_manager.current = 'screensaver'
                return True
            
            return False
        
        Window.bind(on_key_down=on_key_down)
    
    def on_start(self):
        """Appelé au démarrage de l'application"""
        self.logger.info("🚀 Application démarrée avec succès")
        
        # Animation d'entrée
        self.root.opacity = 0
        from kivy.animation import Animation
        anim = Animation(opacity=1, duration=1.5)
        anim.start(self.root)
        
        # Charger le thème Art Déco
        self._load_art_deco_theme()
    
    def _load_art_deco_theme(self):
        """Charge le thème Art Déco"""
        try:
            from kivy.lang import Builder
            theme_path = Path(__file__).parent / 'theme' / 'deco.kv'
            
            if theme_path.exists():
                Builder.load_file(str(theme_path))
                self.logger.info("✅ Thème Art Déco chargé")
            else:
                self.logger.warning("⚠️ Fichier thème Art Déco non trouvé")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur chargement thème: {e}")
    
    def on_stop(self):
        """Appelé à l'arrêt de l'application"""
        self.logger.info("🛑 Arrêt de l'application")
        
        try:
            # Arrêter économiseur si actif
            if self.screensaver_event:
                self.screensaver_event.cancel()
            
            # Nettoyer les systèmes hardware
            if self.hardware_mode:
                try:
                    from hardware.pumps import get_pump_manager
                    manager = get_pump_manager()
                    manager.cleanup()
                    self.logger.info("✅ Système pompes nettoyé")
                except:
                    pass
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'arrêt: {e}")
    
    def on_pause(self):
        """Appelé quand l'app est mise en pause"""
        self.logger.info("⏸️ Application mise en pause")
        return True
    
    def on_resume(self):
        """Appelé quand l'app reprend"""
        self.logger.info("▶️ Application reprise")

def main():
    """Point d'entrée principal"""
    # Parse des arguments
    parser = argparse.ArgumentParser(description='Machine à Cocktails Art Déco')
    parser.add_argument('--demo', action='store_true', 
                       help='Mode démonstration (fenêtré, sans hardware)')
    parser.add_argument('--no-hardware', action='store_true',
                       help='Désactiver le hardware (pompes, GPIO)')
    parser.add_argument('--debug', action='store_true',
                       help='Mode debug avec logs verbeux')
    parser.add_argument('--resolution', type=str, default='480x480',
                       help='Résolution de la fenêtre (ex: 800x600)')
    
    args = parser.parse_args()
    
    # Configuration du logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logger = setup_logging(log_level)
    
    logger.info("═══════════════════════════════════════")
    logger.info("🍸 COCKTAIL MACHINE ART DÉCO 1925 🍸")
    logger.info("═══════════════════════════════════════")
    
    # Configuration selon les arguments
    if args.demo:
        logger.info("🎭 Mode DÉMONSTRATION activé")
        demo_mode = True
        hardware_mode = False
    else:
        demo_mode = False
        hardware_mode = not args.no_hardware
    
    if args.resolution != '480x480':
        try:
            w, h = map(int, args.resolution.split('x'))
            ROUND_SCREEN_CONFIG['resolution'] = (w, h)
            logger.info(f"Résolution personnalisée: {w}x{h}")
        except:
            logger.warning("Format résolution invalide, utilisation par défaut")
    
    # Vérifications préalables
    if not demo_mode:
        logger.info("🔍 Vérification environnement production...")
        
        # Vérifier si on est sur Raspberry Pi
        try:
            with open('/proc/cpuinfo', 'r') as f:
                if 'Raspberry Pi' in f.read():
                    logger.info("✅ Raspberry Pi détecté")
                else:
                    logger.warning("⚠️ Pas sur Raspberry Pi - basculer en démo")
                    demo_mode = True
        except:
            logger.warning("⚠️ Impossible de détecter le hardware - basculer en démo")
            demo_mode = True
    
    # Créer et démarrer l'application
    try:
        app = CocktailMachineApp(
            hardware_mode=hardware_mode,
            demo_mode=demo_mode
        )
        
        logger.info(f"Hardware: {'✅' if hardware_mode else '❌'}")
        logger.info(f"Mode démo: {'✅' if demo_mode else '❌'}")
        logger.info("🚀 Démarrage de l'interface...")
        
        app.run()
        
    except KeyboardInterrupt:
        logger.info("👋 Arrêt demandé par utilisateur")
    except Exception as e:
        logger.error(f"💥 Erreur fatale: {e}")
        raise
    finally:
        logger.info("🏁 Application terminée")

if __name__ == '__main__':
    main()