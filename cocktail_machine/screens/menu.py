#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════
ÉCRAN MENU PRINCIPAL - INTERFACE ART DÉCO KIVY
Menu principal avec navigation et sélection de cocktails
Design sophistiqué années 1920 pour écran rond 4"
═══════════════════════════════════════════════════════════════
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import dp

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

try:
    from cocktail_manager import get_cocktail_manager
    COCKTAIL_SUPPORT = True
except ImportError:
    COCKTAIL_SUPPORT = False
    print("⚠️ Cocktail Manager non disponible en mode démo")
except Exception as e:
    COCKTAIL_SUPPORT = False
    print(f"⚠️ Erreur chargement Cocktail Manager: {e}")

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.round_display import RoundScreen, DecoTransition

class CocktailCard(BoxLayout):
    """Carte de cocktail avec style Art Déco"""
    
    def __init__(self, cocktail_data, callback=None, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.cocktail_data = cocktail_data
        self.callback = callback
        self.size_hint = (None, None)
        self.size = (dp(150), dp(180))
        
        # Image du cocktail
        self.cocktail_image = Image(
            source='assets/images/cocktails/default.png',
            size_hint=(1, 0.7),
            allow_stretch=True,
            keep_ratio=True
        )
        
        # Nom du cocktail
        self.name_label = Label(
            text=cocktail_data.get('name', 'Cocktail'),
            size_hint=(1, 0.2),
            font_size='14sp',
            color=(0.83, 0.69, 0.22, 1),  # Doré
            bold=True,
            halign='center',
            text_size=(dp(140), None)
        )
        
        # Détails (difficulté, temps)
        details_text = f"⭐ {cocktail_data.get('difficulty', 1)}/5 • ⏱ {cocktail_data.get('preparation_time', 60)}s"
        self.details_label = Label(
            text=details_text,
            size_hint=(1, 0.1),
            font_size='10sp',
            color=(0.97, 0.96, 0.91, 0.8),  # Crème pâle
            halign='center'
        )
        
        self.add_widget(self.cocktail_image)
        self.add_widget(self.name_label)
        self.add_widget(self.details_label)
        
        # Style Art Déco
        self._setup_art_deco_style()
        
        # Gestion du touch
        self.bind(on_touch_down=self.on_cocktail_touch)
        
        # Animation d'entrée
        DecoTransition.fade_in_gold(self, 0.8)
    
    def _setup_art_deco_style(self):
        """Applique le style Art Déco à la carte"""
        with self.canvas.before:
            from kivy.graphics import Color, RoundedRectangle, Line
            
            # Fond noir semi-transparent
            Color(0.04, 0.04, 0.04, 0.9)
            self.bg_rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[10]
            )
            
            # Bordure dorée
            Color(0.83, 0.69, 0.22, 1)
            self.border_line = Line(
                rounded_rectangle=(self.x, self.y, self.width, self.height, 10),
                width=2
            )
            
            # Coins décoratifs
            Color(0.83, 0.69, 0.22, 0.7)
            self.corner_lines = [
                Line(points=[self.x + 15, self.y + 15, self.x + 25, self.y + 15, self.x + 20, self.y + 20], width=1),
                Line(points=[self.right - 25, self.y + 15, self.right - 15, self.y + 15, self.right - 20, self.y + 20], width=1)
            ]
        
        # Mettre à jour position quand le widget bouge
        self.bind(pos=self._update_graphics, size=self._update_graphics)
    
    def _update_graphics(self, *args):
        """Met à jour les graphiques quand position/taille change"""
        if hasattr(self, 'bg_rect'):
            self.bg_rect.pos = self.pos
            self.bg_rect.size = self.size
        
        if hasattr(self, 'border_line'):
            self.border_line.rounded_rectangle = (self.x, self.y, self.width, self.height, 10)
    
    def on_cocktail_touch(self, instance, touch):
        """Gestion du touch sur la carte cocktail"""
        if self.collide_point(*touch.pos):
            # Animation de sélection
            anim = Animation(scale=0.95, duration=0.1) + Animation(scale=1.0, duration=0.1)
            anim.start(self)
            
            if self.callback:
                Clock.schedule_once(lambda dt: self.callback(self.cocktail_data), 0.2)
            return True
        return False

class MenuScreen(RoundScreen):
    """Écran menu principal avec design Art Déco"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'menu'
        self.cocktails_data = []
        
        # Charger les cocktails
        self._load_cocktails()
        
        # Construire l'interface
        self._build_interface()
        
        # Animation d'entrée
        Clock.schedule_once(self._animate_entrance, 0.5)
    
    def _load_cocktails(self):
        """Charge les données de cocktails"""
        if COCKTAIL_SUPPORT:
            try:
                manager = get_cocktail_manager()
                cocktails = manager.database.get_makeable_cocktails()
                
                self.cocktails_data = []
                for cocktail in cocktails[:10]:  # Limiter à 10 pour l'écran
                    cocktail_info = {
                        'id': cocktail.id,
                        'name': cocktail.display_name or cocktail.name,
                        'difficulty': cocktail.difficulty,
                        'preparation_time': cocktail.preparation_time,
                        'description': cocktail.description,
                        'category': cocktail.category,
                        'is_makeable': cocktail.is_makeable
                    }
                    self.cocktails_data.append(cocktail_info)
                
                print(f"✅ {len(self.cocktails_data)} cocktails chargés")
                
            except Exception as e:
                print(f"❌ Erreur chargement cocktails: {e}")
                self._load_demo_cocktails()
        else:
            self._load_demo_cocktails()
    
    def _load_demo_cocktails(self):
        """Charge des cocktails de démonstration"""
        self.cocktails_data = [
            {'id': 'gin_tonic', 'name': 'Gin Tonic', 'difficulty': 1, 'preparation_time': 45, 'category': 'classic'},
            {'id': 'vodka_cranberry', 'name': 'Vodka Cranberry', 'difficulty': 1, 'preparation_time': 30, 'category': 'modern'},
            {'id': 'rum_cola', 'name': 'Rum & Cola', 'difficulty': 1, 'preparation_time': 30, 'category': 'classic'},
            {'id': 'tequila_sunrise', 'name': 'Tequila Sunrise', 'difficulty': 2, 'preparation_time': 60, 'category': 'tropical'},
            {'id': 'whisky_cola', 'name': 'Whisky Cola', 'difficulty': 1, 'preparation_time': 35, 'category': 'classic'},
            {'id': 'brandy_orange', 'name': 'Brandy Orange', 'difficulty': 2, 'preparation_time': 75, 'category': 'classic'}
        ]
    
    def _build_interface(self):
        """Construit l'interface utilisateur"""
        main_layout = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(20))
        
        # Titre principal avec style Art Déco
        title_layout = BoxLayout(orientation='vertical', size_hint_y=0.2)
        
        title_label = Label(
            text='MACHINE À COCKTAILS',
            font_size='24sp',
            color=(0.83, 0.69, 0.22, 1),  # Doré
            bold=True,
            halign='center',
            size_hint_y=0.7
        )
        
        subtitle_label = Label(
            text='Collection Prohibition • Art Déco 1925',
            font_size='12sp',
            color=(0.97, 0.96, 0.91, 0.7),  # Crème pâle
            halign='center',
            size_hint_y=0.3,
            italic=True
        )
        
        title_layout.add_widget(title_label)
        title_layout.add_widget(subtitle_label)
        
        # Grille de cocktails avec scroll
        scroll = ScrollView(size_hint=(1, 0.65))
        
        cocktails_grid = GridLayout(
            cols=2,
            spacing=dp(15),
            size_hint_y=None,
            padding=(dp(10), 0)
        )
        cocktails_grid.bind(minimum_height=cocktails_grid.setter('height'))
        
        # Créer les cartes de cocktails
        for cocktail_data in self.cocktails_data:
            card = CocktailCard(
                cocktail_data,
                callback=self._on_cocktail_selected
            )
            cocktails_grid.add_widget(card)
        
        scroll.add_widget(cocktails_grid)
        
        # Boutons de navigation
        nav_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=0.15,
            spacing=dp(20),
            padding=(dp(40), 0)
        )
        
        # Bouton Settings
        settings_btn = Button(
            text='⚙️ RÉGLAGES',
            size_hint=(0.5, 1)
        )
        settings_btn.bind(on_press=self._go_to_settings)
        
        # Bouton Nettoyage
        cleaning_btn = Button(
            text='🧼 NETTOYAGE',
            size_hint=(0.5, 1)
        )
        cleaning_btn.bind(on_press=self._go_to_cleaning)
        
        nav_layout.add_widget(settings_btn)
        nav_layout.add_widget(cleaning_btn)
        
        # Assembler l'interface
        main_layout.add_widget(title_layout)
        main_layout.add_widget(scroll)
        main_layout.add_widget(nav_layout)
        
        self.add_widget(main_layout)
    
    def _animate_entrance(self, dt):
        """Animation d'entrée de l'écran"""
        # Animation du titre depuis le haut
        if self.children:
            main_layout = self.children[0]
            if main_layout.children:
                title_layout = main_layout.children[-1]  # Premier ajouté = dernier dans la liste
                
                # Effet de glissement depuis le centre
                DecoTransition.slide_from_center(title_layout, 0.8)
    
    def _on_cocktail_selected(self, cocktail_data):
        """Callback quand un cocktail est sélectionné"""
        print(f"🍸 Cocktail sélectionné: {cocktail_data['name']}")
        
        # Aller à l'écran de cocktail
        if self.manager:
            cocktail_screen = self.manager.get_screen('cocktail')
            if hasattr(cocktail_screen, 'set_cocktail'):
                cocktail_screen.set_cocktail(cocktail_data)
            
            self.manager.transition.direction = 'left'
            self.manager.current = 'cocktail'
    
    def _go_to_settings(self, instance):
        """Va à l'écran de réglages"""
        print("⚙️ Ouverture des réglages")
        if self.manager:
            self.manager.transition.direction = 'up'
            self.manager.current = 'settings'
    
    def _go_to_cleaning(self, instance):
        """Va à l'écran de nettoyage"""
        print("🧼 Ouverture du nettoyage")
        if self.manager:
            self.manager.transition.direction = 'down'
            self.manager.current = 'cleaning'
    
    def on_enter(self):
        """Appelé quand l'écran devient actif"""
        print("📱 Menu principal affiché")
        
        # Réactiver animations si nécessaire
        pass
    
    def on_leave(self):
        """Appelé quand on quitte l'écran"""
        print("📱 Sortie du menu principal")