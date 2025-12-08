#!/usr/bin/env python3
"""
Test simple de l'interface Kivy Art Déco
"""

import kivy
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.graphics import Color, Ellipse, Line
from kivy.metrics import dp

# Configuration Kivy
from kivy.config import Config
Config.set('graphics', 'width', '480')
Config.set('graphics', 'height', '480')

class ArtDecoWidget(BoxLayout):
    """Widget simple Art Déco pour test"""
    
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        
        # Titre Art Déco
        title = Label(
            text='🍸 COCKTAIL MACHINE\nART DÉCO 1925',
            font_size='24sp',
            color=(0.83, 0.69, 0.22, 1),  # Doré
            bold=True,
            halign='center'
        )
        
        # Bouton stylé
        btn = Button(
            text='Gin Tonic',
            size_hint=(0.8, 0.3),
            pos_hint={'center_x': 0.5}
        )
        btn.bind(on_press=self.on_button_press)
        
        # Message
        self.message = Label(
            text='Interface Kivy Art Déco\nfonctionnelle ! ✨',
            font_size='16sp',
            color=(0.97, 0.96, 0.91, 1),  # Crème
            halign='center'
        )
        
        self.add_widget(title)
        self.add_widget(btn)
        self.add_widget(self.message)
        
        # Style Art Déco
        with self.canvas.before:
            Color(0.04, 0.04, 0.04, 1)  # Fond noir
        
        self._setup_deco_graphics()
    
    def _setup_deco_graphics(self):
        """Ajoute les motifs Art Déco"""
        with self.canvas.after:
            # Bordure dorée
            Color(0.83, 0.69, 0.22, 0.8)
            Line(rectangle=(self.x + 10, self.y + 10, 
                          self.width - 20, self.height - 20), width=3)
        
        self.bind(pos=self._update_graphics, size=self._update_graphics)
    
    def _update_graphics(self, *args):
        """Met à jour les graphiques"""
        self.canvas.after.clear()
        with self.canvas.after:
            Color(0.83, 0.69, 0.22, 0.8)
            Line(rectangle=(self.x + 10, self.y + 10, 
                          self.width - 20, self.height - 20), width=3)
    
    def on_button_press(self, instance):
        """Action du bouton"""
        self.message.text = f'🍸 {instance.text} sélectionné!\nInterface Art Déco fonctionne parfaitement ✨'
        print(f"✅ Bouton pressé: {instance.text}")

class TestApp(App):
    """Application de test simple"""
    
    def build(self):
        self.title = "Test Cocktail Machine Art Déco"
        return ArtDecoWidget()

if __name__ == '__main__':
    print("🍸 Test de l'interface Kivy Art Déco...")
    try:
        app = TestApp()
        app.run()
        print("✅ Test réussi !")
    except Exception as e:
        print(f"❌ Erreur test: {e}")
        import traceback
        traceback.print_exc()