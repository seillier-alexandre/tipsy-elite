"""
═══════════════════════════════════════════════════════════════
SUPPORT ÉCRAN ROND 4" - RASPBERRY PI
Gestion du masque circulaire et des zones de sécurité
═══════════════════════════════════════════════════════════════
"""

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.graphics import Ellipse, Color, Line, PushMatrix, PopMatrix, Rotate
from kivy.graphics.instructions import InstructionGroup
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.clock import Clock
import math


class CircularMask(Widget):
    """Applique un masque circulaire sur l'écran entier"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(size=self._update_mask, pos=self._update_mask)
    
    def _update_mask(self, *args):
        self.canvas.clear()
        if self.size[0] > 0 and self.size[1] > 0:
            diameter = min(self.size)
            with self.canvas:
                Color(0.04, 0.04, 0.04, 1)  # Noir pour cacher les bords
                # Rectangles pour masquer les coins
                from kivy.graphics import Rectangle
                
                # Haut
                Rectangle(pos=(0, diameter), size=(self.width, self.height - diameter))
                # Bas  
                Rectangle(pos=(0, 0), size=(self.width, self.height - diameter))
                # Gauche
                Rectangle(pos=(0, 0), size=(self.width - diameter, self.height))
                # Droite
                Rectangle(pos=(diameter, 0), size=(self.width - diameter, self.height))


class CircleLayout(FloatLayout):
    """Layout qui centre tous les éléments dans un cercle"""
    
    def __init__(self, safe_margin=0.1, **kwargs):
        super().__init__(**kwargs)
        self.safe_margin = safe_margin  # Marge de sécurité (10% du rayon)
        self.circle_radius = 0
        self.bind(size=self._update_circle_bounds)
    
    def _update_circle_bounds(self, *args):
        """Met à jour les dimensions du cercle utilisable"""
        if self.size[0] > 0 and self.size[1] > 0:
            diameter = min(self.size)
            self.circle_radius = (diameter / 2) * (1 - self.safe_margin)
    
    def add_widget(self, widget, **kwargs):
        """Ajoute un widget en s'assurant qu'il reste dans le cercle"""
        super().add_widget(widget, **kwargs)
        self._constrain_to_circle(widget)
    
    def _constrain_to_circle(self, widget):
        """Contraint un widget à rester dans les limites du cercle"""
        if hasattr(widget, 'size_hint') and widget.size_hint != (None, None):
            return  # Les widgets avec size_hint sont gérés automatiquement
        
        def update_position(*args):
            if self.circle_radius <= 0:
                return
            
            center_x = self.center_x
            center_y = self.center_y
            
            # Distance du centre
            widget_center_x = widget.center_x
            widget_center_y = widget.center_y
            distance = math.sqrt((widget_center_x - center_x)**2 + (widget_center_y - center_y)**2)
            
            # Si le widget dépasse, le ramener dans le cercle
            max_distance = self.circle_radius - max(widget.width, widget.height) / 2
            if distance > max_distance and max_distance > 0:
                ratio = max_distance / distance
                widget.center_x = center_x + (widget_center_x - center_x) * ratio
                widget.center_y = center_y + (widget_center_y - center_y) * ratio
        
        widget.bind(pos=update_position, size=update_position)
        self.bind(pos=update_position, size=update_position)


class RoundScreen(CircleLayout):
    """Écran de base pour interface circulaire avec animations Art Déco"""
    
    def __init__(self, **kwargs):
        super().__init__(safe_margin=0.15, **kwargs)
        self._setup_background()
        self._setup_animations()
    
    def _setup_background(self):
        """Configure le fond Art Déco"""
        with self.canvas.before:
            # Fond noir profond
            Color(0.04, 0.04, 0.04, 1)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
            
            # Cercle de base doré
            Color(0.83, 0.69, 0.22, 0.3)
            diameter = min(self.size) if self.size[0] > 0 else 400
            self.circle = Ellipse(
                pos=(self.center_x - diameter/2, self.center_y - diameter/2),
                size=(diameter, diameter)
            )
        
        self.bind(size=self._update_background, pos=self._update_background)
    
    def _update_background(self, *args):
        """Met à jour le fond quand la taille change"""
        if hasattr(self, 'bg_rect'):
            self.bg_rect.pos = self.pos
            self.bg_rect.size = self.size
        
        if hasattr(self, 'circle') and self.size[0] > 0:
            diameter = min(self.size) * 0.95
            self.circle.pos = (self.center_x - diameter/2, self.center_y - diameter/2)
            self.circle.size = (diameter, diameter)
    
    def _setup_animations(self):
        """Configure les animations de fond"""
        self.animation_angle = 0
        Clock.schedule_interval(self._animate_background, 1/30.0)
    
    def _animate_background(self, dt):
        """Animation subtile de rotation"""
        self.animation_angle += 0.5
        if self.animation_angle >= 360:
            self.animation_angle = 0


class TouchCircleDetector:
    """Détecte si un touch est dans la zone circulaire"""
    
    @staticmethod
    def is_touch_in_circle(touch, widget):
        """Retourne True si le touch est dans le cercle de l'widget"""
        if not widget.size[0] or not widget.size[1]:
            return True
        
        diameter = min(widget.size)
        radius = diameter / 2
        center_x = widget.center_x
        center_y = widget.center_y
        
        distance = math.sqrt((touch.x - center_x)**2 + (touch.y - center_y)**2)
        return distance <= radius


class DecoTransition:
    """Transitions Art Déco entre écrans"""
    
    @staticmethod
    def fade_in_gold(widget, duration=0.5):
        """Transition d'entrée dorée"""
        widget.opacity = 0
        anim = Animation(opacity=1, duration=duration)
        anim.start(widget)
    
    @staticmethod
    def slide_from_center(widget, duration=0.8):
        """Glissement depuis le centre avec effet Art Déco"""
        original_pos = widget.pos
        widget.pos = widget.parent.center_x - widget.width/2, widget.parent.center_y - widget.height/2
        widget.opacity = 0
        
        anim = Animation(pos=original_pos, opacity=1, duration=duration, t='out_expo')
        anim.start(widget)
    
    @staticmethod
    def sunburst_reveal(widget, duration=1.0):
        """Révélation en rayons dorés"""
        widget.opacity = 0
        widget.scale = 0.5
        
        anim = Animation(opacity=1, scale=1, duration=duration, t='out_elastic')
        anim.start(widget)


# Configuration globale pour écran rond
ROUND_SCREEN_CONFIG = {
    'resolution': (480, 480),  # Écran rond 4"
    'safe_area_margin': 0.15,
    'animation_fps': 30,
    'touch_sensitivity': 0.95
}