# -*- coding: utf-8 -*-
"""
Interface Art Déco années 1920 pour machine à cocktails
Design sophistiqué pour écran tactile rond - Style Al Capone Prohibition
Animation fluide et expérience utilisateur premium
"""
import pygame
import math
import time
import json
import logging
from typing import List, Dict, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
import threading
from hardware_config import SCREEN_CONFIG

logger = logging.getLogger(__name__)

# Initialisation Pygame sera faite dans initialize()
# pygame.init() - Déplacé dans la méthode initialize()
# pygame.mixer.init() - Déplacé dans la méthode initialize()

# Configuration écran rond
SCREEN_WIDTH = SCREEN_CONFIG['width']
SCREEN_HEIGHT = SCREEN_CONFIG['height'] 
CENTER_X = SCREEN_CONFIG['center_x']
CENTER_Y = SCREEN_CONFIG['center_y']
SCREEN_RADIUS = SCREEN_CONFIG['radius']

# Palette couleurs Art Déco sophistiquée
class Colors:
    # Couleurs principales années 1920
    CREAM = (245, 235, 215)          # Crème vintage
    DEEP_BLACK = (15, 15, 15)        # Noir profond
    PURE_BLACK = (0, 0, 0)           # Noir pur
    
    # Ors et métaux
    GOLD = (212, 175, 55)            # Or Art Déco
    CHAMPAGNE_GOLD = (247, 231, 206) # Or champagne
    DARK_GOLD = (184, 134, 11)       # Or foncé
    BRONZE = (176, 141, 87)          # Bronze
    
    # Rouges prohibition
    BURGUNDY = (128, 0, 32)          # Bordeaux prohibition
    DARK_BURGUNDY = (80, 0, 20)      # Bordeaux foncé
    CRIMSON = (153, 0, 0)            # Rouge crimson
    
    # Métaux
    SILVER = (192, 192, 192)         # Argent métallique
    DARK_SILVER = (128, 128, 128)    # Argent foncé
    PLATINUM = (229, 228, 226)       # Platine
    
    # Couleurs spécialisées
    WHISKEY_AMBER = (191, 108, 10)   # Ambre whiskey
    EMERALD = (0, 100, 50)           # Vert émeraude
    CHARCOAL = (36, 36, 36)          # Gris charbon
    IVORY = (255, 255, 240)          # Ivoire
    
    # Couleurs d'état
    SUCCESS_GREEN = (46, 139, 87)    # Vert succès
    WARNING_ORANGE = (255, 165, 0)   # Orange avertissement
    ERROR_RED = (220, 20, 60)        # Rouge erreur
    INFO_BLUE = (70, 130, 180)       # Bleu info

class Fonts:
    """Gestionnaire des polices Art Déco"""
    
    def __init__(self):
        self.fonts = {}
        self._load_fonts()
    
    def _load_fonts(self):
        """Charge les polices avec fallbacks"""
        # Polices Art Déco par ordre de préférence
        art_deco_fonts = [
            'Times New Roman', 'Georgia', 'Garamond', 'serif'
        ]
        
        modern_fonts = [
            'Arial', 'Helvetica', 'sans-serif'
        ]
        
        # Tailles et styles
        font_configs = {
            'title_huge': (72, True),
            'title_large': (56, True),
            'title': (42, True),
            'subtitle': (32, True),
            'large': (28, False),
            'medium': (22, False),
            'small': (18, False),
            'tiny': (14, False),
            'micro': (12, False)
        }
        
        for font_name, (size, bold) in font_configs.items():
            font = None
            
            # Essayer les polices Art Déco d'abord
            for font_family in art_deco_fonts:
                try:
                    font = pygame.font.SysFont(font_family, size, bold=bold)
                    if font:
                        break
                except:
                    continue
            
            # Fallback vers polices modernes
            if not font:
                for font_family in modern_fonts:
                    try:
                        font = pygame.font.SysFont(font_family, size, bold=bold)
                        if font:
                            break
                    except:
                        continue
            
            # Fallback final vers police par défaut
            if not font:
                font = pygame.font.SysFont(None, size)
            
            self.fonts[font_name] = font
    
    def get(self, size_name: str) -> pygame.font.Font:
        """Récupère une police par nom"""
        return self.fonts.get(size_name, self.fonts['medium'])

class AnimationType(Enum):
    """Types d'animation disponibles"""
    FADE_IN = "fade_in"
    FADE_OUT = "fade_out" 
    SLIDE_IN = "slide_in"
    SLIDE_OUT = "slide_out"
    SCALE_IN = "scale_in"
    SCALE_OUT = "scale_out"
    ROTATE = "rotate"
    PULSE = "pulse"
    GLOW = "glow"

@dataclass
class Animation:
    """Configuration d'animation"""
    type: AnimationType
    duration: float
    start_time: float
    start_value: float = 0.0
    end_value: float = 1.0
    easing_function: Optional[Callable[[float], float]] = None
    
    @property
    def progress(self) -> float:
        """Progression de l'animation (0.0 à 1.0)"""
        elapsed = time.time() - self.start_time
        return min(1.0, elapsed / self.duration)
    
    @property
    def is_complete(self) -> bool:
        """L'animation est-elle terminée"""
        return self.progress >= 1.0
    
    def get_value(self) -> float:
        """Valeur interpolée de l'animation"""
        p = self.progress
        if self.easing_function:
            p = self.easing_function(p)
        
        return self.start_value + (self.end_value - self.start_value) * p

class EasingFunctions:
    """Fonctions d'interpolation pour animations fluides"""
    
    @staticmethod
    def ease_in_cubic(t: float) -> float:
        return t * t * t
    
    @staticmethod
    def ease_out_cubic(t: float) -> float:
        return 1 - pow(1 - t, 3)
    
    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        if t < 0.5:
            return 4 * t * t * t
        return 1 - pow(-2 * t + 2, 3) / 2
    
    @staticmethod
    def ease_in_elastic(t: float) -> float:
        c4 = (2 * math.pi) / 3
        if t == 0 or t == 1:
            return t
        return -pow(2, 10 * t - 10) * math.sin((t * 10 - 10.75) * c4)
    
    @staticmethod
    def ease_out_bounce(t: float) -> float:
        n1 = 7.5625
        d1 = 2.75
        
        if t < 1 / d1:
            return n1 * t * t
        elif t < 2 / d1:
            return n1 * (t := t - 1.5 / d1) * t + 0.75
        elif t < 2.5 / d1:
            return n1 * (t := t - 2.25 / d1) * t + 0.9375
        else:
            return n1 * (t := t - 2.625 / d1) * t + 0.984375

class ArtDecoElement:
    """Élément de base de l'interface Art Déco"""
    
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.visible = True
        self.animations: List[Animation] = []
        self._alpha = 255
        
    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    def add_animation(self, animation: Animation):
        """Ajoute une animation à l'élément"""
        self.animations.append(animation)
    
    def update_animations(self):
        """Met à jour toutes les animations"""
        self.animations = [anim for anim in self.animations if not anim.is_complete]
    
    def draw(self, surface: pygame.Surface):
        """Méthode de rendu à surcharger"""
        pass
    
    def is_point_inside_circle(self, point: Tuple[int, int]) -> bool:
        """Vérifie si un point est dans le cercle de l'écran"""
        px, py = point
        distance = math.sqrt((px - CENTER_X) ** 2 + (py - CENTER_Y) ** 2)
        return distance <= SCREEN_RADIUS

class ArtDecoButton(ArtDecoElement):
    """Bouton Art Déco avec animations et effets visuels"""
    
    def __init__(self, x: int, y: int, width: int, height: int, text: str, 
                 callback: Optional[Callable] = None):
        super().__init__(x, y, width, height)
        self.text = text
        self.callback = callback
        self.is_pressed = False
        self.is_hovered = False
        self.base_color = Colors.GOLD
        self.hover_color = Colors.CHAMPAGNE_GOLD
        self.press_color = Colors.DARK_GOLD
        self.text_color = Colors.DEEP_BLACK
        
    def draw(self, surface: pygame.Surface, fonts: Fonts):
        """Dessine le bouton avec style Art Déco"""
        # Déterminer la couleur selon l'état
        if self.is_pressed:
            color = self.press_color
        elif self.is_hovered:
            color = self.hover_color
        else:
            color = self.base_color
        
        # Dessiner le cadre extérieur (biseauté)
        outer_rect = pygame.Rect(self.x - 3, self.y - 3, self.width + 6, self.height + 6)
        pygame.draw.rect(surface, Colors.CHARCOAL, outer_rect, 0, 8)
        
        # Dessiner le bouton principal
        main_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, color, main_rect, 0, 5)
        
        # Bordure intérieure
        pygame.draw.rect(surface, Colors.DARK_GOLD, main_rect, 2, 5)
        
        # Motifs Art Déco dans les coins
        self._draw_corner_ornaments(surface, main_rect)
        
        # Texte centré
        font = fonts.get('medium')
        text_surface = font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=main_rect.center)
        surface.blit(text_surface, text_rect)
        
        # Effet de brillance si survolé
        if self.is_hovered:
            self._draw_shine_effect(surface, main_rect)
    
    def _draw_corner_ornaments(self, surface: pygame.Surface, rect: pygame.Rect):
        """Dessine les ornements Art Déco dans les coins"""
        corner_size = 8
        
        # Coin supérieur gauche
        points = [
            (rect.x + 5, rect.y + 5),
            (rect.x + corner_size + 5, rect.y + 5),
            (rect.x + 5, rect.y + corner_size + 5)
        ]
        pygame.draw.polygon(surface, Colors.BRONZE, points)
        
        # Coin supérieur droit
        points = [
            (rect.x + rect.width - 5, rect.y + 5),
            (rect.x + rect.width - corner_size - 5, rect.y + 5),
            (rect.x + rect.width - 5, rect.y + corner_size + 5)
        ]
        pygame.draw.polygon(surface, Colors.BRONZE, points)
        
        # Coin inférieur gauche
        points = [
            (rect.x + 5, rect.y + rect.height - 5),
            (rect.x + corner_size + 5, rect.y + rect.height - 5),
            (rect.x + 5, rect.y + rect.height - corner_size - 5)
        ]
        pygame.draw.polygon(surface, Colors.BRONZE, points)
        
        # Coin inférieur droit
        points = [
            (rect.x + rect.width - 5, rect.y + rect.height - 5),
            (rect.x + rect.width - corner_size - 5, rect.y + rect.height - 5),
            (rect.x + rect.width - 5, rect.y + rect.height - corner_size - 5)
        ]
        pygame.draw.polygon(surface, Colors.BRONZE, points)
    
    def _draw_shine_effect(self, surface: pygame.Surface, rect: pygame.Rect):
        """Dessine un effet de brillance"""
        # Créer un dégradé de brillance
        shine_surface = pygame.Surface((rect.width, rect.height // 3), pygame.SRCALPHA)
        for i in range(rect.height // 3):
            alpha = int(50 * (1 - i / (rect.height // 3)))
            color = (*Colors.IVORY[:3], alpha)
            pygame.draw.line(shine_surface, color, (0, i), (rect.width, i))
        
        surface.blit(shine_surface, (rect.x, rect.y))
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Gère les événements tactiles"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos) and self.is_point_inside_circle(event.pos):
                self.is_pressed = True
                return True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.is_pressed and self.rect.collidepoint(event.pos) and self.is_point_inside_circle(event.pos):
                self.is_pressed = False
                if self.callback:
                    self.callback()
                return True
            self.is_pressed = False
        
        elif event.type == pygame.MOUSEMOTION:
            self.is_hovered = (self.rect.collidepoint(event.pos) and 
                              self.is_point_inside_circle(event.pos))
        
        return False

class CircularMenu(ArtDecoElement):
    """Menu circulaire Art Déco pour écran rond"""
    
    def __init__(self, center_x: int, center_y: int, radius: int, items: List[str]):
        super().__init__(center_x - radius, center_y - radius, radius * 2, radius * 2)
        self.center_x = center_x
        self.center_y = center_y
        self.radius = radius
        self.items = items
        self.selected_index = 0
        self.rotation_angle = 0
        self.target_rotation = 0
        self.is_rotating = False
        
    def draw(self, surface: pygame.Surface, fonts: Fonts):
        """Dessine le menu circulaire"""
        if not self.items:
            return
        
        # Fond du menu circulaire
        pygame.draw.circle(surface, Colors.CHARCOAL, (self.center_x, self.center_y), 
                          self.radius + 10, 5)
        pygame.draw.circle(surface, Colors.DEEP_BLACK, (self.center_x, self.center_y), self.radius)
        
        # Dessiner les éléments du menu
        item_count = len(self.items)
        angle_step = 2 * math.pi / item_count
        
        for i, item in enumerate(self.items):
            # Calculer la position
            angle = (i * angle_step) + self.rotation_angle
            item_radius = self.radius - 60
            x = self.center_x + math.cos(angle) * item_radius
            y = self.center_y + math.sin(angle) * item_radius
            
            # Déterminer si c'est l'élément sélectionné
            is_selected = i == self.selected_index
            
            # Couleurs selon l'état
            bg_color = Colors.GOLD if is_selected else Colors.SILVER
            text_color = Colors.DEEP_BLACK if is_selected else Colors.CREAM
            
            # Dessiner le cercle de l'élément
            item_size = 45 if is_selected else 35
            pygame.draw.circle(surface, bg_color, (int(x), int(y)), item_size)
            pygame.draw.circle(surface, Colors.BRONZE, (int(x), int(y)), item_size, 3)
            
            # Dessiner le texte
            font = fonts.get('small')
            text_surface = font.render(item, True, text_color)
            text_rect = text_surface.get_rect(center=(int(x), int(y)))
            surface.blit(text_surface, text_rect)
            
            # Effet de brillance pour l'élément sélectionné
            if is_selected:
                self._draw_selection_glow(surface, (int(x), int(y)), item_size)
    
    def _draw_selection_glow(self, surface: pygame.Surface, center: Tuple[int, int], radius: int):
        """Dessine un effet de brillance pour l'élément sélectionné"""
        glow_surface = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
        
        for r in range(radius, radius * 2, 2):
            alpha = int(30 * (1 - (r - radius) / radius))
            color = (*Colors.GOLD[:3], alpha)
            pygame.draw.circle(glow_surface, color, (radius * 2, radius * 2), r)
        
        surface.blit(glow_surface, (center[0] - radius * 2, center[1] - radius * 2))
    
    def rotate_to_item(self, index: int):
        """Fait tourner le menu vers un élément"""
        if 0 <= index < len(self.items):
            self.selected_index = index
            angle_step = 2 * math.pi / len(self.items)
            self.target_rotation = -index * angle_step
            self.is_rotating = True
    
    def update(self):
        """Met à jour les animations"""
        if self.is_rotating:
            # Interpolation fluide vers la rotation cible
            diff = self.target_rotation - self.rotation_angle
            if abs(diff) > 0.01:
                self.rotation_angle += diff * 0.1
            else:
                self.rotation_angle = self.target_rotation
                self.is_rotating = False

class CocktailCard(ArtDecoElement):
    """Carte de cocktail avec design Art Déco"""
    
    def __init__(self, x: int, y: int, width: int, height: int, cocktail_data: Dict):
        super().__init__(x, y, width, height)
        self.cocktail_data = cocktail_data
        self.scale = 1.0
        self.target_scale = 1.0
        self.glow_intensity = 0
        
    def draw(self, surface: pygame.Surface, fonts: Fonts):
        """Dessine la carte de cocktail"""
        # Calculer les dimensions avec mise à l'échelle
        scaled_width = int(self.width * self.scale)
        scaled_height = int(self.height * self.scale)
        scaled_x = self.x + (self.width - scaled_width) // 2
        scaled_y = self.y + (self.height - scaled_height) // 2
        
        # Fond de la carte
        card_rect = pygame.Rect(scaled_x, scaled_y, scaled_width, scaled_height)
        
        # Ombre portée
        shadow_rect = pygame.Rect(scaled_x + 5, scaled_y + 5, scaled_width, scaled_height)
        pygame.draw.rect(surface, Colors.CHARCOAL, shadow_rect, 0, 10)
        
        # Fond principal
        pygame.draw.rect(surface, Colors.CREAM, card_rect, 0, 10)
        pygame.draw.rect(surface, Colors.GOLD, card_rect, 3, 10)
        
        # Bordures décoratives
        self._draw_decorative_borders(surface, card_rect)
        
        # Titre du cocktail
        font_title = fonts.get('subtitle')
        title = self.cocktail_data.get('name', 'Cocktail')
        title_surface = font_title.render(title, True, Colors.DEEP_BLACK)
        title_rect = title_surface.get_rect(centerx=card_rect.centerx, 
                                          y=card_rect.y + 20)
        surface.blit(title_surface, title_rect)
        
        # Séparateur décoratif
        sep_y = title_rect.bottom + 10
        self._draw_decorative_separator(surface, card_rect.centerx, sep_y)
        
        # Liste des ingrédients
        font_ingredient = fonts.get('small')
        ingredients = self.cocktail_data.get('ingredients', [])
        y_offset = sep_y + 30
        
        for ingredient in ingredients[:6]:  # Maximum 6 ingrédients visibles
            ing_text = f"• {ingredient.get('name', '')} ({ingredient.get('amount', '')})"
            ing_surface = font_ingredient.render(ing_text, True, Colors.CHARCOAL)
            ing_rect = ing_surface.get_rect(x=card_rect.x + 20, y=y_offset)
            surface.blit(ing_surface, ing_rect)
            y_offset += 25
        
        # Effet de brillance
        if self.glow_intensity > 0:
            self._draw_glow_effect(surface, card_rect)
    
    def _draw_decorative_borders(self, surface: pygame.Surface, rect: pygame.Rect):
        """Dessine les bordures décoratives Art Déco"""
        # Coins ornementaux
        corner_size = 15
        
        # Motifs géométriques dans les coins
        for corner in ['tl', 'tr', 'bl', 'br']:
            self._draw_corner_pattern(surface, rect, corner, corner_size)
    
    def _draw_corner_pattern(self, surface: pygame.Surface, rect: pygame.Rect, 
                           corner: str, size: int):
        """Dessine un motif dans un coin spécifique"""
        if corner == 'tl':  # Top-left
            base_x, base_y = rect.x + 10, rect.y + 10
            points = [
                (base_x, base_y + size),
                (base_x + size//2, base_y),
                (base_x + size, base_y + size//2),
                (base_x + size//2, base_y + size),
                (base_x, base_y + size//2)
            ]
        elif corner == 'tr':  # Top-right
            base_x, base_y = rect.x + rect.width - 10 - size, rect.y + 10
            points = [
                (base_x, base_y + size//2),
                (base_x + size//2, base_y),
                (base_x + size, base_y + size),
                (base_x + size//2, base_y + size),
                (base_x + size, base_y + size//2)
            ]
        elif corner == 'bl':  # Bottom-left
            base_x, base_y = rect.x + 10, rect.y + rect.height - 10 - size
            points = [
                (base_x, base_y + size//2),
                (base_x + size//2, base_y + size),
                (base_x + size, base_y + size//2),
                (base_x + size//2, base_y),
                (base_x, base_y)
            ]
        else:  # Bottom-right
            base_x, base_y = rect.x + rect.width - 10 - size, rect.y + rect.height - 10 - size
            points = [
                (base_x + size, base_y),
                (base_x + size//2, base_y + size),
                (base_x, base_y + size//2),
                (base_x + size//2, base_y),
                (base_x + size, base_y + size//2)
            ]
        
        pygame.draw.polygon(surface, Colors.BRONZE, points)
    
    def _draw_decorative_separator(self, surface: pygame.Surface, center_x: int, y: int):
        """Dessine un séparateur décoratif"""
        # Ligne principale
        pygame.draw.line(surface, Colors.GOLD, 
                        (center_x - 60, y), (center_x + 60, y), 2)
        
        # Losange central
        diamond_size = 6
        points = [
            (center_x, y - diamond_size),
            (center_x + diamond_size, y),
            (center_x, y + diamond_size),
            (center_x - diamond_size, y)
        ]
        pygame.draw.polygon(surface, Colors.GOLD, points)
        
        # Petits cercles aux extrémités
        pygame.draw.circle(surface, Colors.BRONZE, (center_x - 65, y), 4)
        pygame.draw.circle(surface, Colors.BRONZE, (center_x + 65, y), 4)
    
    def _draw_glow_effect(self, surface: pygame.Surface, rect: pygame.Rect):
        """Dessine un effet de brillance"""
        glow_surface = pygame.Surface((rect.width + 20, rect.height + 20), pygame.SRCALPHA)
        
        for i in range(10):
            alpha = int(self.glow_intensity * (10 - i) / 10)
            color = (*Colors.GOLD[:3], alpha)
            expanded_rect = pygame.Rect(10 - i, 10 - i, 
                                      rect.width + i * 2, rect.height + i * 2)
            pygame.draw.rect(glow_surface, color, expanded_rect, 2, 10)
        
        surface.blit(glow_surface, (rect.x - 10, rect.y - 10))
    
    def set_highlight(self, highlight: bool):
        """Active/désactive la mise en surbrillance"""
        self.target_scale = 1.05 if highlight else 1.0
        self.glow_intensity = 30 if highlight else 0
    
    def update(self):
        """Met à jour les animations"""
        # Animation de mise à l'échelle
        if abs(self.scale - self.target_scale) > 0.001:
            self.scale += (self.target_scale - self.scale) * 0.1

class ArtDecoInterface:
    """Interface principale Art Déco pour machine à cocktails"""
    
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 
                                            pygame.FULLSCREEN if SCREEN_CONFIG['fullscreen'] else 0)
        pygame.display.set_caption("Tipsy - Machine à Cocktails Élite")
        
        self.clock = pygame.time.Clock()
        self.fonts = Fonts()
        self.running = True
        
        # États de l'interface
        self.current_screen = "splash"
        self.transition_time = 0
        self.last_interaction = time.time()
        
        # Éléments UI
        self.elements: List[ArtDecoElement] = []
        self.buttons: List[ArtDecoButton] = []
        
        # Données
        self.cocktails = []
        self.selected_cocktail = None
        
        # Thread pour animations
        self.animation_thread = None
        self.stop_animations = False
        
    def initialize(self):
        """Initialise l'interface"""
        logger.info("Initialisation interface Art Déco")
        
        # Initialiser pygame
        try:
            # Configuration pour fonctionner sans écran (headless)
            import os
            os.environ['SDL_VIDEODRIVER'] = 'dummy'
            pygame.init()
            pygame.mixer.init()
            logger.info("[OK] Pygame initialisé")
        except Exception as e:
            logger.error(f"[ERROR] Impossible d'initialiser Pygame: {e}")
            return False
        
        # Charger les données
        self.load_cocktails()
        
        # Créer les éléments UI
        self.create_ui_elements()
        
        # Démarrer le thread d'animation
        self.start_animation_thread()
        
        return True
    
    def load_cocktails(self):
        """Charge les cocktails depuis la configuration"""
        # Pour l'instant, cocktails d'exemple
        self.cocktails = [
            {
                "name": "Old Fashioned",
                "ingredients": [
                    {"name": "Whisky", "amount": "60ml"},
                    {"name": "Sirop simple", "amount": "10ml"},
                    {"name": "Bitters", "amount": "2 traits"}
                ],
                "description": "Cocktail classique de l'ère prohibition"
            },
            {
                "name": "Gin Fizz",
                "ingredients": [
                    {"name": "Gin", "amount": "45ml"},
                    {"name": "Jus de citron", "amount": "20ml"},
                    {"name": "Eau gazeuse", "amount": "Top"}
                ],
                "description": "Rafraîchissant et élégant"
            },
            {
                "name": "Sidecar",
                "ingredients": [
                    {"name": "Brandy", "amount": "50ml"},
                    {"name": "Triple Sec", "amount": "20ml"},
                    {"name": "Jus de citron", "amount": "15ml"}
                ],
                "description": "Sophistiqué et équilibré"
            }
        ]
    
    def create_ui_elements(self):
        """Crée les éléments de l'interface"""
        # Boutons principaux du menu
        button_width = 200
        button_height = 60
        
        # Menu principal
        self.main_menu_buttons = [
            ArtDecoButton(
                CENTER_X - button_width // 2,
                CENTER_Y - 120,
                button_width, button_height,
                "COCKTAILS",
                lambda: self.switch_screen("cocktail_menu")
            ),
            ArtDecoButton(
                CENTER_X - button_width // 2,
                CENTER_Y - 40,
                button_width, button_height,
                "NETTOYAGE",
                lambda: self.switch_screen("cleaning")
            ),
            ArtDecoButton(
                CENTER_X - button_width // 2,
                CENTER_Y + 40,
                button_width, button_height,
                "PARAMÈTRES",
                lambda: self.switch_screen("settings")
            )
        ]
    
    def draw_splash_screen(self):
        """Dessine l'écran de démarrage"""
        # Fond dégradé
        self.draw_background()
        
        # Masque circulaire
        self.draw_circular_mask()
        
        # Titre principal avec animation
        title_text = "TIPSY"
        subtitle_text = "MACHINE À COCKTAILS ÉLITE"
        tagline_text = "Style 1920 • Sophistication • Excellence"
        
        # Animation du titre
        alpha = min(255, int(255 * (time.time() - self.transition_time)))
        
        # Titre principal
        title_font = self.fonts.get('title_huge')
        title_surface = title_font.render(title_text, True, Colors.GOLD)
        title_surface.set_alpha(alpha)
        title_rect = title_surface.get_rect(center=(CENTER_X, CENTER_Y - 80))
        self.screen.blit(title_surface, title_rect)
        
        # Sous-titre
        subtitle_font = self.fonts.get('large')
        subtitle_surface = subtitle_font.render(subtitle_text, True, Colors.CREAM)
        subtitle_surface.set_alpha(alpha)
        subtitle_rect = subtitle_surface.get_rect(center=(CENTER_X, CENTER_Y - 20))
        self.screen.blit(subtitle_surface, subtitle_rect)
        
        # Tagline
        tagline_font = self.fonts.get('medium')
        tagline_surface = tagline_font.render(tagline_text, True, Colors.SILVER)
        tagline_surface.set_alpha(alpha)
        tagline_rect = tagline_surface.get_rect(center=(CENTER_X, CENTER_Y + 20))
        self.screen.blit(tagline_surface, tagline_rect)
        
        # Ornements Art Déco
        if alpha > 200:
            self.draw_art_deco_ornaments()
        
        # Auto-transition après 3 secondes
        if time.time() - self.transition_time > 3:
            self.switch_screen("main_menu")
    
    def draw_main_menu(self):
        """Dessine le menu principal"""
        self.draw_background()
        self.draw_circular_mask()
        
        # Titre du menu
        title_font = self.fonts.get('title')
        title_surface = title_font.render("MENU PRINCIPAL", True, Colors.GOLD)
        title_rect = title_surface.get_rect(center=(CENTER_X, CENTER_Y - 200))
        self.screen.blit(title_surface, title_rect)
        
        # Dessiner les boutons
        for button in self.main_menu_buttons:
            button.draw(self.screen, self.fonts)
        
        # Heure actuelle
        current_time = time.strftime("%H:%M")
        time_font = self.fonts.get('small')
        time_surface = time_font.render(current_time, True, Colors.SILVER)
        time_rect = time_surface.get_rect(center=(CENTER_X, CENTER_Y + 180))
        self.screen.blit(time_surface, time_rect)
    
    def draw_background(self):
        """Dessine le fond Art Déco"""
        # Fond base
        self.screen.fill(Colors.DEEP_BLACK)
        
        # Motifs géométriques subtils
        self.draw_background_pattern()
    
    def draw_background_pattern(self):
        """Dessine les motifs de fond Art Déco"""
        # Lignes radiales subtiles
        for i in range(12):
            angle = (i * 30) * math.pi / 180
            start_radius = 50
            end_radius = SCREEN_RADIUS - 50
            
            start_x = CENTER_X + math.cos(angle) * start_radius
            start_y = CENTER_Y + math.sin(angle) * start_radius
            end_x = CENTER_X + math.cos(angle) * end_radius
            end_y = CENTER_Y + math.sin(angle) * end_radius
            
            pygame.draw.line(self.screen, Colors.CHARCOAL, 
                           (start_x, start_y), (end_x, end_y), 1)
        
        # Cercles concentriques
        for radius in [100, 200, 300]:
            if radius < SCREEN_RADIUS:
                pygame.draw.circle(self.screen, Colors.CHARCOAL, 
                                 (CENTER_X, CENTER_Y), radius, 1)
    
    def draw_circular_mask(self):
        """Applique le masque circulaire pour l'écran rond"""
        # Créer un masque pour l'écran circulaire
        mask_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        
        # Remplir tout en noir
        mask_surface.fill(Colors.PURE_BLACK)
        
        # Percer le cercle transparent
        pygame.draw.circle(mask_surface, (0, 0, 0, 0), 
                          (CENTER_X, CENTER_Y), SCREEN_RADIUS)
        
        # Bordure dorée
        pygame.draw.circle(self.screen, Colors.GOLD, 
                          (CENTER_X, CENTER_Y), SCREEN_RADIUS, 5)
        pygame.draw.circle(self.screen, Colors.DARK_GOLD, 
                          (CENTER_X, CENTER_Y), SCREEN_RADIUS - 8, 2)
        
        # Appliquer le masque
        self.screen.blit(mask_surface, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
    
    def draw_art_deco_ornaments(self):
        """Dessine les ornements Art Déco décoratifs"""
        # Ornements en étoile autour du titre
        for i in range(8):
            angle = (i * 45) * math.pi / 180
            distance = 120
            x = CENTER_X + math.cos(angle) * distance
            y = CENTER_Y + math.sin(angle) * distance
            
            # Petite étoile Art Déco
            self.draw_art_deco_star(x, y, 8)
    
    def draw_art_deco_star(self, x: float, y: float, size: int):
        """Dessine une étoile Art Déco"""
        points = []
        for i in range(8):
            angle = (i * 45) * math.pi / 180
            if i % 2 == 0:
                radius = size
            else:
                radius = size // 2
            
            point_x = x + math.cos(angle) * radius
            point_y = y + math.sin(angle) * radius
            points.append((point_x, point_y))
        
        pygame.draw.polygon(self.screen, Colors.GOLD, points)
        pygame.draw.polygon(self.screen, Colors.BRONZE, points, 1)
    
    def switch_screen(self, new_screen: str):
        """Change d'écran avec transition"""
        self.current_screen = new_screen
        self.transition_time = time.time()
        self.last_interaction = time.time()
        logger.info(f"Basculement vers écran: {new_screen}")
    
    def handle_events(self):
        """Gère les événements pygame"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_f:
                    pygame.display.toggle_fullscreen()
            
            elif event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION]:
                self.last_interaction = time.time()
                
                # Gestión d'événements selon l'écran actuel
                if self.current_screen == "main_menu":
                    for button in self.main_menu_buttons:
                        if button.handle_event(event):
                            break
                
                elif self.current_screen == "splash":
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.switch_screen("main_menu")
    
    def start_animation_thread(self):
        """Démarre le thread d'animation"""
        def animation_loop():
            while not self.stop_animations:
                # Mettre à jour les animations des éléments
                for element in self.elements:
                    if hasattr(element, 'update'):
                        element.update()
                
                time.sleep(1/60)  # 60 FPS
        
        self.animation_thread = threading.Thread(target=animation_loop, daemon=True)
        self.animation_thread.start()
    
    def run(self):
        """Boucle principale de l'interface"""
        while self.running:
            # Gérer les événements
            self.handle_events()
            
            # Mise à jour de la logique
            self.update()
            
            # Rendu
            self.render()
            
            # Limiter le framerate
            self.clock.tick(60)
        
        self.cleanup()
    
    def update(self):
        """Met à jour la logique de l'interface"""
        # Vérifier l'inactivité pour revenir au splash
        if time.time() - self.last_interaction > 60:  # 1 minute
            if self.current_screen != "splash":
                self.switch_screen("splash")
    
    def render(self):
        """Rendu de l'interface"""
        if self.current_screen == "splash":
            self.draw_splash_screen()
        elif self.current_screen == "main_menu":
            self.draw_main_menu()
        elif self.current_screen == "cocktail_menu":
            self.draw_cocktail_menu()
        elif self.current_screen == "cleaning":
            self.draw_cleaning_screen()
        elif self.current_screen == "settings":
            self.draw_settings_screen()
        
        pygame.display.flip()
    
    def draw_cocktail_menu(self):
        """Dessine le menu des cocktails"""
        self.draw_background()
        self.draw_circular_mask()
        
        # Titre
        title_font = self.fonts.get('title')
        title_surface = title_font.render("COCKTAILS", True, Colors.GOLD)
        title_rect = title_surface.get_rect(center=(CENTER_X, 100))
        self.screen.blit(title_surface, title_rect)
        
        # Liste des cocktails (placeholder)
        font = self.fonts.get('medium')
        y_pos = 200
        for i, cocktail in enumerate(self.cocktails[:5]):
            text = f"{i+1}. {cocktail['name']}"
            text_surface = font.render(text, True, Colors.CREAM)
            text_rect = text_surface.get_rect(center=(CENTER_X, y_pos))
            self.screen.blit(text_surface, text_rect)
            y_pos += 50
        
        # Bouton retour
        back_button = ArtDecoButton(50, 50, 120, 40, "RETOUR", 
                                   lambda: self.switch_screen("main_menu"))
        back_button.draw(self.screen, self.fonts)
    
    def draw_cleaning_screen(self):
        """Dessine l'écran de nettoyage"""
        self.draw_background()
        self.draw_circular_mask()
        
        # Titre
        title_font = self.fonts.get('title')
        title_surface = title_font.render("NETTOYAGE", True, Colors.GOLD)
        title_rect = title_surface.get_rect(center=(CENTER_X, CENTER_Y - 100))
        self.screen.blit(title_surface, title_rect)
        
        # Message
        font = self.fonts.get('medium')
        message = "Système de nettoyage automatique"
        msg_surface = font.render(message, True, Colors.CREAM)
        msg_rect = msg_surface.get_rect(center=(CENTER_X, CENTER_Y))
        self.screen.blit(msg_surface, msg_rect)
        
        # Bouton retour
        back_button = ArtDecoButton(50, 50, 120, 40, "RETOUR", 
                                   lambda: self.switch_screen("main_menu"))
        back_button.draw(self.screen, self.fonts)
    
    def draw_settings_screen(self):
        """Dessine l'écran des paramètres"""
        self.draw_background()
        self.draw_circular_mask()
        
        # Titre
        title_font = self.fonts.get('title')
        title_surface = title_font.render("PARAMÈTRES", True, Colors.GOLD)
        title_rect = title_surface.get_rect(center=(CENTER_X, CENTER_Y - 100))
        self.screen.blit(title_surface, title_rect)
        
        # Message
        font = self.fonts.get('medium')
        message = "Configuration et maintenance"
        msg_surface = font.render(message, True, Colors.CREAM)
        msg_rect = msg_surface.get_rect(center=(CENTER_X, CENTER_Y))
        self.screen.blit(msg_surface, msg_rect)
        
        # Bouton retour
        back_button = ArtDecoButton(50, 50, 120, 40, "RETOUR", 
                                   lambda: self.switch_screen("main_menu"))
        back_button.draw(self.screen, self.fonts)
    
    def cleanup(self):
        """Nettoie les ressources"""
        self.stop_animations = True
        if self.animation_thread:
            self.animation_thread.join(timeout=1)
        
        pygame.quit()

# Point d'entrée pour l'interface
def main():
    """Lance l'interface Art Déco"""
    interface = ArtDecoInterface()
    
    try:
        if interface.initialize():
            interface.run()
    except Exception as e:
        logger.error(f"Erreur interface: {e}")
    finally:
        interface.cleanup()

if __name__ == "__main__":
    main()