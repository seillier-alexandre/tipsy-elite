# -*- coding: utf-8 -*-
"""
Sélecteur de dose pour interface tactile de machine à cocktails
Composant UI pour choisir entre dose simple et double (inspiré de Tipsy)
"""
import pygame
import math
from typing import Tuple, Optional, Callable
from enum import Enum

class DoseMode(Enum):
    """Modes de dose disponibles"""
    SINGLE = "single"
    DOUBLE = "double"
    HALF = "half"
    TRIPLE = "triple"

class DoseSelector:
    """Sélecteur de dose tactile avec animations Art Déco"""
    
    def __init__(self, center: Tuple[int, int], size: Tuple[int, int] = (300, 80)):
        self.center = center
        self.size = size
        self.rect = pygame.Rect(
            center[0] - size[0] // 2,
            center[1] - size[1] // 2,
            size[0], size[1]
        )
        
        # État
        self.selected_dose = DoseMode.SINGLE
        self.callback: Optional[Callable] = None
        self.enabled = True
        
        # Animation
        self.animation_progress = 0.0
        self.animation_speed = 0.15
        self.hover_scale = 1.0
        self.target_hover_scale = 1.0
        
        # Couleurs Art Déco
        self.colors = {
            'background': (36, 36, 36),          # Charcoal
            'border': (212, 175, 55),            # Gold
            'single_normal': (70, 130, 180),     # Steel Blue
            'single_active': (100, 149, 237),    # Cornflower Blue
            'double_normal': (184, 134, 11),     # Dark Gold
            'double_active': (212, 175, 55),     # Gold
            'text': (245, 235, 215),             # Cream
            'text_active': (15, 15, 15),         # Deep Black
            'disabled': (128, 128, 128)          # Gray
        }
        
        # Boutons pour chaque dose
        button_width = size[0] // 2 - 10
        button_height = size[1] - 20
        
        self.single_button = pygame.Rect(
            self.rect.x + 5,
            self.rect.y + 10,
            button_width,
            button_height
        )
        
        self.double_button = pygame.Rect(
            self.rect.x + button_width + 15,
            self.rect.y + 10,
            button_width,
            button_height
        )
        
        # Police (sera initialisée avec pygame)
        self.font = None
        self.font_small = None
    
    def set_callback(self, callback: Callable):
        """Définit le callback appelé lors du changement de dose"""
        self.callback = callback
    
    def set_dose(self, dose: DoseMode):
        """Change la dose sélectionnée"""
        if self.selected_dose != dose:
            self.selected_dose = dose
            self.animation_progress = 0.0
            if self.callback:
                self.callback(dose)
    
    def set_enabled(self, enabled: bool):
        """Active/désactive le sélecteur"""
        self.enabled = enabled
    
    def handle_event(self, event) -> bool:
        """Gère les événements tactiles/souris"""
        if not self.enabled:
            return False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            
            if self.single_button.collidepoint(mouse_pos):
                self.set_dose(DoseMode.SINGLE)
                return True
            elif self.double_button.collidepoint(mouse_pos):
                self.set_dose(DoseMode.DOUBLE)
                return True
        
        elif event.type == pygame.MOUSEMOTION:
            mouse_pos = pygame.mouse.get_pos()
            
            # Animation hover
            if (self.single_button.collidepoint(mouse_pos) or 
                self.double_button.collidepoint(mouse_pos)):
                self.target_hover_scale = 1.05
            else:
                self.target_hover_scale = 1.0
        
        return False
    
    def update(self):
        """Met à jour les animations"""
        # Animation de transition
        if self.animation_progress < 1.0:
            self.animation_progress = min(1.0, self.animation_progress + self.animation_speed)
        
        # Animation hover
        scale_diff = self.target_hover_scale - self.hover_scale
        if abs(scale_diff) > 0.01:
            self.hover_scale += scale_diff * 0.2
        else:
            self.hover_scale = self.target_hover_scale
    
    def render(self, surface: pygame.Surface):
        """Affiche le sélecteur de dose"""
        if not self.font:
            self._init_fonts()
        
        # Fond principal avec bordure dorée
        self._draw_background(surface)
        
        # Boutons de dose
        self._draw_dose_button(surface, self.single_button, DoseMode.SINGLE, "1x", "Simple")
        self._draw_dose_button(surface, self.double_button, DoseMode.DOUBLE, "2x", "Double")
        
        # Indicateur de sélection animé
        self._draw_selection_indicator(surface)
    
    def _init_fonts(self):
        """Initialise les polices"""
        try:
            self.font = pygame.font.Font(None, 24)
            self.font_small = pygame.font.Font(None, 18)
        except:
            # Fallback si police non trouvée
            self.font = pygame.font.SysFont('Arial', 24)
            self.font_small = pygame.font.SysFont('Arial', 18)
    
    def _draw_background(self, surface: pygame.Surface):
        """Dessine le fond du sélecteur"""
        # Fond avec coins arrondis
        pygame.draw.rect(surface, self.colors['background'], self.rect, border_radius=12)
        
        # Bordure dorée
        if self.enabled:
            border_color = self.colors['border']
        else:
            border_color = self.colors['disabled']
        
        pygame.draw.rect(surface, border_color, self.rect, width=2, border_radius=12)
    
    def _draw_dose_button(self, surface: pygame.Surface, button_rect: pygame.Rect, 
                         dose: DoseMode, main_text: str, sub_text: str):
        """Dessine un bouton de dose"""
        is_selected = (dose == self.selected_dose)
        is_hovered = button_rect.collidepoint(pygame.mouse.get_pos())
        
        # Couleurs selon l'état
        if not self.enabled:
            bg_color = self.colors['disabled']
            text_color = self.colors['text']
        elif is_selected:
            bg_color = self.colors[f'{dose.value}_active']
            text_color = self.colors['text_active']
        else:
            bg_color = self.colors[f'{dose.value}_normal']
            text_color = self.colors['text']
        
        # Animation de hover
        if is_hovered and self.enabled:
            scale_factor = self.hover_scale
            scaled_rect = self._scale_rect(button_rect, scale_factor)
        else:
            scaled_rect = button_rect
        
        # Fond du bouton
        pygame.draw.rect(surface, bg_color, scaled_rect, border_radius=8)
        
        # Bordure si sélectionné
        if is_selected:
            border_color = self.colors['border']
            pygame.draw.rect(surface, border_color, scaled_rect, width=2, border_radius=8)
        
        # Texte principal (1x, 2x)
        main_surface = self.font.render(main_text, True, text_color)
        main_rect = main_surface.get_rect()
        main_rect.centerx = scaled_rect.centerx
        main_rect.centery = scaled_rect.centery - 8
        surface.blit(main_surface, main_rect)
        
        # Texte secondaire (Simple, Double)
        sub_surface = self.font_small.render(sub_text, True, text_color)
        sub_rect = sub_surface.get_rect()
        sub_rect.centerx = scaled_rect.centerx
        sub_rect.centery = scaled_rect.centery + 12
        surface.blit(sub_surface, sub_rect)
    
    def _draw_selection_indicator(self, surface: pygame.Surface):
        """Dessine l'indicateur de sélection animé"""
        if not self.enabled:
            return
        
        # Position de l'indicateur selon la sélection
        if self.selected_dose == DoseMode.SINGLE:
            target_x = self.single_button.centerx
        else:
            target_x = self.double_button.centerx
        
        # Animation fluide de l'indicateur
        indicator_radius = 3
        indicator_y = self.rect.bottom - 8
        
        # Effet de pulsation
        pulse_factor = 1.0 + 0.3 * math.sin(pygame.time.get_ticks() * 0.01)
        current_radius = int(indicator_radius * pulse_factor)
        
        pygame.draw.circle(
            surface,
            self.colors['border'],
            (target_x, indicator_y),
            current_radius
        )
    
    def _scale_rect(self, rect: pygame.Rect, scale: float) -> pygame.Rect:
        """Applique un facteur d'échelle à un rectangle"""
        new_width = int(rect.width * scale)
        new_height = int(rect.height * scale)
        new_x = rect.centerx - new_width // 2
        new_y = rect.centery - new_height // 2
        return pygame.Rect(new_x, new_y, new_width, new_height)
    
    def get_dose_multiplier(self) -> float:
        """Récupère le multiplicateur de la dose sélectionnée"""
        multipliers = {
            DoseMode.SINGLE: 1.0,
            DoseMode.DOUBLE: 2.0,
            DoseMode.HALF: 0.5,
            DoseMode.TRIPLE: 3.0
        }
        return multipliers.get(self.selected_dose, 1.0)
    
    def get_dose_text(self) -> str:
        """Récupère le texte descriptif de la dose"""
        texts = {
            DoseMode.SINGLE: "Dose Simple",
            DoseMode.DOUBLE: "Dose Double",
            DoseMode.HALF: "Demi-Dose",
            DoseMode.TRIPLE: "Triple Dose"
        }
        return texts.get(self.selected_dose, "Dose Simple")

class CompactDoseSelector(DoseSelector):
    """Version compacte du sélecteur pour espace réduit"""
    
    def __init__(self, center: Tuple[int, int], size: Tuple[int, int] = (120, 40)):
        super().__init__(center, size)
        
        # Repositionner les boutons pour la version compacte
        button_size = 50
        button_spacing = 10
        
        self.single_button = pygame.Rect(
            self.rect.centerx - button_size - button_spacing // 2,
            self.rect.centery - button_size // 2,
            button_size,
            button_size
        )
        
        self.double_button = pygame.Rect(
            self.rect.centerx + button_spacing // 2,
            self.rect.centery - button_size // 2,
            button_size,
            button_size
        )
    
    def _draw_dose_button(self, surface: pygame.Surface, button_rect: pygame.Rect, 
                         dose: DoseMode, main_text: str, sub_text: str):
        """Version compacte du bouton - texte principal uniquement"""
        is_selected = (dose == self.selected_dose)
        is_hovered = button_rect.collidepoint(pygame.mouse.get_pos())
        
        # Couleurs selon l'état
        if not self.enabled:
            bg_color = self.colors['disabled']
            text_color = self.colors['text']
        elif is_selected:
            bg_color = self.colors[f'{dose.value}_active']
            text_color = self.colors['text_active']
        else:
            bg_color = self.colors[f'{dose.value}_normal']
            text_color = self.colors['text']
        
        # Animation de hover
        if is_hovered and self.enabled:
            scale_factor = self.hover_scale
            scaled_rect = self._scale_rect(button_rect, scale_factor)
        else:
            scaled_rect = button_rect
        
        # Fond du bouton (circulaire pour version compacte)
        pygame.draw.circle(
            surface,
            bg_color,
            scaled_rect.center,
            scaled_rect.width // 2
        )
        
        # Bordure si sélectionné
        if is_selected:
            pygame.draw.circle(
                surface,
                self.colors['border'],
                scaled_rect.center,
                scaled_rect.width // 2,
                width=2
            )
        
        # Texte principal centré
        main_surface = self.font.render(main_text, True, text_color)
        main_rect = main_surface.get_rect(center=scaled_rect.center)
        surface.blit(main_surface, main_rect)

# Test du composant
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Test Dose Selector")
    clock = pygame.time.Clock()
    
    # Créer sélecteurs
    dose_selector = DoseSelector((400, 200))
    compact_selector = CompactDoseSelector((400, 350))
    
    def on_dose_changed(dose):
        print(f"Dose changée: {dose.value}")
    
    dose_selector.set_callback(on_dose_changed)
    compact_selector.set_callback(on_dose_changed)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            dose_selector.handle_event(event)
            compact_selector.handle_event(event)
        
        # Mise à jour
        dose_selector.update()
        compact_selector.update()
        
        # Affichage
        screen.fill((15, 15, 15))  # Fond noir
        
        dose_selector.render(screen)
        compact_selector.render(screen)
        
        # Texte d'info
        font = pygame.font.Font(None, 36)
        title = font.render("Sélecteurs de Dose - Test", True, (245, 235, 215))
        screen.blit(title, (400 - title.get_width() // 2, 50))
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()