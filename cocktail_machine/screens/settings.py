#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════
ÉCRAN RÉGLAGES - INTERFACE ART DÉCO KIVY
Configuration du système, calibration des pompes, paramètres
Design sophistiqué années 1920 pour écran rond 4"
═══════════════════════════════════════════════════════════════
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.textinput import TextInput
from kivy.uix.switch import Switch
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.accordion import Accordion, AccordionItem
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import dp
import json
from pathlib import Path

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from hardware.pumps import get_pump_manager
    PUMP_SUPPORT = True
except ImportError:
    PUMP_SUPPORT = False
    print("⚠️ Système pompes non disponible en mode démo")

from ..utils.round_display import RoundScreen, DecoTransition

class SettingItem(BoxLayout):
    """Item de réglage avec style Art Déco"""
    
    def __init__(self, title, description, control_widget, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.size_hint_y = None
        self.height = dp(80)
        
        # En-tête avec titre et description
        header_layout = BoxLayout(orientation='horizontal', size_hint_y=0.6)
        
        info_layout = BoxLayout(orientation='vertical', size_hint_x=0.7)
        
        title_label = Label(
            text=title,
            color=(0.83, 0.69, 0.22, 1),  # Doré
            font_size='14sp',
            bold=True,
            halign='left',
            size_hint_y=0.6,
            text_size=(dp(150), None)
        )
        
        desc_label = Label(
            text=description,
            color=(0.97, 0.96, 0.91, 0.7),  # Crème pâle
            font_size='10sp',
            halign='left',
            size_hint_y=0.4,
            text_size=(dp(150), None)
        )
        
        info_layout.add_widget(title_label)
        info_layout.add_widget(desc_label)
        
        # Widget de contrôle
        control_container = BoxLayout(size_hint_x=0.3)
        control_container.add_widget(control_widget)
        
        header_layout.add_widget(info_layout)
        header_layout.add_widget(control_container)
        
        self.add_widget(header_layout)
        
        # Ligne de séparation
        separator = Label(size_hint_y=0.4)
        self.add_widget(separator)
        
        # Style
        self._setup_deco_style()
    
    def _setup_deco_style(self):
        """Style Art Déco"""
        with self.canvas.before:
            from kivy.graphics import Color, Line
            
            # Ligne décorative
            Color(0.83, 0.69, 0.22, 0.3)
            self.deco_line = Line(
                points=[self.x + 20, self.y + 10, self.right - 20, self.y + 10],
                width=1
            )
        
        self.bind(pos=self._update_line)
    
    def _update_line(self, *args):
        if hasattr(self, 'deco_line'):
            self.deco_line.points = [self.x + 20, self.y + 10, self.right - 20, self.y + 10]

class PumpCalibrationItem(BoxLayout):
    """Item de calibration de pompe"""
    
    def __init__(self, pump_data, callback=None, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.pump_data = pump_data
        self.callback = callback
        self.size_hint_y = None
        self.height = dp(120)
        
        # Titre pompe
        title_label = Label(
            text=f"Pompe: {pump_data.get('ingredient', 'N/A')}",
            color=(0.83, 0.69, 0.22, 1),
            font_size='14sp',
            bold=True,
            size_hint_y=0.2,
            halign='left'
        )
        
        # Facteur de calibration actuel
        cal_layout = BoxLayout(orientation='horizontal', size_hint_y=0.3)
        
        cal_layout.add_widget(Label(
            text=f"Facteur:",
            size_hint_x=0.4,
            color=(0.97, 0.96, 0.91, 0.8)
        ))
        
        self.cal_label = Label(
            text=f"{pump_data.get('calibration_factor', 1.0):.3f}",
            size_hint_x=0.6,
            color=(0.83, 0.69, 0.22, 1),
            bold=True
        )
        cal_layout.add_widget(self.cal_label)
        
        # Contrôles de calibration
        controls_layout = BoxLayout(orientation='horizontal', size_hint_y=0.3)
        
        self.volume_input = TextInput(
            text='50',
            size_hint_x=0.3,
            multiline=False,
            input_filter='float'
        )
        
        cal_btn = Button(
            text='Calibrer',
            size_hint_x=0.4
        )
        cal_btn.bind(on_press=self._calibrate)
        
        test_btn = Button(
            text='Test 10ml',
            size_hint_x=0.3
        )
        test_btn.bind(on_press=self._test_pump)
        
        controls_layout.add_widget(Label(text='Volume (ml):', size_hint_x=0.3))
        controls_layout.add_widget(self.volume_input)
        controls_layout.add_widget(cal_btn)
        controls_layout.add_widget(test_btn)
        
        # Statut
        self.status_label = Label(
            text=pump_data.get('status', 'idle').upper(),
            size_hint_y=0.2,
            color=(0, 1, 0, 1) if pump_data.get('enabled') else (0.5, 0.5, 0.5, 1),
            font_size='10sp'
        )
        
        self.add_widget(title_label)
        self.add_widget(cal_layout)
        self.add_widget(controls_layout)
        self.add_widget(self.status_label)
        
        # Style
        self._setup_deco_style()
    
    def _setup_deco_style(self):
        """Style Art Déco"""
        with self.canvas.before:
            from kivy.graphics import Color, RoundedRectangle, Line
            
            # Fond
            Color(0.04, 0.04, 0.04, 0.5)
            self.bg_rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[8]
            )
            
            # Bordure
            Color(0.83, 0.69, 0.22, 0.8)
            self.border_line = Line(
                rounded_rectangle=(self.x, self.y, self.width, self.height, 8),
                width=1
            )
        
        self.bind(pos=self._update_graphics, size=self._update_graphics)
    
    def _update_graphics(self, *args):
        if hasattr(self, 'bg_rect'):
            self.bg_rect.pos = self.pos
            self.bg_rect.size = self.size
        if hasattr(self, 'border_line'):
            self.border_line.rounded_rectangle = (self.x, self.y, self.width, self.height, 8)
    
    def _calibrate(self, instance):
        """Lance la calibration"""
        try:
            volume = float(self.volume_input.text)
            if volume <= 0 or volume > 500:
                raise ValueError("Volume invalide")
            
            if self.callback:
                self.callback('calibrate', self.pump_data, {'volume': volume})
            
        except ValueError:
            self._show_error("Volume invalide (1-500ml)")
    
    def _test_pump(self, instance):
        """Test de la pompe"""
        if self.callback:
            self.callback('test', self.pump_data, {'volume': 10.0})
    
    def _show_error(self, message):
        """Affiche une erreur temporaire"""
        original_text = self.status_label.text
        original_color = self.status_label.color
        
        self.status_label.text = message
        self.status_label.color = (1, 0, 0, 1)
        
        def restore(*args):
            self.status_label.text = original_text
            self.status_label.color = original_color
        
        Clock.schedule_once(restore, 2.0)
    
    def update_calibration(self, new_factor):
        """Met à jour le facteur de calibration affiché"""
        self.cal_label.text = f"{new_factor:.3f}"
        
        # Animation pour montrer le changement
        anim = Animation(color=(0, 1, 0, 1), duration=0.5) + Animation(color=(0.83, 0.69, 0.22, 1), duration=0.5)
        anim.start(self.cal_label)

class SettingsScreen(RoundScreen):
    """Écran de réglages du système"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'settings'
        self.settings_data = self._load_settings()
        
        self._build_interface()
    
    def _load_settings(self):
        """Charge les réglages depuis le fichier"""
        default_settings = {
            'system': {
                'auto_clean': True,
                'screen_brightness': 80,
                'sound_enabled': True,
                'demo_mode': False
            },
            'cocktails': {
                'double_dose_multiplier': 2.0,
                'preparation_timeout': 300,
                'auto_garnish_reminder': True
            },
            'hardware': {
                'pump_default_speed': 80,
                'calibration_volume': 50,
                'emergency_timeout': 10
            }
        }
        
        try:
            settings_path = Path('config/settings.json')
            if settings_path.exists():
                with open(settings_path, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    # Merger avec les défauts
                    for category, values in default_settings.items():
                        if category not in loaded_settings:
                            loaded_settings[category] = values
                        else:
                            for key, default_value in values.items():
                                if key not in loaded_settings[category]:
                                    loaded_settings[category][key] = default_value
                    return loaded_settings
        except Exception as e:
            print(f"Erreur chargement réglages: {e}")
        
        return default_settings
    
    def _save_settings(self):
        """Sauvegarde les réglages"""
        try:
            settings_path = Path('config/settings.json')
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings_data, f, ensure_ascii=False, indent=2)
            
            print("✅ Réglages sauvegardés")
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde réglages: {e}")
    
    def _build_interface(self):
        """Construit l'interface de réglages"""
        main_layout = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(15))
        
        # Titre
        title_label = Label(
            text='⚙️ RÉGLAGES',
            size_hint_y=0.1,
            color=(0.83, 0.69, 0.22, 1),
            font_size='18sp',
            bold=True,
            halign='center'
        )
        
        # Accordion pour catégories
        self.accordion = Accordion(orientation='vertical', size_hint_y=0.75)
        
        # Catégories de réglages
        self._build_system_settings()
        self._build_cocktail_settings()
        self._build_hardware_settings()
        
        # Boutons de navigation
        nav_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=0.15,
            spacing=dp(15)
        )
        
        # Bouton Retour
        back_btn = Button(
            text='⬅️ RETOUR',
            size_hint_x=0.3
        )
        back_btn.bind(on_press=self._go_back)
        
        # Bouton Sauvegarder
        save_btn = Button(
            text='💾 SAUVEGARDER',
            size_hint_x=0.4
        )
        save_btn.bind(on_press=lambda x: self._save_settings())
        
        # Bouton Reset
        reset_btn = Button(
            text='🔄 RESET',
            size_hint_x=0.3,
            background_color=(1, 0.5, 0.5, 1)
        )
        reset_btn.bind(on_press=self._show_reset_confirmation)
        
        nav_layout.add_widget(back_btn)
        nav_layout.add_widget(save_btn)
        nav_layout.add_widget(reset_btn)
        
        # Assembler
        main_layout.add_widget(title_label)
        main_layout.add_widget(self.accordion)
        main_layout.add_widget(nav_layout)
        
        self.add_widget(main_layout)
        
        # Animation d'entrée
        DecoTransition.fade_in_gold(main_layout, 0.8)
    
    def _build_system_settings(self):
        """Construit les réglages système"""
        content = BoxLayout(orientation='vertical', spacing=dp(5))
        
        # Nettoyage automatique
        auto_clean_switch = Switch()
        auto_clean_switch.active = self.settings_data['system']['auto_clean']
        auto_clean_switch.bind(active=lambda x, v: self._update_setting('system', 'auto_clean', v))
        
        content.add_widget(SettingItem(
            'Nettoyage automatique',
            'Nettoyage des pompes après chaque cocktail',
            auto_clean_switch
        ))
        
        # Luminosité écran
        brightness_slider = Slider(
            min=20, max=100, value=self.settings_data['system']['screen_brightness'],
            step=10
        )
        brightness_slider.bind(value=lambda x, v: self._update_setting('system', 'screen_brightness', int(v)))
        
        content.add_widget(SettingItem(
            'Luminosité écran',
            'Réglage de la luminosité (20-100%)',
            brightness_slider
        ))
        
        # Son activé
        sound_switch = Switch()
        sound_switch.active = self.settings_data['system']['sound_enabled']
        sound_switch.bind(active=lambda x, v: self._update_setting('system', 'sound_enabled', v))
        
        content.add_widget(SettingItem(
            'Sons système',
            'Activer les sons et notifications',
            sound_switch
        ))
        
        # Mode démo
        demo_switch = Switch()
        demo_switch.active = self.settings_data['system']['demo_mode']
        demo_switch.bind(active=lambda x, v: self._update_setting('system', 'demo_mode', v))
        
        content.add_widget(SettingItem(
            'Mode démonstration',
            'Simulation sans hardware réel',
            demo_switch
        ))
        
        # Créer l'item accordion
        system_item = AccordionItem(title='🔧 Système')
        system_item.add_widget(content)
        self.accordion.add_widget(system_item)
    
    def _build_cocktail_settings(self):
        """Construit les réglages cocktails"""
        content = BoxLayout(orientation='vertical', spacing=dp(5))
        
        # Multiplicateur double dose
        double_dose_slider = Slider(
            min=1.5, max=3.0, value=self.settings_data['cocktails']['double_dose_multiplier'],
            step=0.1
        )
        double_dose_slider.bind(value=lambda x, v: self._update_setting('cocktails', 'double_dose_multiplier', round(v, 1)))
        
        content.add_widget(SettingItem(
            'Multiplicateur double dose',
            'Facteur pour les doubles doses (1.5-3.0x)',
            double_dose_slider
        ))
        
        # Timeout préparation
        timeout_slider = Slider(
            min=60, max=600, value=self.settings_data['cocktails']['preparation_timeout'],
            step=30
        )
        timeout_slider.bind(value=lambda x, v: self._update_setting('cocktails', 'preparation_timeout', int(v)))
        
        content.add_widget(SettingItem(
            'Timeout préparation',
            'Temps limite pour préparer (60-600s)',
            timeout_slider
        ))
        
        # Rappel garnitures
        garnish_switch = Switch()
        garnish_switch.active = self.settings_data['cocktails']['auto_garnish_reminder']
        garnish_switch.bind(active=lambda x, v: self._update_setting('cocktails', 'auto_garnish_reminder', v))
        
        content.add_widget(SettingItem(
            'Rappel garnitures',
            'Rappel automatique pour les garnitures',
            garnish_switch
        ))
        
        cocktails_item = AccordionItem(title='🍸 Cocktails')
        cocktails_item.add_widget(content)
        self.accordion.add_widget(cocktails_item)
    
    def _build_hardware_settings(self):
        """Construit les réglages hardware"""
        content = ScrollView()
        content_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(10))
        content_layout.bind(minimum_height=content_layout.setter('height'))
        
        # Réglages généraux hardware
        general_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(160))
        
        # Vitesse par défaut des pompes
        pump_speed_slider = Slider(
            min=40, max=100, value=self.settings_data['hardware']['pump_default_speed'],
            step=10
        )
        pump_speed_slider.bind(value=lambda x, v: self._update_setting('hardware', 'pump_default_speed', int(v)))
        
        general_layout.add_widget(SettingItem(
            'Vitesse pompes',
            'Vitesse par défaut des pompes (40-100%)',
            pump_speed_slider
        ))
        
        # Timeout d'urgence
        emergency_slider = Slider(
            min=5, max=30, value=self.settings_data['hardware']['emergency_timeout'],
            step=5
        )
        emergency_slider.bind(value=lambda x, v: self._update_setting('hardware', 'emergency_timeout', int(v)))
        
        general_layout.add_widget(SettingItem(
            'Timeout d\'urgence',
            'Délai d\'arrêt d\'urgence (5-30s)',
            emergency_slider
        ))
        
        content_layout.add_widget(general_layout)
        
        # Calibration des pompes
        pumps_title = Label(
            text='CALIBRATION DES POMPES',
            color=(0.83, 0.69, 0.22, 1),
            font_size='14sp',
            bold=True,
            size_hint_y=None,
            height=dp(40),
            halign='center'
        )
        content_layout.add_widget(pumps_title)
        
        # Charger les pompes
        self._build_pump_calibration(content_layout)
        
        content.add_widget(content_layout)
        
        hardware_item = AccordionItem(title='⚡ Hardware')
        hardware_item.add_widget(content)
        self.accordion.add_widget(hardware_item)
    
    def _build_pump_calibration(self, parent_layout):
        """Construit la section de calibration des pompes"""
        if PUMP_SUPPORT:
            try:
                manager = get_pump_manager()
                status = manager.get_system_status()
                
                for pump_status in status.get('pumps', []):
                    if pump_status.get('enabled', False):
                        pump_cal = PumpCalibrationItem(
                            pump_status,
                            callback=self._on_pump_action
                        )
                        parent_layout.add_widget(pump_cal)
                
            except Exception as e:
                error_label = Label(
                    text=f"Erreur chargement pompes: {str(e)[:50]}",
                    color=(1, 0, 0, 1),
                    size_hint_y=None,
                    height=dp(40)
                )
                parent_layout.add_widget(error_label)
        else:
            # Mode démo
            demo_pumps = [
                {'id': 'pump_1', 'ingredient': 'Gin', 'calibration_factor': 1.0, 'enabled': True, 'status': 'idle'},
                {'id': 'pump_2', 'ingredient': 'Vodka', 'calibration_factor': 0.95, 'enabled': True, 'status': 'idle'},
                {'id': 'pump_7', 'ingredient': 'Sprite', 'calibration_factor': 1.1, 'enabled': True, 'status': 'idle'}
            ]
            
            for pump_data in demo_pumps:
                pump_cal = PumpCalibrationItem(
                    pump_data,
                    callback=self._on_pump_action
                )
                parent_layout.add_widget(pump_cal)
    
    def _on_pump_action(self, action, pump_data, params):
        """Callback pour actions sur les pompes"""
        pump_id = pump_data.get('id')
        
        if action == 'calibrate':
            volume = params['volume']
            print(f"🔧 Calibration pompe {pump_id}: {volume}ml")
            self._calibrate_pump(pump_data, volume)
            
        elif action == 'test':
            volume = params['volume']
            print(f"🧪 Test pompe {pump_id}: {volume}ml")
            self._test_pump(pump_data, volume)
    
    def _calibrate_pump(self, pump_data, volume):
        """Lance la calibration d'une pompe"""
        if PUMP_SUPPORT:
            try:
                # En mode réel, on ferait un versement et demanderait la mesure
                self._show_calibration_dialog(pump_data, volume)
            except Exception as e:
                print(f"Erreur calibration: {e}")
        else:
            # Mode démo
            self._show_calibration_dialog(pump_data, volume)
    
    def _show_calibration_dialog(self, pump_data, volume):
        """Affiche le dialogue de calibration"""
        content = BoxLayout(orientation='vertical', spacing=dp(15))
        
        # Instructions
        instructions = Label(
            text=f"1. Placez un verre vide sous la sortie\n"
                 f"2. Appuyez sur 'Démarrer versement'\n"
                 f"3. Mesurez le volume obtenu\n"
                 f"4. Entrez la mesure ci-dessous",
            halign='center',
            text_size=(dp(250), None)
        )
        content.add_widget(instructions)
        
        # Bouton de versement
        pour_btn = Button(
            text=f'Démarrer versement {volume}ml',
            size_hint_y=None,
            height=dp(50)
        )
        content.add_widget(pour_btn)
        
        # Champ de mesure
        measure_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        measure_layout.add_widget(Label(text='Volume mesuré:', size_hint_x=0.6))
        
        measure_input = TextInput(
            text='',
            multiline=False,
            input_filter='float',
            size_hint_x=0.4
        )
        measure_layout.add_widget(measure_input)
        content.add_widget(measure_layout)
        
        # Boutons
        buttons_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        
        cancel_btn = Button(text='Annuler', size_hint_x=0.33)
        apply_btn = Button(text='Appliquer', size_hint_x=0.33)
        test_btn = Button(text='Test 10ml', size_hint_x=0.34)
        
        buttons_layout.add_widget(cancel_btn)
        buttons_layout.add_widget(apply_btn)
        buttons_layout.add_widget(test_btn)
        
        content.add_widget(buttons_layout)
        
        popup = Popup(
            title=f'Calibration {pump_data["ingredient"]}',
            content=content,
            size_hint=(0.9, 0.8),
            auto_dismiss=False
        )
        
        def on_pour(*args):
            pour_btn.text = 'Versement en cours...'
            pour_btn.disabled = True
            # En mode réel, lancerait le versement
            Clock.schedule_once(lambda dt: (
                setattr(pour_btn, 'text', 'Versement terminé'),
                setattr(pour_btn, 'disabled', False)
            ), 3.0)
        
        def on_apply(*args):
            try:
                measured = float(measure_input.text)
                if 1 <= measured <= 500:
                    # Calculer nouveau facteur
                    new_factor = volume / measured
                    print(f"✅ Nouvelle calibration: {new_factor:.3f}")
                    # En mode réel, appliquerait la calibration
                    popup.dismiss()
                else:
                    measure_input.text = 'Valeur invalide'
            except ValueError:
                measure_input.text = 'Nombre requis'
        
        pour_btn.bind(on_press=on_pour)
        cancel_btn.bind(on_press=popup.dismiss)
        apply_btn.bind(on_press=on_apply)
        test_btn.bind(on_press=lambda x: self._test_pump(pump_data, 10))
        
        popup.open()
    
    def _test_pump(self, pump_data, volume):
        """Test une pompe"""
        print(f"🧪 Test pompe {pump_data['ingredient']}: {volume}ml")
        
        if PUMP_SUPPORT:
            try:
                # En mode réel, lancerait le test
                pass
            except Exception as e:
                print(f"Erreur test pompe: {e}")
        
        # Simulation démo
        self._show_status_message(f"Test {pump_data['ingredient']} terminé")
    
    def _update_setting(self, category, key, value):
        """Met à jour un réglage"""
        if category not in self.settings_data:
            self.settings_data[category] = {}
        
        self.settings_data[category][key] = value
        print(f"⚙️ Réglage: {category}.{key} = {value}")
    
    def _show_status_message(self, message):
        """Affiche un message de statut temporaire"""
        popup = Popup(
            title='Information',
            content=Label(text=message, halign='center'),
            size_hint=(0.6, 0.4),
            auto_dismiss=True
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 2.0)
    
    def _show_reset_confirmation(self, instance):
        """Confirme la remise à zéro"""
        content = BoxLayout(orientation='vertical', spacing=dp(15))
        
        content.add_widget(Label(
            text='⚠️ ATTENTION ⚠️\n\nCeci va remettre tous les réglages\naux valeurs par défaut.\n\nÊtes-vous sûr?',
            halign='center',
            color=(1, 0.5, 0, 1)
        ))
        
        buttons_layout = BoxLayout(orientation='horizontal')
        
        cancel_btn = Button(text='Annuler', size_hint_x=0.5)
        confirm_btn = Button(
            text='Confirmer Reset',
            size_hint_x=0.5,
            background_color=(1, 0.3, 0.3, 1)
        )
        
        buttons_layout.add_widget(cancel_btn)
        buttons_layout.add_widget(confirm_btn)
        content.add_widget(buttons_layout)
        
        popup = Popup(
            title='Confirmation Reset',
            content=content,
            size_hint=(0.8, 0.7),
            auto_dismiss=False
        )
        
        def on_confirm(*args):
            self._reset_settings()
            popup.dismiss()
        
        cancel_btn.bind(on_press=popup.dismiss)
        confirm_btn.bind(on_press=on_confirm)
        
        popup.open()
    
    def _reset_settings(self):
        """Remet les réglages à zéro"""
        # Recharger les défauts
        self.settings_data = self._load_settings()
        
        # Reconstruire l'interface
        self.clear_widgets()
        self._build_interface()
        
        print("🔄 Réglages remis aux valeurs par défaut")
        self._show_status_message("Réglages remis à zéro")
    
    def _go_back(self, instance):
        """Retourne au menu"""
        # Sauvegarder automatiquement avant de partir
        self._save_settings()
        
        print("⬅️ Retour au menu depuis réglages")
        if self.manager:
            self.manager.transition.direction = 'down'
            self.manager.current = 'menu'
    
    def on_enter(self):
        """Appelé à l'entrée de l'écran"""
        print("⚙️ Écran réglages affiché")
    
    def on_leave(self):
        """Appelé à la sortie de l'écran"""
        print("⚙️ Sortie écran réglages")
        # Sauvegarder avant de quitter
        self._save_settings()