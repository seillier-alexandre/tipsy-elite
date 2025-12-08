#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════
ÉCRAN NETTOYAGE - INTERFACE ART DÉCO KIVY
Système de nettoyage automatique des pompes et conduites
Design sophistiqué années 1920 pour écran rond 4"
═══════════════════════════════════════════════════════════════
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.progressbar import ProgressBar
from kivy.uix.popup import Popup
from kivy.uix.togglebutton import ToggleButton
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import dp
import threading
import time

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from hardware.pumps import get_pump_manager, initialize_pump_system
    PUMP_SUPPORT = True
except ImportError:
    PUMP_SUPPORT = False
    print("⚠️ Système pompes non disponible en mode démo")

from ..utils.round_display import RoundScreen, DecoTransition

class PumpCleaningItem(BoxLayout):
    """Widget de nettoyage individuel par pompe"""
    
    def __init__(self, pump_data, callback=None, **kwargs):
        super().__init__(orientation='horizontal', **kwargs)
        self.pump_data = pump_data
        self.callback = callback
        self.size_hint_y = None
        self.height = dp(50)
        self.is_cleaning = False
        
        # Nom de la pompe/ingrédient
        self.name_label = Label(
            text=pump_data.get('ingredient', f"Pompe {pump_data.get('id', '?')}"),
            size_hint_x=0.4,
            color=(0.97, 0.96, 0.91, 1),  # Crème
            halign='left',
            text_size=(dp(80), None)
        )
        
        # Statut
        self.status_label = Label(
            text="Prêt",
            size_hint_x=0.3,
            color=(0.83, 0.69, 0.22, 1),  # Doré
            halign='center'
        )
        
        # Bouton nettoyage
        self.clean_btn = ToggleButton(
            text="🧼",
            size_hint_x=0.3,
            size_hint_y=1
        )
        self.clean_btn.bind(on_press=self._on_clean_toggle)
        
        self.add_widget(self.name_label)
        self.add_widget(self.status_label)
        self.add_widget(self.clean_btn)
        
        # Style Art Déco
        self._setup_deco_style()
    
    def _setup_deco_style(self):
        """Style Art Déco"""
        with self.canvas.before:
            from kivy.graphics import Color, Line, RoundedRectangle
            
            # Fond subtil
            Color(0.04, 0.04, 0.04, 0.3)
            self.bg_rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[5]
            )
            
            # Bordure dorée fine
            Color(0.83, 0.69, 0.22, 0.5)
            self.border_line = Line(
                rounded_rectangle=(self.x, self.y, self.width, self.height, 5),
                width=1
            )
        
        self.bind(pos=self._update_graphics, size=self._update_graphics)
    
    def _update_graphics(self, *args):
        """Met à jour les graphiques"""
        if hasattr(self, 'bg_rect'):
            self.bg_rect.pos = self.pos
            self.bg_rect.size = self.size
        if hasattr(self, 'border_line'):
            self.border_line.rounded_rectangle = (self.x, self.y, self.width, self.height, 5)
    
    def _on_clean_toggle(self, instance):
        """Gestion du toggle nettoyage"""
        if instance.state == 'down':
            self._start_cleaning()
        else:
            self._stop_cleaning()
    
    def _start_cleaning(self):
        """Démarre le nettoyage"""
        self.is_cleaning = True
        self.status_label.text = "Nettoyage..."
        self.status_label.color = (0, 1, 0, 1)  # Vert
        
        if self.callback:
            self.callback('start', self.pump_data)
        
        # Animation du status
        anim = Animation(color=(0, 1, 0, 1), duration=0.5) + Animation(color=(0.83, 0.69, 0.22, 1), duration=0.5)
        anim.repeat = True
        anim.start(self.status_label)
    
    def _stop_cleaning(self):
        """Arrête le nettoyage"""
        self.is_cleaning = False
        self.status_label.text = "Prêt"
        self.status_label.color = (0.83, 0.69, 0.22, 1)  # Doré
        
        if self.callback:
            self.callback('stop', self.pump_data)
        
        # Arrêter animation
        Animation.cancel_all(self.status_label)
    
    def set_error(self, error_msg):
        """Marque en erreur"""
        self.is_cleaning = False
        self.clean_btn.state = 'normal'
        self.status_label.text = "Erreur"
        self.status_label.color = (1, 0, 0, 1)  # Rouge
        Animation.cancel_all(self.status_label)

class CleaningProgress(BoxLayout):
    """Widget de progression du nettoyage global"""
    
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.size_hint_y = None
        self.height = dp(120)
        
        # Titre
        self.title_label = Label(
            text='NETTOYAGE AUTOMATIQUE',
            size_hint_y=0.3,
            color=(0.83, 0.69, 0.22, 1),
            font_size='16sp',
            bold=True,
            halign='center'
        )
        
        # Barre de progression
        self.progress_bar = ProgressBar(
            max=100,
            value=0,
            size_hint_y=0.2
        )
        
        # Statut
        self.status_label = Label(
            text='Système prêt pour nettoyage',
            size_hint_y=0.25,
            color=(0.97, 0.96, 0.91, 0.8),
            font_size='12sp',
            halign='center'
        )
        
        # Temps estimé
        self.time_label = Label(
            text='',
            size_hint_y=0.25,
            color=(0.83, 0.69, 0.22, 0.7),
            font_size='11sp',
            halign='center'
        )
        
        self.add_widget(self.title_label)
        self.add_widget(self.progress_bar)
        self.add_widget(self.status_label)
        self.add_widget(self.time_label)
        
        # Style de la barre
        self._setup_progress_style()
    
    def _setup_progress_style(self):
        """Style Art Déco pour la barre"""
        with self.progress_bar.canvas.before:
            from kivy.graphics import Color, RoundedRectangle, Line
            
            # Fond
            Color(0.04, 0.04, 0.04, 0.8)
            self.bg_rect = RoundedRectangle(
                pos=self.progress_bar.pos,
                size=self.progress_bar.size,
                radius=[8]
            )
            
            # Bordure dorée
            Color(0.83, 0.69, 0.22, 0.8)
            self.border_line = Line(
                rounded_rectangle=(self.progress_bar.x, self.progress_bar.y, 
                                 self.progress_bar.width, self.progress_bar.height, 8),
                width=2
            )
        
        self.progress_bar.bind(pos=self._update_bg, size=self._update_bg)
    
    def _update_bg(self, *args):
        """Met à jour le style de la barre"""
        if hasattr(self, 'bg_rect'):
            self.bg_rect.pos = self.progress_bar.pos
            self.bg_rect.size = self.progress_bar.size
        if hasattr(self, 'border_line'):
            self.border_line.rounded_rectangle = (
                self.progress_bar.x, self.progress_bar.y,
                self.progress_bar.width, self.progress_bar.height, 8
            )
    
    def start_cleaning_cycle(self, estimated_time=180):
        """Démarre un cycle de nettoyage"""
        self.title_label.text = 'NETTOYAGE EN COURS'
        self.status_label.text = 'Purge des conduites...'
        self.time_label.text = f'Temps estimé: {estimated_time}s'
        self.progress_bar.value = 0
        
        # Animation du titre
        anim = Animation(color=(0, 1, 0, 1), duration=1.0) + Animation(color=(0.83, 0.69, 0.22, 1), duration=1.0)
        anim.repeat = True
        anim.start(self.title_label)
    
    def update_progress(self, step_name, progress, time_remaining=None):
        """Met à jour la progression"""
        self.status_label.text = step_name
        self.progress_bar.value = progress
        
        if time_remaining:
            self.time_label.text = f'Temps restant: {time_remaining}s'
        
        # Animation de la barre
        anim = Animation(value=progress, duration=0.5)
        anim.start(self.progress_bar)
    
    def set_completed(self):
        """Marque comme terminé"""
        Animation.cancel_all(self.title_label)
        self.title_label.text = '✅ NETTOYAGE TERMINÉ'
        self.title_label.color = (0, 1, 0, 1)
        self.status_label.text = 'Système propre et prêt'
        self.time_label.text = 'Machine prête à utiliser'
        self.progress_bar.value = 100
    
    def set_error(self, error_msg):
        """Marque en erreur"""
        Animation.cancel_all(self.title_label)
        self.title_label.text = '❌ ERREUR NETTOYAGE'
        self.title_label.color = (1, 0, 0, 1)
        self.status_label.text = error_msg
        self.time_label.text = ''

class CleaningScreen(RoundScreen):
    """Écran de nettoyage du système"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'cleaning'
        self.is_cleaning = False
        self.active_cleanings = set()
        
        self._build_interface()
        
        # Charger les pompes
        self._load_pumps()
    
    def _load_pumps(self):
        """Charge les informations des pompes"""
        self.pumps_data = []
        
        if PUMP_SUPPORT:
            try:
                manager = get_pump_manager()
                status = manager.get_system_status()
                
                for pump_status in status.get('pumps', []):
                    pump_data = {
                        'id': pump_status['id'],
                        'ingredient': pump_status['ingredient'],
                        'status': pump_status['status'],
                        'enabled': pump_status['enabled']
                    }
                    self.pumps_data.append(pump_data)
                
                print(f"✅ {len(self.pumps_data)} pompes chargées pour nettoyage")
                
            except Exception as e:
                print(f"❌ Erreur chargement pompes: {e}")
                self._load_demo_pumps()
        else:
            self._load_demo_pumps()
        
        # Reconstruire la liste si l'interface existe
        if hasattr(self, 'pumps_container'):
            self._rebuild_pumps_list()
    
    def _load_demo_pumps(self):
        """Charge des pompes de démonstration"""
        self.pumps_data = [
            {'id': 'pump_1', 'ingredient': 'Gin', 'status': 'idle', 'enabled': True},
            {'id': 'pump_2', 'ingredient': 'Vodka', 'status': 'idle', 'enabled': True},
            {'id': 'pump_3', 'ingredient': 'Rhum', 'status': 'idle', 'enabled': True},
            {'id': 'pump_4', 'ingredient': 'Whisky', 'status': 'idle', 'enabled': True},
            {'id': 'pump_7', 'ingredient': 'Sprite', 'status': 'idle', 'enabled': True},
            {'id': 'pump_8', 'ingredient': 'Coca Cola', 'status': 'idle', 'enabled': True}
        ]
    
    def _build_interface(self):
        """Construit l'interface de nettoyage"""
        main_layout = BoxLayout(orientation='vertical', spacing=dp(15), padding=dp(20))
        
        # Titre
        title_label = Label(
            text='🧼 NETTOYAGE SYSTÈME',
            size_hint_y=0.1,
            color=(0.83, 0.69, 0.22, 1),
            font_size='18sp',
            bold=True,
            halign='center'
        )
        
        # Progression globale
        self.progress_widget = CleaningProgress()
        
        # Liste des pompes
        pumps_title = Label(
            text='Pompes individuelles:',
            size_hint_y=None,
            height=dp(25),
            color=(0.97, 0.96, 0.91, 0.8),
            font_size='12sp',
            halign='left'
        )
        
        # Container scrollable pour pompes
        from kivy.uix.scrollview import ScrollView
        scroll = ScrollView(size_hint=(1, 0.35))
        
        self.pumps_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(5)
        )
        self.pumps_container.bind(minimum_height=self.pumps_container.setter('height'))
        
        scroll.add_widget(self.pumps_container)
        
        # Boutons d'action
        self._build_action_buttons(main_layout)
        
        # Assembler
        main_layout.add_widget(title_label)
        main_layout.add_widget(self.progress_widget)
        main_layout.add_widget(pumps_title)
        main_layout.add_widget(scroll)
        
        self.add_widget(main_layout)
        
        # Animation d'entrée
        DecoTransition.slide_from_center(main_layout, 0.8)
    
    def _build_action_buttons(self, parent_layout):
        """Construit les boutons d'action"""
        buttons_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=0.15,
            spacing=dp(10)
        )
        
        # Bouton Retour
        back_btn = Button(
            text='⬅️ RETOUR',
            size_hint_x=0.25
        )
        back_btn.bind(on_press=self._go_back)
        
        # Bouton Nettoyage complet
        self.full_clean_btn = Button(
            text='🚿 NETTOYAGE COMPLET',
            size_hint_x=0.5
        )
        self.full_clean_btn.bind(on_press=self._start_full_cleaning)
        
        # Bouton Arrêt d'urgence
        emergency_btn = Button(
            text='🚨 ARRÊT',
            size_hint_x=0.25,
            background_color=(1, 0.3, 0.3, 1)
        )
        emergency_btn.bind(on_press=self._emergency_stop)
        
        buttons_layout.add_widget(back_btn)
        buttons_layout.add_widget(self.full_clean_btn)
        buttons_layout.add_widget(emergency_btn)
        
        parent_layout.add_widget(buttons_layout)
    
    def _rebuild_pumps_list(self):
        """Reconstruit la liste des pompes"""
        self.pumps_container.clear_widgets()
        
        for pump_data in self.pumps_data:
            if pump_data.get('enabled', False):
                pump_item = PumpCleaningItem(
                    pump_data,
                    callback=self._on_pump_cleaning_toggle
                )
                self.pumps_container.add_widget(pump_item)
    
    def _on_pump_cleaning_toggle(self, action, pump_data):
        """Callback pour nettoyage individuel"""
        pump_id = pump_data['id']
        
        if action == 'start':
            print(f"🧼 Démarrage nettoyage pompe: {pump_data['ingredient']}")
            self.active_cleanings.add(pump_id)
            self._start_individual_cleaning(pump_data)
            
        elif action == 'stop':
            print(f"🛑 Arrêt nettoyage pompe: {pump_data['ingredient']}")
            self.active_cleanings.discard(pump_id)
            self._stop_individual_cleaning(pump_data)
    
    def _start_individual_cleaning(self, pump_data):
        """Démarre le nettoyage d'une pompe"""
        if PUMP_SUPPORT:
            try:
                # Nettoyage réel avec système de pompes
                def run_cleaning():
                    try:
                        manager = get_pump_manager()
                        # Faire tourner la pompe avec de l'eau pendant 30s
                        # (nécessiterait une pompe d'eau séparée dans un vrai système)
                        print(f"Nettoyage pompe {pump_data['id']} pendant 30 secondes")
                        time.sleep(30)  # Simulation
                        
                    except Exception as e:
                        print(f"Erreur nettoyage pompe: {e}")
                
                thread = threading.Thread(target=run_cleaning)
                thread.daemon = True
                thread.start()
                
            except Exception as e:
                print(f"Erreur démarrage nettoyage: {e}")
        else:
            # Mode démo
            print(f"[DÉMO] Nettoyage pompe {pump_data['ingredient']}")
    
    def _stop_individual_cleaning(self, pump_data):
        """Arrête le nettoyage d'une pompe"""
        print(f"Arrêt nettoyage pompe: {pump_data['ingredient']}")
        # En mode réel, arrêterait la pompe
    
    def _start_full_cleaning(self, instance):
        """Démarre un cycle de nettoyage complet"""
        if self.is_cleaning:
            self._stop_full_cleaning()
            return
        
        print("🚿 Démarrage nettoyage complet du système")
        self.is_cleaning = True
        self.full_clean_btn.text = '🛑 ARRÊTER'
        self.full_clean_btn.background_color = (1, 0.3, 0.3, 1)
        
        # Arrêter tous les nettoyages individuels
        for child in self.pumps_container.children:
            if hasattr(child, 'clean_btn'):
                child.clean_btn.state = 'normal'
                child._stop_cleaning()
        
        self.active_cleanings.clear()
        
        # Démarrer le cycle
        self.progress_widget.start_cleaning_cycle(180)  # 3 minutes
        
        # Lancer en arrière-plan
        if PUMP_SUPPORT:
            thread = threading.Thread(target=self._run_full_cleaning_cycle)
            thread.daemon = True
            thread.start()
        else:
            self._demo_full_cleaning()
    
    def _run_full_cleaning_cycle(self):
        """Exécute un cycle de nettoyage complet réel"""
        try:
            manager = get_pump_manager()
            
            phases = [
                ("Purge des conduites", 20, 30),
                ("Rinçage à l'eau", 50, 60),
                ("Nettoyage désinfectant", 80, 60),
                ("Rinçage final", 100, 30)
            ]
            
            for phase_name, progress, duration in phases:
                if not self.is_cleaning:
                    break
                
                Clock.schedule_once(
                    lambda dt, name=phase_name, prog=progress, dur=duration: 
                    self.progress_widget.update_progress(name, prog, dur), 0
                )
                
                # Simulation du processus
                for i in range(duration):
                    if not self.is_cleaning:
                        break
                    time.sleep(1)
            
            if self.is_cleaning:
                Clock.schedule_once(lambda dt: self.progress_widget.set_completed(), 0)
                Clock.schedule_once(lambda dt: self._cleaning_finished(True), 0)
            
        except Exception as e:
            print(f"Erreur cycle nettoyage: {e}")
            Clock.schedule_once(lambda dt: self.progress_widget.set_error(str(e)), 0)
            Clock.schedule_once(lambda dt: self._cleaning_finished(False), 0)
    
    def _demo_full_cleaning(self):
        """Simulation démo du nettoyage complet"""
        phases = [
            ("Purge des conduites", 20),
            ("Rinçage à l'eau", 50),
            ("Nettoyage désinfectant", 80),
            ("Rinçage final", 100)
        ]
        
        def run_phase(phase_index):
            if phase_index < len(phases) and self.is_cleaning:
                phase_name, progress = phases[phase_index]
                time_remaining = (len(phases) - phase_index) * 20
                
                self.progress_widget.update_progress(phase_name, progress, time_remaining)
                
                if phase_index < len(phases) - 1:
                    Clock.schedule_once(lambda dt: run_phase(phase_index + 1), 3.0)
                else:
                    Clock.schedule_once(lambda dt: self.progress_widget.set_completed(), 2.0)
                    Clock.schedule_once(lambda dt: self._cleaning_finished(True), 3.0)
        
        Clock.schedule_once(lambda dt: run_phase(0), 1.0)
    
    def _stop_full_cleaning(self):
        """Arrête le nettoyage complet"""
        print("🛑 Arrêt du nettoyage complet")
        self.is_cleaning = False
        self.full_clean_btn.text = '🚿 NETTOYAGE COMPLET'
        self.full_clean_btn.background_color = (1, 1, 1, 1)
        self.progress_widget.set_error("Nettoyage interrompu")
    
    def _cleaning_finished(self, success):
        """Finalise le nettoyage"""
        self.is_cleaning = False
        self.full_clean_btn.text = '🚿 NETTOYAGE COMPLET'
        self.full_clean_btn.background_color = (1, 1, 1, 1)
        
        if success:
            print("✅ Nettoyage complet terminé avec succès")
        else:
            print("❌ Erreur pendant le nettoyage")
    
    def _emergency_stop(self, instance):
        """Arrêt d'urgence de tous les nettoyages"""
        print("🚨 ARRÊT D'URGENCE NETTOYAGE")
        
        # Arrêter tout
        self._stop_full_cleaning()
        
        # Arrêter nettoyages individuels
        for child in self.pumps_container.children:
            if hasattr(child, 'clean_btn'):
                child.clean_btn.state = 'normal'
                child._stop_cleaning()
        
        self.active_cleanings.clear()
        
        # Arrêt système pompes si disponible
        if PUMP_SUPPORT:
            try:
                manager = get_pump_manager()
                manager.emergency_stop()
                Clock.schedule_once(lambda dt: manager.reset_emergency(), 2.0)
            except Exception as e:
                print(f"Erreur arrêt urgence pompes: {e}")
    
    def _go_back(self, instance):
        """Retourne au menu"""
        # Vérifier si nettoyage en cours
        if self.is_cleaning or self.active_cleanings:
            self._show_confirm_exit()
        else:
            self._do_go_back()
    
    def _show_confirm_exit(self):
        """Confirme la sortie pendant nettoyage"""
        content = BoxLayout(orientation='vertical', spacing=dp(10))
        
        content.add_widget(Label(
            text='Nettoyage en cours!\nVoulez-vous vraiment quitter?',
            halign='center'
        ))
        
        buttons_layout = BoxLayout(orientation='horizontal')
        
        cancel_btn = Button(text='Annuler', size_hint_x=0.5)
        confirm_btn = Button(text='Quitter', size_hint_x=0.5, background_color=(1, 0.3, 0.3, 1))
        
        buttons_layout.add_widget(cancel_btn)
        buttons_layout.add_widget(confirm_btn)
        content.add_widget(buttons_layout)
        
        popup = Popup(
            title='Confirmation',
            content=content,
            size_hint=(0.8, 0.6),
            auto_dismiss=False
        )
        
        cancel_btn.bind(on_press=popup.dismiss)
        confirm_btn.bind(on_press=lambda x: (self._emergency_stop(None), popup.dismiss(), self._do_go_back()))
        
        popup.open()
    
    def _do_go_back(self):
        """Retourne effectivement au menu"""
        print("⬅️ Retour au menu depuis nettoyage")
        if self.manager:
            self.manager.transition.direction = 'up'
            self.manager.current = 'menu'
    
    def on_enter(self):
        """Appelé à l'entrée de l'écran"""
        print("🧼 Écran nettoyage affiché")
        # Recharger les pompes au cas où
        self._load_pumps()
    
    def on_leave(self):
        """Appelé à la sortie de l'écran"""
        print("🧼 Sortie écran nettoyage")
        # Note: Ne pas arrêter automatiquement le nettoyage ici
        # L'utilisateur pourrait vouloir revenir voir le progrès