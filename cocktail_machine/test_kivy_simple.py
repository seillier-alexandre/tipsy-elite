#!/usr/bin/env python3
"""
Test minimal de l'interface Kivy pour diagnostiquer les problèmes
"""

import os
os.environ['KIVY_NO_ARGS'] = '1'  # Désactiver le parsing d'arguments de Kivy

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.graphics import Color, Line
from kivy.core.window import Window
from kivy.config import Config

# Configuration AVANT les imports Kivy
Config.set('graphics', 'width', '480')
Config.set('graphics', 'height', '480')
Config.set('graphics', 'resizable', '1')

print("🍸 Test Kivy - Diagnostic...")
print(f"Window disponible: {Window is not None}")

class TestWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        
        # Style Art Déco simple
        with self.canvas.before:
            Color(0.04, 0.04, 0.04, 1)  # Fond noir
        
        # Titre
        title = Label(
            text='🍸 COCKTAIL MACHINE\nART DÉCO TEST',
            font_size='20sp',
            color=(0.83, 0.69, 0.22, 1),  # Doré
            bold=True,
            halign='center'
        )
        
        # Boutons de test
        btn1 = Button(text='Menu Principal', size_hint=(1, 0.2))
        btn2 = Button(text='Cocktail Details', size_hint=(1, 0.2))
        btn3 = Button(text='Settings', size_hint=(1, 0.2))
        
        btn1.bind(on_press=lambda x: print("Menu pressé"))
        btn2.bind(on_press=lambda x: print("Cocktail pressé"))
        btn3.bind(on_press=lambda x: print("Settings pressé"))
        
        # Status
        status = Label(
            text='✅ Interface Kivy fonctionnelle!\nPrêt pour le projet complet',
            color=(0.97, 0.96, 0.91, 1),
            halign='center'
        )
        
        self.add_widget(title)
        self.add_widget(btn1)
        self.add_widget(btn2) 
        self.add_widget(btn3)
        self.add_widget(status)

class TestApp(App):
    def build(self):
        self.title = "Test Cocktail Machine Art Déco"
        return TestWidget()

if __name__ == '__main__':
    try:
        print("Démarrage test Kivy...")
        app = TestApp()
        app.run()
        print("✅ Test terminé avec succès!")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()