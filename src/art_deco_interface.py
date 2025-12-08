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

@dataclass
class GestureEvent:
    """Événement de geste tactile"""
    gesture_type: str  # 'swipe_left', 'swipe_right', 'swipe_up', 'swipe_down'
    start_pos: Tuple[int, int]
    end_pos: Tuple[int, int]
    distance: float
    velocity: float
    timestamp: float

class GestureManager:
    """Gestionnaire des gestes tactiles pour interface moderne avec animations fluides"""
    
    def __init__(self, min_distance: int = 50, min_velocity: float = 200, screen_width: int = 800):
        self.min_distance = min_distance
        self.min_velocity = min_velocity
        self.screen_width = screen_width
        self.min_swipe_threshold = screen_width // 4  # 1/4 de l'écran comme dans Tipsy
        
        self.touch_start = None
        self.touch_start_time = None
        self.is_dragging = False
        self.drag_offset = 0
        self.current_gesture = None
        
        # Animation fluide
        self.animation_offset = 0
        self.target_offset = 0
        self.animation_speed = 0.2
        self.max_drag_distance = screen_width // 2
        
        self.callbacks = {
            'swipe_left': [],
            'swipe_right': [], 
            'swipe_up': [],
            'swipe_down': [],
            'drag_start': [],
            'drag_move': [],
            'drag_end': []
        }
    
    def register_callback(self, gesture_type: str, callback: Callable):
        """Enregistre un callback pour un geste"""
        if gesture_type in self.callbacks:
            self.callbacks[gesture_type].append(callback)
    
    def handle_event(self, event) -> Optional[GestureEvent]:
        """Traite les événements tactiles/souris avec animations fluides"""
        current_time = time.time()
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.touch_start = pygame.mouse.get_pos()
            self.touch_start_time = current_time
            self.is_dragging = False
            self.drag_offset = 0
            self._trigger_callbacks_with_data('drag_start', {'position': self.touch_start})
            return None
        
        elif event.type == pygame.MOUSEMOTION and self.touch_start:
            current_pos = pygame.mouse.get_pos()
            dx = current_pos[0] - self.touch_start[0]
            dy = current_pos[1] - self.touch_start[1]
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Détecter début du drag si mouvement suffisant
            if distance > 10 and not self.is_dragging:
                self.is_dragging = True
                self.current_gesture = self._detect_gesture_direction(dx, dy)
            
            # Si on est en train de draguer
            if self.is_dragging:
                # Limiter le drag selon la direction
                if abs(dx) > abs(dy):  # Drag horizontal
                    self.drag_offset = max(-self.max_drag_distance, 
                                         min(self.max_drag_distance, dx))
                else:  # Drag vertical
                    self.drag_offset = max(-self.max_drag_distance, 
                                         min(self.max_drag_distance, dy))
                
                self._trigger_callbacks_with_data('drag_move', {
                    'offset': self.drag_offset,
                    'direction': self.current_gesture,
                    'position': current_pos
                })
            
            return None
        
        elif event.type == pygame.MOUSEBUTTONUP and self.touch_start:
            touch_end = pygame.mouse.get_pos()
            touch_end_time = current_time
            
            # Calculer distance et vélocité
            dx = touch_end[0] - self.touch_start[0]
            dy = touch_end[1] - self.touch_start[1]
            distance = math.sqrt(dx*dx + dy*dy)
            duration = max(touch_end_time - self.touch_start_time, 0.001)
            velocity = distance / duration
            
            gesture_event = None
            
            # Si c'était un drag, vérifier s'il faut déclencher un swipe
            if self.is_dragging:
                abs_offset = abs(self.drag_offset)
                
                # Swipe confirmé si dépassement du seuil ou vélocité suffisante
                if abs_offset > self.min_swipe_threshold or velocity > self.min_velocity:
                    gesture_event = self._create_gesture_event(dx, dy, distance, velocity)
                    if gesture_event:
                        self._trigger_callbacks(gesture_event)
                        # Animation de retour fluide
                        self.target_offset = self.screen_width if self.drag_offset > 0 else -self.screen_width
                else:
                    # Retour à la position initiale
                    self.target_offset = 0
                
                self._trigger_callbacks_with_data('drag_end', {
                    'offset': self.drag_offset,
                    'confirmed': gesture_event is not None,
                    'gesture': gesture_event
                })
            
            # Vérifier geste simple (click/tap)
            elif distance < self.min_distance and duration < 0.5:
                # C'est un tap/click simple
                self._trigger_callbacks_with_data('tap', {'position': touch_end})
            
            # Reset
            self.touch_start = None
            self.touch_start_time = None
            self.is_dragging = False
            self.current_gesture = None
            
            return gesture_event
    
    def _detect_gesture_direction(self, dx: float, dy: float) -> str:
        """Détecte la direction du geste"""
        abs_dx = abs(dx)
        abs_dy = abs(dy)
        
        if abs_dx > abs_dy:  # Geste horizontal
            return 'swipe_right' if dx > 0 else 'swipe_left'
        else:  # Geste vertical
            return 'swipe_down' if dy > 0 else 'swipe_up'
    
    def _create_gesture_event(self, dx: float, dy: float, distance: float, velocity: float) -> Optional[GestureEvent]:
        """Crée un événement de geste"""
        gesture_type = self._detect_gesture_direction(dx, dy)
        
        return GestureEvent(
            gesture_type=gesture_type,
            start_pos=self.touch_start,
            end_pos=(self.touch_start[0] + dx, self.touch_start[1] + dy),
            distance=distance,
            velocity=velocity,
            timestamp=time.time()
        )
    
    def _trigger_callbacks(self, gesture_event: GestureEvent):
        """Déclenche les callbacks pour un geste"""
        for callback in self.callbacks[gesture_event.gesture_type]:
            try:
                callback(gesture_event)
            except Exception as e:
                logger.error(f"Erreur callback geste {gesture_event.gesture_type}: {e}")
    
    def _trigger_callbacks_with_data(self, event_type: str, data: Dict):
        """Déclenche les callbacks avec données supplémentaires"""
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Erreur callback {event_type}: {e}")
    
    def update_animation(self):
        """Met à jour l'animation fluide"""
        # Animation interpolée vers la cible
        diff = self.target_offset - self.animation_offset
        if abs(diff) > 1:
            self.animation_offset += diff * self.animation_speed
        else:
            self.animation_offset = self.target_offset
    
    def get_current_offset(self) -> float:
        """Récupère l'offset actuel pour l'affichage"""
        if self.is_dragging:
            return self.drag_offset
        return self.animation_offset
    
    def reset_animation(self):
        """Remet l'animation à zéro"""
        self.target_offset = 0
        self.animation_offset = 0
        self.drag_offset = 0

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
        # Initialiser pygame et le module font
        if not pygame.get_init():
            pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()
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

class CocktailCarousel:
    """Carrousel de cocktails avec navigation tactile horizontale"""
    
    def __init__(self, cocktails: List[Dict], fonts: 'Fonts'):
        self.cocktails = cocktails
        self.fonts = fonts
        self.current_index = 0
        self.selected_index = 0  # Alias pour compatibilité
        self.scroll_offset = 0.0
        self.target_offset = 0.0
        self.is_animating = False
        self.card_width = 500
        self.card_height = 600
        
    def next_cocktail(self):
        """Passe au cocktail suivant"""
        if self.current_index < len(self.cocktails) - 1:
            self.current_index += 1
            self.selected_index = self.current_index  # Synchroniser
            self.target_offset = -self.current_index * self.card_width
            self.is_animating = True
    
    def previous_cocktail(self):
        """Passe au cocktail précédent"""
        if self.current_index > 0:
            self.current_index -= 1
            self.selected_index = self.current_index  # Synchroniser
            self.target_offset = -self.current_index * self.card_width
            self.is_animating = True
    
    def update(self):
        """Met à jour les animations"""
        if self.is_animating:
            diff = self.target_offset - self.scroll_offset
            self.scroll_offset += diff * 0.15
            if abs(diff) < 1:
                self.scroll_offset = self.target_offset
                self.is_animating = False
    
    def draw(self, screen):
        """Dessine le carrousel"""
        self.update()
        
        # Position centrale pour l'affichage
        center_x = CENTER_X
        center_y = CENTER_Y - 50
        
        for i, cocktail in enumerate(self.cocktails):
            # Position de la carte
            card_x = center_x - self.card_width // 2 + i * self.card_width + self.scroll_offset
            card_y = center_y - self.card_height // 2
            
            # Ne dessiner que les cartes visibles
            if -self.card_width <= card_x <= SCREEN_WIDTH:
                self._draw_cocktail_card(screen, cocktail, card_x, card_y, i == self.current_index)
    
    def _draw_cocktail_card(self, screen, cocktail, x, y, is_active):
        """Dessine une carte cocktail"""
        # Échelle pour carte active
        scale = 1.0 if is_active else 0.85
        alpha = 255 if is_active else 180
        
        # Surface de la carte avec alpha
        card_surface = pygame.Surface((self.card_width * scale, self.card_height * scale), pygame.SRCALPHA)
        
        # Fond avec dégradé Art Déco
        self._draw_art_deco_background(card_surface, scale, is_active)
        
        # Image du cocktail (placeholder pour l'instant)
        self._draw_cocktail_image(card_surface, cocktail, scale)
        
        # Nom du cocktail
        self._draw_cocktail_info(card_surface, cocktail, scale, is_active)
        
        # Appliquer alpha et dessiner
        card_surface.set_alpha(alpha)
        final_x = x + (self.card_width - self.card_width * scale) // 2
        final_y = y + (self.card_height - self.card_height * scale) // 2
        screen.blit(card_surface, (final_x, final_y))
    
    def _draw_art_deco_background(self, surface, scale, is_active):
        """Dessine le fond Art Déco de la carte"""
        width = int(self.card_width * scale)
        height = int(self.card_height * scale)
        
        # Fond principal
        color = Colors.CHARCOAL if is_active else Colors.DEEP_BLACK
        pygame.draw.rect(surface, color, (0, 0, width, height), border_radius=15)
        
        # Bordure dorée
        border_color = Colors.GOLD if is_active else Colors.DARK_GOLD
        pygame.draw.rect(surface, border_color, (0, 0, width, height), width=3, border_radius=15)
        
        # Motifs Art Déco
        if is_active:
            # Lignes décoratives en haut
            for i in range(3):
                y_pos = 20 + i * 8
                line_width = width - 40 - i * 20
                line_x = (width - line_width) // 2
                pygame.draw.rect(surface, Colors.DARK_GOLD, (line_x, y_pos, line_width, 2))
    
    def _draw_cocktail_image(self, surface, cocktail, scale):
        """Dessine l'image du cocktail"""
        # Zone image - format rectangulaire plus naturel
        img_width = int(350 * scale)  # Légèrement plus large
        img_height = int(250 * scale)  # Format plus rectangulaire
        img_x = (int(self.card_width * scale) - img_width) // 2
        img_y = int(60 * scale)  # Plus haut pour compenser la hauteur réduite
        
        # Charger la vraie image du cocktail
        cocktail_image = None
        try:
            # Import conditionnel de l'ImageManager
            from image_manager import get_image_manager
            
            cocktail_id = cocktail.get('id', '')
            if cocktail_id:
                image_manager = get_image_manager()
                cocktail_image = image_manager.load_cocktail_image(
                    cocktail_id, 'main', (img_width, img_height)
                )
                logger.debug(f"Image chargée pour {cocktail_id}: {cocktail_image is not None}")
                
                if cocktail_image is not None:
                    # Afficher l'image directement - pure et belle !
                    surface.blit(cocktail_image, (img_x, img_y))
                    return  # Image chargée avec succès
        
        except Exception as e:
            logger.debug(f"Erreur chargement image cocktail {cocktail.get('id', 'inconnu')}: {e}")
        
        # Fallback : fond coloré rectangulaire si image non disponible
        logger.debug(f"Affichage fallback pour cocktail {cocktail.get('name', 'inconnu')}")
        img_color = self._get_cocktail_color(cocktail)
        
        # Fond coloré rectangulaire
        pygame.draw.rect(surface, img_color, (img_x, img_y, img_width, img_height))
        
        # Bordure dorée
        pygame.draw.rect(surface, Colors.GOLD, (img_x-2, img_y-2, img_width+4, img_height+4), width=2)
        
        # Icône cocktail au centre
        icon_size = int(60 * scale)
        icon_x = img_x + (img_width - icon_size) // 2
        icon_y = img_y + (img_height - icon_size) // 2
        
        # Dessiner un verre stylisé
        glass_color = Colors.CREAM
        # Coupe du verre
        pygame.draw.ellipse(surface, glass_color, (icon_x + icon_size//4, icon_y + icon_size//3, icon_size//2, icon_size//4), width=3)
        # Pied du verre
        pygame.draw.line(surface, glass_color, (icon_x + icon_size//2, icon_y + icon_size//3 + icon_size//4), 
                        (icon_x + icon_size//2, icon_y + icon_size - 8), width=2)
        # Base du verre
        pygame.draw.line(surface, glass_color, (icon_x + icon_size//3, icon_y + icon_size - 8), 
                        (icon_x + 2*icon_size//3, icon_y + icon_size - 8), width=3)
        
        # Reflet style verre
        highlight = pygame.Surface((img_width//2, img_height//3), pygame.SRCALPHA)
        highlight.fill((*Colors.CREAM, 60))
        surface.blit(highlight, (img_x + img_width//4, img_y + img_height//6))
    
    def _draw_cocktail_info(self, surface, cocktail, scale, is_active):
        """Dessine les informations du cocktail"""
        width = int(self.card_width * scale)
        
        # Nom du cocktail
        font_size = 'title' if is_active else 'subtitle'
        font = self.fonts.get(font_size)
        name_surface = font.render(cocktail['name'], True, Colors.GOLD)
        name_rect = name_surface.get_rect(center=(width//2, int(420 * scale)))
        surface.blit(name_surface, name_rect)
        
        # Description courte
        if is_active and 'description' in cocktail:
            desc_font = self.fonts.get('small')
            desc_lines = self._wrap_text(cocktail['description'], desc_font, width - 40)
            y_offset = int(460 * scale)
            
            for line in desc_lines[:2]:  # Max 2 lignes
                line_surface = desc_font.render(line, True, Colors.CREAM)
                line_rect = line_surface.get_rect(center=(width//2, y_offset))
                surface.blit(line_surface, line_rect)
                y_offset += 25
    
    def _get_cocktail_color(self, cocktail):
        """Retourne une couleur représentative du cocktail"""
        colors = {
            'gin': Colors.EMERALD,
            'vodka': Colors.PLATINUM,
            'whisky': Colors.WHISKEY_AMBER,
            'rhum': Colors.BRONZE,
            'tequila': Colors.GOLD,
            'brandy': Colors.BURGUNDY,
            'campari': Colors.CRIMSON,
            'vermouth': Colors.BURGUNDY,
            'amaretto': Colors.DARK_GOLD
        }
        
        cocktail_name = cocktail.get('name', '').lower()
        logger.debug(f"Couleur pour cocktail: {cocktail_name}")
        
        # Recherche par nom de cocktail d'abord
        for spirit, color in colors.items():
            if spirit in cocktail_name:
                return color
        
        # Recherche par ingrédient principal  
        ingredients = cocktail.get('ingredients', [])
        logger.debug(f"Ingrédients cocktail: {len(ingredients)}")
        
        for ingredient in ingredients:
            ingredient_name = ingredient.get('name', '') if isinstance(ingredient, dict) else str(ingredient)
            for spirit, color in colors.items():
                if spirit.lower() in ingredient_name.lower():
                    return color
        
        # Couleur par défaut plus visible
        return Colors.BURGUNDY
    
    def _wrap_text(self, text, font, max_width):
        """Découpe le texte en lignes"""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if font.size(test_line)[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def get_current_cocktail(self):
        """Retourne le cocktail actuellement sélectionné"""
        return self.cocktails[self.current_index] if self.cocktails else None

class IngredientPanel:
    """Panel des ingrédients avec statut pompes (swipe up)"""
    
    def __init__(self, fonts: 'Fonts'):
        self.fonts = fonts
        self.visible = False
        self.slide_offset = SCREEN_HEIGHT
        self.target_offset = SCREEN_HEIGHT
        self.cocktail = None
        
    def show(self, cocktail):
        """Affiche le panel avec un cocktail"""
        self.cocktail = cocktail
        self.visible = True
        self.target_offset = 100  # Laisse un peu d'espace en haut
        
    def hide(self):
        """Cache le panel"""
        self.visible = False
        self.target_offset = SCREEN_HEIGHT
    
    def set_ingredients(self, ingredients):
        """Met à jour les ingrédients"""
        if self.cocktail is None:
            self.cocktail = {}
        self.cocktail['ingredients'] = ingredients
        
    def update(self):
        """Met à jour l'animation"""
        diff = self.target_offset - self.slide_offset
        self.slide_offset += diff * 0.2
        
        if not self.visible and abs(diff) < 5:
            self.slide_offset = SCREEN_HEIGHT
            
    def draw(self, screen):
        """Dessine le panel"""
        if self.slide_offset >= SCREEN_HEIGHT - 10:
            return
            
        self.update()
        
        # Surface du panel
        panel_height = SCREEN_HEIGHT - self.slide_offset
        panel_surface = pygame.Surface((SCREEN_WIDTH, panel_height), pygame.SRCALPHA)
        
        # Fond Art Déco
        panel_surface.fill(Colors.CHARCOAL)
        pygame.draw.rect(panel_surface, Colors.GOLD, (0, 0, SCREEN_WIDTH, panel_height), width=3)
        
        # Titre
        title_font = self.fonts.get('subtitle')
        title = "INGRÉDIENTS"
        title_surface = title_font.render(title, True, Colors.GOLD)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH//2, 50))
        panel_surface.blit(title_surface, title_rect)
        
        # Liste des ingrédients
        if self.cocktail:
            self._draw_ingredients_list(panel_surface)
        
        # Dessiner sur l'écran principal
        screen.blit(panel_surface, (0, self.slide_offset))
    
    def _draw_ingredients_list(self, surface):
        """Dessine la liste des ingrédients avec statut"""
        y_start = 100
        ingredient_height = 60
        
        for i, ingredient in enumerate(self.cocktail.get('ingredients', [])):
            y_pos = y_start + i * ingredient_height
            if y_pos > surface.get_height() - 50:
                break
                
            self._draw_ingredient_item(surface, ingredient, y_pos)
    
    def _draw_ingredient_item(self, surface, ingredient, y_pos):
        """Dessine un item ingrédient"""
        # Nom de l'ingrédient
        font = self.fonts.get('medium')
        name = ingredient['name']
        amount = f"{ingredient['amount_ml']}ml"
        
        name_surface = font.render(name, True, Colors.CREAM)
        surface.blit(name_surface, (50, y_pos))
        
        amount_surface = font.render(amount, True, Colors.GOLD)
        amount_rect = amount_surface.get_rect(right=SCREEN_WIDTH - 150, y=y_pos)
        surface.blit(amount_surface, amount_rect)
        
        # Indicateur statut (simulé pour l'instant)
        status_color = Colors.SUCCESS_GREEN if ingredient.get('is_available', True) else Colors.ERROR_RED
        pygame.draw.circle(surface, status_color, (SCREEN_WIDTH - 80, y_pos + 15), 12)

class SettingsPanel:
    """Panel des settings (swipe down)"""
    
    def __init__(self, fonts: 'Fonts'):
        self.fonts = fonts
        self.visible = False
        self.slide_offset = -SCREEN_HEIGHT
        self.target_offset = -SCREEN_HEIGHT
        
    def show(self):
        """Affiche le panel"""
        self.visible = True
        self.target_offset = -100  # Laisse un peu d'espace en bas
        
    def hide(self):
        """Cache le panel"""
        self.visible = False
        self.target_offset = -SCREEN_HEIGHT
        
    def update(self):
        """Met à jour l'animation"""
        diff = self.target_offset - self.slide_offset
        self.slide_offset += diff * 0.2
        
    def draw(self, screen):
        """Dessine le panel"""
        if self.slide_offset <= -SCREEN_HEIGHT + 10:
            return
            
        self.update()
        
        # Surface du panel
        panel_height = SCREEN_HEIGHT + self.slide_offset
        panel_surface = pygame.Surface((SCREEN_WIDTH, panel_height), pygame.SRCALPHA)
        
        # Fond Art Déco
        panel_surface.fill(Colors.CHARCOAL)
        pygame.draw.rect(panel_surface, Colors.GOLD, (0, 0, SCREEN_WIDTH, panel_height), width=3)
        
        # Titre
        title_font = self.fonts.get('subtitle')
        title = "PARAMÈTRES"
        title_surface = title_font.render(title, True, Colors.GOLD)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH//2, 50))
        panel_surface.blit(title_surface, title_rect)
        
        # Options de settings
        self._draw_settings_options(panel_surface)
        
        # Dessiner sur l'écran principal
        screen.blit(panel_surface, (0, self.slide_offset))
    
    def _draw_settings_options(self, surface):
        """Dessine les options de settings"""
        options = [
            "Calibrage Pompes",
            "Nettoyage Système", 
            "Historique Cocktails",
            "Niveau Bouteilles",
            "Configuration"
        ]
        
        y_start = 120
        option_height = 70
        
        for i, option in enumerate(options):
            y_pos = y_start + i * option_height
            if y_pos > surface.get_height() - 50:
                break
                
            # Fond option
            option_rect = pygame.Rect(30, y_pos - 10, SCREEN_WIDTH - 60, option_height - 20)
            pygame.draw.rect(surface, Colors.DEEP_BLACK, option_rect, border_radius=10)
            pygame.draw.rect(surface, Colors.DARK_GOLD, option_rect, width=2, border_radius=10)
            
            # Texte option
            font = self.fonts.get('medium')
            text_surface = font.render(option, True, Colors.CREAM)
            text_rect = text_surface.get_rect(center=option_rect.center)
            surface.blit(text_surface, text_rect)

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
        
        # Nouveaux composants tactiles
        self.gesture_manager = GestureManager()
        self.cocktail_carousel = None
        self.ingredient_panel = IngredientPanel(self.fonts)
        self.settings_panel = SettingsPanel(self.fonts)
        self.serve_button = None
        
        # Boutons retour pour chaque écran
        self.back_buttons = {}
        
        # État des panels
        self.ingredient_panel_visible = False
        self.settings_panel_visible = False
        
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
            import os
            # Configuration pour Raspberry Pi - essayer fbcon d'abord, puis fallback
            if not os.environ.get('DISPLAY'):
                os.environ['SDL_VIDEODRIVER'] = 'fbcon'
                os.environ['SDL_FBDEV'] = '/dev/fb0'
            
            pygame.init()
            pygame.mixer.init()
            
            # Cacher le curseur pour mode kiosk
            pygame.mouse.set_visible(False)
            
            logger.info("[OK] Pygame initialisé")
        except Exception as e:
            logger.error(f"[ERROR] Impossible d'initialiser Pygame: {e}")
            return False
        
        # Charger les données
        self.load_cocktails()
        
        # Créer les éléments UI
        self.create_ui_elements()
        
        # Initialiser le cocktail sélectionné
        if self.cocktails:
            self.selected_cocktail = self.cocktails[0]
            logger.info(f"Cocktail initial sélectionné: {self.selected_cocktail.get('name', 'Inconnu')}")
        
        # Démarrer le thread d'animation
        self.start_animation_thread()
        
        return True
    
    def load_cocktails(self):
        """Charge les cocktails depuis le gestionnaire de cocktails"""
        try:
            # Importer le gestionnaire de cocktails
            try:
                from cocktail_manager import get_cocktail_manager
                cocktail_manager = get_cocktail_manager()
                if not cocktail_manager:
                    raise ImportError("Gestionnaire cocktails non disponible")
            except (ImportError, AttributeError) as e:
                logger.error(f"Mode démo - gestionnaire cocktails non disponible: {e}")
                self.show_status_message("Mode démo - Préparation simulée", "info")
                return
            
            # Charger les cocktails réalisables
            recipes = cocktail_manager.database.get_makeable_cocktails() if cocktail_manager and cocktail_manager.database else []
            
            self.cocktails = []
            for recipe in recipes:
                cocktail_data = {
                    "id": recipe.id,
                    "name": recipe.name,
                    "description": recipe.description,
                    "ingredients": [
                        {
                            "name": ing.name,
                            "amount": f"{ing.amount_ml}ml",
                            "available": ing.is_available
                        } for ing in recipe.ingredients
                    ],
                    "category": recipe.category,
                    "glass_type": recipe.glass_type,
                    "garnish": recipe.garnish,
                    "is_makeable": recipe.is_makeable
                }
                self.cocktails.append(cocktail_data)
                
            logger.info(f"Chargé {len(self.cocktails)} cocktails réalisables")
            
        except Exception as e:
            logger.error(f"Erreur chargement cocktails: {e}")
            # Fallback vers des cocktails d'exemple
            self.cocktails = [
                {
                    "id": "gin_tonic",
                    "name": "Gin Tonic",
                    "ingredients": [
                        {"name": "Gin", "amount": "50ml", "available": True},
                        {"name": "Sprite", "amount": "100ml", "available": True}
                    ],
                    "description": "Classique rafraîchissant, simple et élégant",
                    "category": "classic",
                    "is_makeable": True
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
        
        # Créer le carrousel avec les cocktails chargés
        if self.cocktails:
            self.cocktail_carousel = CocktailCarousel(self.cocktails, self.fonts)
        
        # Créer le bouton servir
        self.serve_button = ArtDecoButton(
            CENTER_X - 100, 
            SCREEN_HEIGHT - 150,
            200, 60,
            "SERVIR",
            self.serve_cocktail
        )
        
        # Enregistrer les callbacks de gestes
        self.register_gesture_callbacks()
        
        # Créer les boutons retour
        self._setup_back_buttons()
    
    def _setup_back_buttons(self):
        """Crée les boutons retour pour chaque écran"""
        back_button_width = 120
        back_button_height = 40
        back_button_x = CENTER_X - back_button_width // 2
        back_button_y = SCREEN_HEIGHT - back_button_height - 30
        
        # Bouton retour pour écran cocktails
        self.back_buttons['cocktail_menu'] = ArtDecoButton(
            back_button_x, back_button_y, back_button_width, back_button_height,
            "RETOUR", lambda: self.switch_screen("main_menu")
        )
        
        # Bouton retour pour écran nettoyage
        self.back_buttons['cleaning'] = ArtDecoButton(
            back_button_x, back_button_y, back_button_width, back_button_height,
            "RETOUR", lambda: self.switch_screen("main_menu")
        )
        
        # Bouton retour pour écran paramètres
        self.back_buttons['settings'] = ArtDecoButton(
            back_button_x, back_button_y, back_button_width, back_button_height,
            "RETOUR", lambda: self.switch_screen("main_menu")
        )
    
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
    
    def register_gesture_callbacks(self):
        """Enregistre les callbacks pour les gestes tactiles"""
        # Gestes horizontaux pour navigation cocktails
        self.gesture_manager.register_callback('swipe_left', self.next_cocktail)
        self.gesture_manager.register_callback('swipe_right', self.previous_cocktail)
        
        # Geste vers le haut pour afficher les ingrédients
        self.gesture_manager.register_callback('swipe_up', self.show_ingredient_panel)
        
        # Geste vers le bas pour afficher les paramètres
        self.gesture_manager.register_callback('swipe_down', self.show_settings_panel)
    
    def next_cocktail(self, gesture_event=None):
        """Passe au cocktail suivant"""
        if self.cocktail_carousel and self.current_screen == "cocktail_menu":
            self.cocktail_carousel.next_cocktail()
            self.update_selected_cocktail()
    
    def previous_cocktail(self, gesture_event=None):
        """Passe au cocktail précédent"""
        if self.cocktail_carousel and self.current_screen == "cocktail_menu":
            self.cocktail_carousel.previous_cocktail()
            self.update_selected_cocktail()
    
    def show_ingredient_panel(self, gesture_event=None):
        """Affiche le panel des ingrédients"""
        if self.current_screen == "cocktail_menu" and not self.ingredient_panel_visible:
            # Mettre à jour les ingrédients du cocktail sélectionné
            if self.selected_cocktail:
                self.ingredient_panel.set_ingredients(self.selected_cocktail.get('ingredients', []))
            
            self.ingredient_panel_visible = True
            self.ingredient_panel.show()
            logger.info("Panel ingrédients affiché")
    
    def show_settings_panel(self, gesture_event=None):
        """Affiche le panel des paramètres"""
        if self.current_screen == "cocktail_menu" and not self.settings_panel_visible:
            self.settings_panel_visible = True
            self.settings_panel.show()
            logger.info("Panel paramètres affiché")
    
    def hide_panels(self):
        """Masque tous les panels ouverts"""
        if self.ingredient_panel_visible:
            self.ingredient_panel.hide()
            self.ingredient_panel_visible = False
        
        if self.settings_panel_visible:
            self.settings_panel.hide()
            self.settings_panel_visible = False
    
    def update_selected_cocktail(self):
        """Met à jour le cocktail sélectionné"""
        if self.cocktail_carousel and self.cocktails:
            index = self.cocktail_carousel.selected_index
            if 0 <= index < len(self.cocktails):
                self.selected_cocktail = self.cocktails[index]
                logger.info(f"Cocktail sélectionné: {self.selected_cocktail.get('name', 'Inconnu')}")
    
    def serve_cocktail(self):
        """Lance la préparation du cocktail sélectionné"""
        if not self.selected_cocktail:
            logger.warning("Aucun cocktail sélectionné")
            return
        
        if not self.selected_cocktail.get('is_makeable', False):
            logger.warning(f"Cocktail non réalisable: {self.selected_cocktail.get('name')}")
            return
        
        try:
            # Importer le gestionnaire de cocktails
            try:
                from cocktail_manager import get_cocktail_manager
                cocktail_manager = get_cocktail_manager()
                if not cocktail_manager:
                    raise ImportError("Gestionnaire cocktails non disponible")
            except (ImportError, AttributeError) as e:
                logger.error(f"Mode démo - gestionnaire cocktails non disponible: {e}")
                self.show_status_message("Mode démo - Préparation simulée", "info")
                return
            
            cocktail_id = self.selected_cocktail.get('id')
            if cocktail_id:
                logger.info(f"Démarrage préparation cocktail: {self.selected_cocktail.get('name')}")
                
                # Démarrer la préparation en asynchrone
                import threading
                import asyncio
                
                def prepare_async():
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        success = loop.run_until_complete(
                            cocktail_manager.maker.prepare_cocktail(cocktail_id)
                        )
                        loop.close()
                        
                        if success:
                            logger.info("Cocktail préparé avec succès")
                        else:
                            logger.error("Échec préparation cocktail")
                    except Exception as e:
                        logger.error(f"Erreur préparation: {e}")
                
                preparation_thread = threading.Thread(target=prepare_async, daemon=True)
                preparation_thread.start()
            
        except Exception as e:
            logger.error(f"Erreur service cocktail: {e}")

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
                
                # Traitement des gestes tactiles
                gesture_event = self.gesture_manager.handle_event(event)
                
                # Vérification des clics pour masquer les panels
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Si clic en dehors des panels, les masquer
                    if self.current_screen == "cocktail_menu":
                        if (self.ingredient_panel_visible or self.settings_panel_visible):
                            # Vérifier si le clic est en dehors des panels
                            click_pos = event.pos
                            panel_clicked = False
                            
                            if self.ingredient_panel_visible:
                                # Créer un rect temporaire pour le panel
                                panel_rect = pygame.Rect(0, self.ingredient_panel.slide_offset, 
                                                       SCREEN_WIDTH, SCREEN_HEIGHT - self.ingredient_panel.slide_offset)
                                if panel_rect.collidepoint(click_pos):
                                    panel_clicked = True
                            
                            if self.settings_panel_visible:
                                # Créer un rect temporaire pour le panel  
                                panel_rect = pygame.Rect(0, self.settings_panel.slide_offset,
                                                       SCREEN_WIDTH, SCREEN_HEIGHT + self.settings_panel.slide_offset)
                                if panel_rect.collidepoint(click_pos):
                                    panel_clicked = True
                            
                            if not panel_clicked:
                                self.hide_panels()
                
                # Gestion d'événements selon l'écran actuel
                if self.current_screen == "main_menu":
                    for button in self.main_menu_buttons:
                        if button.handle_event(event):
                            break
                
                elif self.current_screen == "cocktail_menu":
                    # Gestion du bouton servir
                    if (self.serve_button and self.selected_cocktail and 
                        self.selected_cocktail.get('is_makeable', False)):
                        if self.serve_button.handle_event(event):
                            break
                    
                    # Gestion du bouton retour
                    if 'cocktail_menu' in self.back_buttons:
                        if self.back_buttons['cocktail_menu'].handle_event(event):
                            break
                
                elif self.current_screen == "cleaning":
                    # Gestion du bouton retour
                    if 'cleaning' in self.back_buttons:
                        if self.back_buttons['cleaning'].handle_event(event):
                            break
                
                elif self.current_screen == "settings":
                    # Gestion du bouton retour
                    if 'settings' in self.back_buttons:
                        if self.back_buttons['settings'].handle_event(event):
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
        """Dessine le menu des cocktails avec carrousel tactile"""
        self.draw_background()
        self.draw_circular_mask()
        
        # Titre
        title_font = self.fonts.get('title')
        title_surface = title_font.render("COCKTAILS", True, Colors.GOLD)
        title_rect = title_surface.get_rect(center=(CENTER_X, 80))
        self.screen.blit(title_surface, title_rect)
        
        # Carrousel de cocktails
        if self.cocktail_carousel:
            self.cocktail_carousel.draw(self.screen)
            
            # Mettre à jour le cocktail sélectionné
            if (self.cocktail_carousel and 
                hasattr(self.cocktail_carousel, 'selected_index') and
                self.cocktail_carousel.selected_index != getattr(self, '_last_selected_index', -1)):
                self.update_selected_cocktail()
                if self.cocktail_carousel:  # Re-vérifier par sécurité
                    self._last_selected_index = self.cocktail_carousel.selected_index
        
        # Instructions gestuelles (petite aide en bas)
        help_font = self.fonts.get('small')
        help_texts = [
            "↔ Glissez horizontalement pour naviguer",
            "↑ Glissez vers le haut pour voir les ingrédients", 
            "↓ Glissez vers le bas pour les paramètres"
        ]
        
        help_y = SCREEN_HEIGHT - 120
        for text in help_texts:
            help_surface = help_font.render(text, True, Colors.SILVER)
            help_rect = help_surface.get_rect(center=(CENTER_X, help_y))
            self.screen.blit(help_surface, help_rect)
            help_y += 25
        
        # Bouton servir si cocktail sélectionné et réalisable
        if (self.selected_cocktail and 
            self.selected_cocktail.get('is_makeable', False) and 
            not self.ingredient_panel_visible and 
            not self.settings_panel_visible):
            self.serve_button.draw(self.screen, self.fonts)
        
        # Panels par-dessus le reste
        if self.ingredient_panel_visible:
            self.ingredient_panel.draw(self.screen)
        
        if self.settings_panel_visible:
            self.settings_panel.draw(self.screen)
        
        # Bouton retour centré en bas
        if 'cocktail_menu' in self.back_buttons:
            self.back_buttons['cocktail_menu'].draw(self.screen, self.fonts)
    
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
        
        # Bouton retour centré en bas
        screen_key = self.current_screen if self.current_screen in self.back_buttons else 'cleaning'
        if screen_key in self.back_buttons:
            self.back_buttons[screen_key].draw(self.screen, self.fonts)
    
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
        
        # Bouton retour centré en bas
        screen_key = self.current_screen if self.current_screen in self.back_buttons else 'cleaning'
        if screen_key in self.back_buttons:
            self.back_buttons[screen_key].draw(self.screen, self.fonts)
    
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