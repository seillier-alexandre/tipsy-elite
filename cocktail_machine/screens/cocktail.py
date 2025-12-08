#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════
ÉCRAN DÉTAIL COCKTAIL - INTERFACE ART DÉCO KIVY
Affichage détaillé d'un cocktail et préparation
Design sophistiqué années 1920 pour écran rond 4"
═══════════════════════════════════════════════════════════════
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.progressbar import ProgressBar
from kivy.uix.popup import Popup
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import dp
import asyncio
import threading

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

class IngredientItem(BoxLayout):
    """Item d'ingrédient avec style Art Déco"""
    
    def __init__(self, ingredient_data, **kwargs):
        super().__init__(orientation='horizontal', **kwargs)
        self.ingredient_data = ingredient_data
        self.size_hint_y = None
        self.height = dp(40)
        
        # Nom de l'ingrédient
        name_label = Label(
            text=ingredient_data.get('name', 'Ingrédient'),
            size_hint_x=0.6,
            color=(0.97, 0.96, 0.91, 1),  # Crème
            halign='left',
            text_size=(dp(120), None)
        )
        
        # Quantité
        amount_label = Label(
            text=f"{ingredient_data.get('amount_ml', 0):.0f}ml",
            size_hint_x=0.25,
            color=(0.83, 0.69, 0.22, 1),  # Doré
            halign='center',
            bold=True
        )
        
        # Statut disponibilité
        status_icon = "✅" if ingredient_data.get('is_available', False) else "❌"
        status_label = Label(
            text=status_icon,
            size_hint_x=0.15,
            halign='center'
        )
        
        self.add_widget(name_label)
        self.add_widget(amount_label)
        self.add_widget(status_label)
        
        # Style Art Déco
        self._setup_deco_style()
    
    def _setup_deco_style(self):
        """Style Art Déco pour l'item"""
        with self.canvas.before:
            from kivy.graphics import Color, Line
            
            # Ligne décorative dorée en bas
            Color(0.83, 0.69, 0.22, 0.3)
            self.deco_line = Line(
                points=[self.x + 10, self.y + 5, self.right - 10, self.y + 5],
                width=1
            )
        
        self.bind(pos=self._update_line)
    
    def _update_line(self, *args):
        """Met à jour la ligne décorative"""
        if hasattr(self, 'deco_line'):
            self.deco_line.points = [self.x + 10, self.y + 5, self.right - 10, self.y + 5]

class PreparationProgress(BoxLayout):
    """Widget de progression de préparation avec style Art Déco"""
    
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.size_hint_y = None
        self.height = dp(100)
        
        # Titre
        self.status_label = Label(
            text='Prêt à préparer',
            size_hint_y=0.4,
            color=(0.83, 0.69, 0.22, 1),
            font_size='16sp',
            bold=True,
            halign='center'
        )
        
        # Barre de progression
        self.progress_bar = ProgressBar(
            max=100,
            value=0,
            size_hint_y=0.3
        )
        
        # Étape actuelle
        self.step_label = Label(
            text='',
            size_hint_y=0.3,
            color=(0.97, 0.96, 0.91, 0.8),
            font_size='12sp',
            halign='center'
        )
        
        self.add_widget(self.status_label)
        self.add_widget(self.progress_bar)
        self.add_widget(self.step_label)
        
        # Style de la barre
        self._setup_progress_style()
    
    def _setup_progress_style(self):
        """Style Art Déco pour la barre de progression"""
        with self.progress_bar.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            
            # Fond de la barre
            Color(0.04, 0.04, 0.04, 0.8)
            self.bg_rect = RoundedRectangle(
                pos=self.progress_bar.pos,
                size=self.progress_bar.size,
                radius=[5]
            )
        
        self.progress_bar.bind(pos=self._update_bg, size=self._update_bg)
    
    def _update_bg(self, *args):
        """Met à jour le fond de la barre"""
        if hasattr(self, 'bg_rect'):
            self.bg_rect.pos = self.progress_bar.pos
            self.bg_rect.size = self.progress_bar.size
    
    def update_progress(self, step_name, progress):
        """Met à jour la progression"""
        self.status_label.text = f"Préparation en cours..."
        self.step_label.text = step_name
        self.progress_bar.value = progress
        
        # Animation de la barre
        if progress > 0:
            anim = Animation(value=progress, duration=0.3)
            anim.start(self.progress_bar)
    
    def set_completed(self):
        """Marque comme terminé"""
        self.status_label.text = "🍸 Cocktail prêt !"
        self.step_label.text = "Dégustez avec modération"
        self.progress_bar.value = 100
        
        # Animation de success
        anim = Animation(color=(0, 1, 0, 1), duration=0.5) + Animation(color=(0.83, 0.69, 0.22, 1), duration=0.5)
        anim.start(self.status_label)
    
    def set_error(self, error_msg):
        """Marque comme erreur"""
        self.status_label.text = "❌ Erreur"
        self.status_label.color = (1, 0, 0, 1)
        self.step_label.text = error_msg
        self.progress_bar.value = 0

class CocktailScreen(RoundScreen):
    """Écran détail cocktail avec préparation"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'cocktail'
        self.cocktail_data = None
        self.cocktail_recipe = None
        self.is_preparing = False
        
        # Interface sera construite lors de set_cocktail
        self.main_layout = None
        
    def set_cocktail(self, cocktail_data):
        """Configure l'écran pour un cocktail spécifique"""
        self.cocktail_data = cocktail_data
        self.is_preparing = False
        
        # Charger la recette complète si possible
        self._load_full_recipe()
        
        # Reconstruire l'interface
        self._build_interface()
        
        print(f"🍸 Affichage cocktail: {cocktail_data.get('name', 'Inconnu')}")
    
    def _load_full_recipe(self):
        """Charge la recette complète depuis le gestionnaire"""
        if COCKTAIL_SUPPORT and self.cocktail_data:
            try:
                manager = get_cocktail_manager()
                cocktail_id = self.cocktail_data.get('id')
                self.cocktail_recipe = manager.database.get_cocktail(cocktail_id)
                
                if self.cocktail_recipe:
                    print(f"✅ Recette complète chargée: {self.cocktail_recipe.name}")
                else:
                    print(f"❌ Recette non trouvée pour: {cocktail_id}")
                    
            except Exception as e:
                print(f"❌ Erreur chargement recette: {e}")
                self.cocktail_recipe = None
    
    def _build_interface(self):
        """Construit l'interface pour ce cocktail"""
        if not self.cocktail_data:
            return
        
        # Nettoyer l'écran
        self.clear_widgets()
        
        self.main_layout = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(15))
        
        # En-tête avec image et nom
        self._build_header()
        
        # Ingrédients
        self._build_ingredients_section()
        
        # Progression de préparation
        self._build_progress_section()
        
        # Boutons d'action
        self._build_action_buttons()
        
        self.add_widget(self.main_layout)
        
        # Animation d'entrée
        DecoTransition.sunburst_reveal(self.main_layout, 1.0)
    
    def _build_header(self):
        """Construit l'en-tête avec image et infos"""
        header_layout = BoxLayout(orientation='horizontal', size_hint_y=0.3)
        
        # Image du cocktail
        cocktail_image = Image(
            source='assets/images/cocktails/default.png',
            size_hint_x=0.4,
            allow_stretch=True,
            keep_ratio=True
        )
        
        # Informations
        info_layout = BoxLayout(orientation='vertical', size_hint_x=0.6, padding=(dp(10), 0))
        
        # Nom
        name_label = Label(
            text=self.cocktail_data.get('name', 'Cocktail'),
            color=(0.83, 0.69, 0.22, 1),  # Doré
            font_size='18sp',
            bold=True,
            size_hint_y=0.4,
            halign='left',
            text_size=(dp(150), None)
        )
        
        # Description
        description = self.cocktail_data.get('description', 'Délicieux cocktail artisanal')
        desc_label = Label(
            text=description,
            color=(0.97, 0.96, 0.91, 0.8),
            font_size='11sp',
            size_hint_y=0.4,
            halign='left',
            text_size=(dp(150), None),
            text_size_hint=(1, None)
        )
        
        # Métadonnées
        difficulty = self.cocktail_data.get('difficulty', 1)
        time_prep = self.cocktail_data.get('preparation_time', 60)
        meta_text = f"Difficulté: {'⭐' * difficulty} • Temps: {time_prep}s"
        
        meta_label = Label(
            text=meta_text,
            color=(0.83, 0.69, 0.22, 0.8),
            font_size='10sp',
            size_hint_y=0.2,
            halign='left',
            text_size=(dp(150), None)
        )
        
        info_layout.add_widget(name_label)
        info_layout.add_widget(desc_label)
        info_layout.add_widget(meta_label)
        
        header_layout.add_widget(cocktail_image)
        header_layout.add_widget(info_layout)
        
        self.main_layout.add_widget(header_layout)
    
    def _build_ingredients_section(self):
        """Construit la section des ingrédients"""
        # Titre ingrédients
        ingredients_title = Label(
            text='INGRÉDIENTS',
            color=(0.83, 0.69, 0.22, 1),
            font_size='14sp',
            bold=True,
            size_hint_y=None,
            height=dp(30),
            halign='center'
        )
        self.main_layout.add_widget(ingredients_title)
        
        # Liste des ingrédients
        ingredients_layout = BoxLayout(orientation='vertical', size_hint_y=0.25)
        
        if self.cocktail_recipe and self.cocktail_recipe.ingredients:
            # Utiliser les vrais ingrédients
            for ingredient in self.cocktail_recipe.ingredients:
                if ingredient.category != "garnish":  # Exclure garnitures
                    ing_data = {
                        'name': ingredient.name,
                        'amount_ml': ingredient.amount_ml,
                        'is_available': ingredient.is_available
                    }
                    ing_item = IngredientItem(ing_data)
                    ingredients_layout.add_widget(ing_item)
        else:
            # Ingrédients démo
            demo_ingredients = [
                {'name': 'Base alcoolisée', 'amount_ml': 50, 'is_available': True},
                {'name': 'Mixer/Jus', 'amount_ml': 100, 'is_available': True},
                {'name': 'Sirop (optionnel)', 'amount_ml': 10, 'is_available': False}
            ]
            
            for ing_data in demo_ingredients:
                ing_item = IngredientItem(ing_data)
                ingredients_layout.add_widget(ing_item)
        
        self.main_layout.add_widget(ingredients_layout)
    
    def _build_progress_section(self):
        """Construit la section de progression"""
        self.progress_widget = PreparationProgress()
        self.main_layout.add_widget(self.progress_widget)
    
    def _build_action_buttons(self):
        """Construit les boutons d'action"""
        buttons_layout = BoxLayout(
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
        
        # Bouton Principal (Préparer ou Arrêter)
        self.main_action_btn = Button(
            text='🍸 PRÉPARER',
            size_hint_x=0.5
        )
        self.main_action_btn.bind(on_press=self._on_main_action)
        
        # Bouton Options
        options_btn = Button(
            text='⚙️ OPTIONS',
            size_hint_x=0.2
        )
        options_btn.bind(on_press=self._show_options)
        
        buttons_layout.add_widget(back_btn)
        buttons_layout.add_widget(self.main_action_btn)
        buttons_layout.add_widget(options_btn)
        
        self.main_layout.add_widget(buttons_layout)
    
    def _go_back(self, instance):
        """Retourne au menu"""
        print("⬅️ Retour au menu")
        if self.manager:
            self.manager.transition.direction = 'right'
            self.manager.current = 'menu'
    
    def _on_main_action(self, instance):
        """Action principale (préparer/arrêter)"""
        if self.is_preparing:
            self._stop_preparation()
        else:
            self._start_preparation()
    
    def _start_preparation(self):
        """Démarre la préparation du cocktail"""
        if not self.cocktail_data:
            return
        
        # Vérifier disponibilité des ingrédients
        if self.cocktail_recipe and not self.cocktail_recipe.is_makeable:
            self._show_error_popup("Ingrédients manquants", 
                                 f"Ingrédients non disponibles: {', '.join(self.cocktail_recipe.missing_ingredients)}")
            return
        
        self.is_preparing = True
        self.main_action_btn.text = "🛑 ARRÊTER"
        self.main_action_btn.background_color = (1, 0.3, 0.3, 1)
        
        print(f"🚀 Début préparation: {self.cocktail_data['name']}")
        
        # Lancer la préparation en arrière-plan
        if COCKTAIL_SUPPORT and self.cocktail_recipe:
            thread = threading.Thread(target=self._prepare_cocktail_async)
            thread.daemon = True
            thread.start()
        else:
            # Mode démo
            self._demo_preparation()
    
    def _prepare_cocktail_async(self):
        """Prépare le cocktail de façon asynchrone"""
        try:
            # Créer une nouvelle boucle événements pour ce thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Callback pour mettre à jour l'UI
            def progress_callback(step, progress):
                Clock.schedule_once(lambda dt: self._update_progress(step, progress), 0)
            
            # Préparer le cocktail
            manager = get_cocktail_manager()
            manager.maker.set_progress_callback(progress_callback)
            
            # Lancer préparation
            success = loop.run_until_complete(
                manager.maker.prepare_cocktail(self.cocktail_recipe.id)
            )
            
            # Finaliser
            Clock.schedule_once(
                lambda dt: self._preparation_finished(success), 0
            )
            
        except Exception as e:
            print(f"❌ Erreur préparation: {e}")
            Clock.schedule_once(
                lambda dt: self._preparation_error(str(e)), 0
            )
        finally:
            if 'loop' in locals():
                loop.close()
    
    def _demo_preparation(self):
        """Simulation de préparation pour démo"""
        steps = [
            ("Vérification du système", 10),
            ("Préparation des pompes", 25),
            ("Versement gin", 50),
            ("Versement tonic", 75),
            ("Mélange final", 90),
            ("Finalisation", 100)
        ]
        
        def run_demo_step(step_index):
            if step_index < len(steps) and self.is_preparing:
                step_name, progress = steps[step_index]
                self._update_progress(step_name, progress)
                
                if step_index < len(steps) - 1:
                    Clock.schedule_once(lambda dt: run_demo_step(step_index + 1), 1.5)
                else:
                    Clock.schedule_once(lambda dt: self._preparation_finished(True), 1.0)
        
        Clock.schedule_once(lambda dt: run_demo_step(0), 0.5)
    
    def _update_progress(self, step_name, progress):
        """Met à jour la progression dans l'UI"""
        if self.progress_widget:
            self.progress_widget.update_progress(step_name, progress)
    
    def _preparation_finished(self, success):
        """Finalise la préparation"""
        self.is_preparing = False
        self.main_action_btn.text = "🍸 PRÉPARER"
        self.main_action_btn.background_color = (1, 1, 1, 1)
        
        if success:
            self.progress_widget.set_completed()
            print("✅ Cocktail préparé avec succès!")
        else:
            self.progress_widget.set_error("Erreur pendant la préparation")
            print("❌ Échec de la préparation")
    
    def _preparation_error(self, error_msg):
        """Gère une erreur de préparation"""
        self.is_preparing = False
        self.main_action_btn.text = "🍸 PRÉPARER"
        self.main_action_btn.background_color = (1, 1, 1, 1)
        self.progress_widget.set_error(error_msg)
    
    def _stop_preparation(self):
        """Arrête la préparation"""
        print("🛑 Arrêt de la préparation")
        self.is_preparing = False
        self.main_action_btn.text = "🍸 PRÉPARER"
        self.main_action_btn.background_color = (1, 1, 1, 1)
        
        # Arrêter le système de cocktails si disponible
        if COCKTAIL_SUPPORT:
            try:
                manager = get_cocktail_manager()
                manager.maker.stop_preparation()
            except Exception as e:
                print(f"Erreur arrêt préparation: {e}")
        
        self.progress_widget.set_error("Préparation interrompue")
    
    def _show_options(self, instance):
        """Affiche les options (doses, etc.)"""
        content = BoxLayout(orientation='vertical', spacing=dp(10))
        
        content.add_widget(Label(text='Options de préparation', font_size='16sp', size_hint_y=0.3))
        
        # Boutons de dose
        dose_layout = BoxLayout(orientation='horizontal', size_hint_y=0.4)
        
        simple_btn = Button(text='Dose Simple')
        double_btn = Button(text='Dose Double')
        
        dose_layout.add_widget(simple_btn)
        dose_layout.add_widget(double_btn)
        
        content.add_widget(dose_layout)
        
        # Bouton fermer
        close_btn = Button(text='Fermer', size_hint_y=0.3)
        content.add_widget(close_btn)
        
        popup = Popup(
            title='Options',
            content=content,
            size_hint=(0.8, 0.6)
        )
        
        close_btn.bind(on_press=popup.dismiss)
        popup.open()
    
    def _show_error_popup(self, title, message):
        """Affiche une popup d'erreur"""
        content = BoxLayout(orientation='vertical', spacing=dp(10))
        
        content.add_widget(Label(text=message, text_size=(dp(200), None)))
        
        close_btn = Button(text='OK', size_hint_y=0.3)
        content.add_widget(close_btn)
        
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.8, 0.5)
        )
        
        close_btn.bind(on_press=popup.dismiss)
        popup.open()