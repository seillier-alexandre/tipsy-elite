#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════
ÉCRAN DE VEILLE - INTERFACE ART DÉCO KIVY
Économiseur d'écran avec animations élégantes Art Déco
Design sophistiqué années 1920 pour écran rond 4"
═══════════════════════════════════════════════════════════════
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Ellipse, PushMatrix, PopMatrix, Rotate, Rectangle
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import dp
import math
import time
import random

from ..utils.round_display import RoundScreen

class DecoRay(Widget):
    """Rayon Art Déco animé"""
    
    def __init__(self, angle=0, length=100, **kwargs):
        super().__init__(**kwargs)
        self.angle = angle
        self.length = length
        self.opacity_factor = 1.0
        
        with self.canvas:
            PushMatrix()
            self.rotation = Rotate(angle=self.angle, origin=(0, 0))
            Color(0.83, 0.69, 0.22, 0.6)  # Doré semi-transparent
            self.line = Line(points=[0, 0, 0, self.length], width=2)
            PopMatrix()
        
        self.bind(pos=self._update_graphics, size=self._update_graphics)
        
        # Animation continue
        self._start_animation()
    
    def _update_graphics(self, *args):
        """Met à jour les graphiques selon la position"""
        center_x = self.center_x
        center_y = self.center_y
        
        self.rotation.origin = (center_x, center_y)
        
        # Calculer fin du rayon selon l'angle
        end_x = center_x + self.length * math.cos(math.radians(self.angle))
        end_y = center_y + self.length * math.sin(math.radians(self.angle))
        
        self.line.points = [center_x, center_y, end_x, end_y]
    
    def _start_animation(self):
        """Démarre l'animation du rayon"""
        def update_opacity(dt):
            # Oscillation de l'opacité
            t = time.time() * 0.5 + self.angle * 0.02  # Décalage selon l'angle
            self.opacity_factor = 0.3 + 0.7 * (math.sin(t) + 1) / 2
            
            # Rotation lente
            self.angle += 0.2
            if self.angle >= 360:
                self.angle -= 360
            
            self.rotation.angle = self.angle
            self._update_graphics()
        
        Clock.schedule_interval(update_opacity, 1/30.0)  # 30 FPS

class SunburstWidget(Widget):
    """Widget de rayons de soleil Art Déco"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rays = []
        self.animation_phase = 0
        
        # Créer les rayons
        self._create_rays()
        
        # Animation globale
        self._start_animation()
    
    def _create_rays(self):
        """Crée les rayons dorés"""
        ray_count = 12
        base_length = min(self.width, self.height) * 0.4 if self.width and self.height else 150
        
        for i in range(ray_count):
            angle = (360 / ray_count) * i
            # Alterner la longueur des rayons
            length = base_length if i % 2 == 0 else base_length * 0.7
            
            ray = DecoRay(angle=angle, length=length)
            self.add_widget(ray)
            self.rays.append(ray)
        
        self.bind(size=self._update_ray_lengths)
    
    def _update_ray_lengths(self, *args):
        """Met à jour la longueur des rayons selon la taille"""
        if self.rays and self.width and self.height:
            base_length = min(self.width, self.height) * 0.4
            
            for i, ray in enumerate(self.rays):
                ray.length = base_length if i % 2 == 0 else base_length * 0.7
                ray._update_graphics()
    
    def _start_animation(self):
        """Animation globale du sunburst"""
        def animate_sunburst(dt):
            self.animation_phase += 1
            
            # Faire pulser l'ensemble
            scale_factor = 0.9 + 0.1 * math.sin(self.animation_phase * 0.1)
            
            # Animation de rotation générale très lente
            rotation_angle = self.animation_phase * 0.1
            
            # Appliquer à tous les rayons
            for i, ray in enumerate(self.rays):
                # Décalage de phase par rayon
                phase_offset = i * 0.2
                ray_scale = scale_factor * (0.8 + 0.2 * math.sin(self.animation_phase * 0.1 + phase_offset))
                
                # Mise à jour virtuelle de la longueur
                base_length = min(self.width, self.height) * 0.4 if self.width and self.height else 150
                ray.length = (base_length if i % 2 == 0 else base_length * 0.7) * ray_scale
        
        Clock.schedule_interval(animate_sunburst, 1/20.0)  # 20 FPS

class FloatingOrb(Widget):
    """Orbe flottant décoratif"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size = (dp(30), dp(30))
        self.orb_opacity = 0.7
        
        with self.canvas:
            Color(0.83, 0.69, 0.22, self.orb_opacity)  # Doré
            self.orb_ellipse = Ellipse(pos=self.pos, size=self.size)
            
            # Bordure plus claire
            Color(0.9, 0.8, 0.5, self.orb_opacity * 0.8)
            self.orb_line = Line(ellipse=(self.x, self.y, self.width, self.height), width=1)
        
        self.bind(pos=self._update_graphics, size=self._update_graphics)
        
        # Position et mouvement aléatoires
        self._setup_movement()
    
    def _update_graphics(self, *args):
        """Met à jour les graphiques"""
        self.orb_ellipse.pos = self.pos
        self.orb_ellipse.size = self.size
        self.orb_line.ellipse = (self.x, self.y, self.width, self.height)
    
    def _setup_movement(self):
        """Configure le mouvement flottant"""
        # Position initiale aléatoire
        if self.parent:
            max_x = self.parent.width - self.width
            max_y = self.parent.height - self.height
            self.pos = (random.uniform(0, max_x), random.uniform(0, max_y))
        
        # Démarrer animation de flottement
        self._animate_float()
    
    def _animate_float(self):
        """Animation de flottement"""
        if not self.parent:
            return
        
        # Nouvelle position aléatoire
        margin = dp(50)
        new_x = random.uniform(margin, self.parent.width - self.width - margin)
        new_y = random.uniform(margin, self.parent.height - self.height - margin)
        
        # Animation vers la nouvelle position
        duration = random.uniform(8, 15)  # Durée variable
        
        anim = Animation(x=new_x, y=new_y, duration=duration, t='in_out_sine')
        
        # Programmer la prochaine animation
        def next_movement(*args):
            Clock.schedule_once(lambda dt: self._animate_float(), random.uniform(1, 3))
        
        anim.bind(on_complete=next_movement)
        anim.start(self)
        
        # Animation d'opacité simultanée
        opacity_anim = (Animation(opacity=0.3, duration=duration/2, t='in_sine') + 
                       Animation(opacity=0.7, duration=duration/2, t='out_sine'))
        opacity_anim.start(self)

class ClockDisplay(BoxLayout):
    """Affichage de l'heure Art Déco"""
    
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.size_hint = (None, None)
        self.size = (dp(200), dp(100)
        
        # Heure
        self.time_label = Label(
            text='',
            font_size='32sp',
            color=(0.83, 0.69, 0.22, 1),  # Doré
            bold=True,
            halign='center'
        )
        
        # Date
        self.date_label = Label(
            text='',
            font_size='14sp',
            color=(0.97, 0.96, 0.91, 0.8),  # Crème pâle
            halign='center'
        )
        
        self.add_widget(self.time_label)
        self.add_widget(self.date_label)
        
        # Mettre à jour l'heure
        self._update_time()
        Clock.schedule_interval(self._update_time, 1.0)
    
    def _update_time(self, *args):
        """Met à jour l'affichage de l'heure"""
        import datetime
        now = datetime.datetime.now()
        
        # Format heure élégant
        time_str = now.strftime('%H:%M')
        self.time_label.text = time_str
        
        # Format date Art Déco
        date_str = now.strftime('%A %d %B %Y')
        self.date_label.text = date_str.upper()

class MachineStatus(BoxLayout):
    """Statut de la machine en veille"""
    
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.size_hint = (None, None)
        self.size = (dp(180), dp(80))
        
        # Statut principal
        self.status_label = Label(
            text='MACHINE PRÊTE',
            font_size='16sp',
            color=(0, 1, 0, 0.8),  # Vert
            bold=True,
            halign='center'
        )
        
        # Détails
        self.details_label = Label(
            text='Appuyez pour commencer',
            font_size='11sp',
            color=(0.97, 0.96, 0.91, 0.6),
            halign='center',
            italic=True
        )
        
        self.add_widget(self.status_label)
        self.add_widget(self.details_label)
        
        # Animation du statut
        self._animate_status()
    
    def _animate_status(self):
        """Animation du statut"""
        # Pulsation subtile
        anim = (Animation(opacity=0.6, duration=2.0, t='in_out_sine') + 
               Animation(opacity=1.0, duration=2.0, t='in_out_sine'))
        anim.repeat = True
        anim.start(self.status_label)

class ScreensaverScreen(RoundScreen):
    """Écran de veille Art Déco"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'screensaver'
        self.is_active = False
        self.orbs = []
        
        self._build_interface()
        
        # Gestion du touch pour sortir de veille
        self.bind(on_touch_down=self._on_touch)
    
    def _build_interface(self):
        """Construit l'interface de veille"""
        # Layout principal
        main_layout = FloatLayout()
        
        # Animation de fond - Sunburst central
        self.sunburst = SunburstWidget()
        self.sunburst.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        self.sunburst.size_hint = (0.8, 0.8)
        main_layout.add_widget(self.sunburst)
        
        # Horloge Art Déco
        self.clock_display = ClockDisplay()
        self.clock_display.pos_hint = {'center_x': 0.5, 'center_y': 0.7}
        main_layout.add_widget(self.clock_display)
        
        # Statut machine
        self.status_display = MachineStatus()
        self.status_display.pos_hint = {'center_x': 0.5, 'center_y': 0.3}
        main_layout.add_widget(self.status_display)
        
        # Logo/Titre en bas
        brand_label = Label(
            text='COCKTAIL MACHINE\n• ART DÉCO COLLECTION •',
            font_size='10sp',
            color=(0.83, 0.69, 0.22, 0.5),
            halign='center',
            pos_hint={'center_x': 0.5, 'center_y': 0.1},
            size_hint=(None, None),
            height=dp(50)
        )
        main_layout.add_widget(brand_label)
        
        # Créer orbes flottants
        self._create_floating_orbs(main_layout)
        
        self.add_widget(main_layout)
    
    def _create_floating_orbs(self, parent):
        """Crée les orbes décoratifs flottants"""
        orb_count = 6
        
        for i in range(orb_count):
            orb = FloatingOrb()
            parent.add_widget(orb)
            self.orbs.append(orb)
            
            # Démarrer le mouvement avec un délai aléatoire
            Clock.schedule_once(
                lambda dt, o=orb: o._setup_movement(),
                random.uniform(0, 3)
            )
    
    def start_screensaver(self):
        """Active l'économiseur d'écran"""
        if self.is_active:
            return
        
        self.is_active = True
        print("🌙 Économiseur d'écran activé")
        
        # Animations d'entrée
        self.opacity = 0
        anim = Animation(opacity=1, duration=2.0, t='in_out_sine')
        anim.start(self)
        
        # Réduire la luminosité (simulation)
        self._dim_screen()
    
    def stop_screensaver(self):
        """Désactive l'économiseur d'écran"""
        if not self.is_active:
            return
        
        self.is_active = False
        print("☀️ Économiseur d'écran désactivé")
        
        # Restaurer luminosité
        self._restore_screen()
        
        # Retour au menu
        if self.manager:
            self.manager.transition.direction = 'right'
            self.manager.current = 'menu'
    
    def _dim_screen(self):
        """Réduit la luminosité (simulation)"""
        # En mode réel, on pourrait contrôler la luminosité hardware
        # Ici on simule en assombrissant légèrement l'interface
        
        with self.canvas.before:
            Color(0, 0, 0, 0.3)  # Overlay sombre léger
            self.dim_overlay = Rectangle(pos=self.pos, size=self.size)
        
        self.bind(pos=self._update_overlay, size=self._update_overlay)
    
    def _update_overlay(self, *args):
        """Met à jour l'overlay d'assombrissement"""
        if hasattr(self, 'dim_overlay'):
            self.dim_overlay.pos = self.pos
            self.dim_overlay.size = self.size
    
    def _restore_screen(self):
        """Restaure la luminosité normale"""
        if hasattr(self, 'dim_overlay'):
            self.canvas.before.remove(self.dim_overlay)
            delattr(self, 'dim_overlay')
    
    def _on_touch(self, instance, touch):
        """Gestion du touch pour sortir de veille"""
        if self.is_active and self.collide_point(*touch.pos):
            print("👆 Touch détecté - Sortie de veille")
            self.stop_screensaver()
            return True
        return False
    
    def update_machine_status(self, status_text, status_color=(0, 1, 0, 0.8)):
        """Met à jour le statut de la machine"""
        if hasattr(self, 'status_display'):
            self.status_display.status_label.text = status_text
            self.status_display.status_label.color = status_color
    
    def on_enter(self):
        """Appelé quand l'écran devient actif"""
        print("🌙 Écran de veille affiché")
        self.start_screensaver()
        
        # Programmer vérification statut machine
        Clock.schedule_interval(self._check_machine_status, 30.0)  # Toutes les 30s
    
    def on_leave(self):
        """Appelé quand on quitte l'écran"""
        print("🌙 Sortie écran de veille")
        self.is_active = False
        
        # Arrêter vérifications
        Clock.unschedule(self._check_machine_status)
        
        # Nettoyer overlay si présent
        self._restore_screen()
    
    def _check_machine_status(self, *args):
        """Vérifie périodiquement le statut de la machine"""
        try:
            # En mode réel, vérifierait le statut des pompes, erreurs, etc.
            # Ici on simule un statut "OK"
            
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
            
            try:
                from hardware.pumps import get_pump_manager
                manager = get_pump_manager()
                status = manager.get_system_status()
                
                if status.get('emergency_stop', False):
                    self.update_machine_status('ARRÊT D\'URGENCE', (1, 0, 0, 1))
                elif status.get('active_pumps', 0) > 0:
                    self.update_machine_status('PRÉPARATION EN COURS', (1, 1, 0, 1))
                else:
                    self.update_machine_status('MACHINE PRÊTE', (0, 1, 0, 0.8))
                    
            except:
                # Mode démo ou erreur
                self.update_machine_status('MACHINE PRÊTE', (0, 1, 0, 0.8))
                
        except Exception as e:
            print(f"Erreur vérification statut: {e}")

# Fonction utilitaire pour activer l'économiseur depuis d'autres écrans
def activate_screensaver_after_delay(screen_manager, delay_seconds=300):
    """Active l'économiseur après un délai d'inactivité"""
    
    def activate_screensaver(*args):
        if screen_manager.current != 'screensaver':
            print(f"🌙 Activation automatique économiseur (inactivité {delay_seconds}s)")
            screen_manager.transition.direction = 'left'
            screen_manager.current = 'screensaver'
    
    # Programmer l'activation
    event = Clock.schedule_once(activate_screensaver, delay_seconds)
    
    return event  # Retourner pour pouvoir l'annuler si nécessaire