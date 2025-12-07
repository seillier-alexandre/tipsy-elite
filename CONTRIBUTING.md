# 🤝 Contributing to Tipsy Elite

Merci de votre intérêt pour contribuer au projet Tipsy Elite ! Ce guide vous aidera à participer efficacement au développement.

## 📋 Guidelines de Contribution

### 🚀 Quick Start
1. **Fork** le repository
2. **Clone** votre fork localement
3. **Créer** une branche pour votre feature
4. **Développer** avec les standards du projet
5. **Tester** thoroughly
6. **Commit** avec des messages clairs
7. **Push** et créer une Pull Request

### 🏗️ Architecture du Projet

```
cocktail.bzh/
├── src/                    # Code source principal
│   ├── main.py            # Point d'entrée
│   ├── hardware_config.py # Configuration hardware
│   ├── tb6612_controller.py # Contrôleur pompes
│   ├── art_deco_interface.py # Interface utilisateur
│   ├── cocktail_manager.py   # Gestion cocktails
│   └── cleaning_system.py   # Système nettoyage
├── tests/                 # Tests unitaires et intégration
├── config/               # Fichiers de configuration
├── assets/              # Resources graphiques
└── docs/               # Documentation
```

## 🎯 Types de Contributions

### 🐛 Bug Reports
- Utilisez les templates d'issues
- Décrivez les étapes de reproduction
- Incluez logs et configurations
- Testez sur hardware si possible

### ✨ New Features
- Ouvrez une issue pour discussion
- Suivez l'architecture existante
- Documentez les nouvelles APIs
- Incluez des tests complets

### 🍹 Nouveaux Cocktails
- Utilisez le format JSON standard
- Vérifiez la disponibilité des ingrédients
- Testez les proportions
- Ajoutez descriptions historiques

### 🎨 Améliorations Interface
- Respectez le style Art Déco
- Testez sur écran tactile rond
- Optimisez les performances
- Maintenez l'accessibilité

## 📝 Standards de Code

### 🐍 Python Style Guide
```python
# Utilisez Black pour le formatage
black src/ tests/

# Type hints obligatoires
def prepare_cocktail(cocktail_id: str, volume: float) -> bool:
    """
    Prépare un cocktail avec volume spécifique.
    
    Args:
        cocktail_id: ID unique du cocktail
        volume: Volume en ml
        
    Returns:
        True si succès, False sinon
    """
    pass

# Docstrings pour toutes les fonctions publiques
class CocktailMaker:
    """Système de préparation de cocktails automatisé."""
    
    def __init__(self, config: Config):
        """Initialise le système avec configuration."""
        pass
```

### 🏷️ Naming Conventions
- **Classes**: `PascalCase` (ex: `CocktailManager`)
- **Functions/Variables**: `snake_case` (ex: `prepare_cocktail`)
- **Constants**: `UPPER_SNAKE_CASE` (ex: `MAX_POUR_TIME`)
- **Files**: `snake_case.py` (ex: `cocktail_manager.py`)

### 📦 Import Organization
```python
# Standard library
import logging
import time
from typing import Dict, List, Optional

# Third party
import pygame
import asyncio

# Local imports
from hardware_config import PUMP_CONFIGS
from tb6612_controller import pump_manager
```

## 🧪 Testing

### 🔬 Test Requirements
- **Coverage minimum**: 80%
- **Tests unitaires** pour toute nouvelle fonction
- **Tests d'intégration** pour features complètes
- **Tests hardware** si applicable (avec mocks)

### 🚦 Running Tests
```bash
# Tests complets
pytest tests/ -v

# Tests avec coverage
pytest --cov=src tests/ --cov-report=html

# Tests hardware (nécessite Pi)
pytest tests/ -m hardware

# Tests sans hardware
pytest tests/ -m "not hardware"
```

### 🎭 Mocking Hardware
```python
import unittest.mock as mock

class TestPumpController:
    @mock.patch('src.tb6612_controller.GPIO')
    def test_pump_start(self, mock_gpio):
        # Setup mock
        mock_gpio.setup.return_value = None
        
        # Test
        controller = PumpController()
        result = controller.start_pump(1, 50)
        
        # Assert
        assert result is True
        mock_gpio.setup.assert_called()
```

## 📋 Commit Guidelines

### 📝 Commit Message Format
```
🎯 <type>(<scope>): <description>

<body>

<footer>
```

### 🏷️ Types
- `🐛 fix`: Bug fixes
- `✨ feat`: New features
- `📝 docs`: Documentation
- `🎨 style`: Code style/formatting
- `♻️ refactor`: Code refactoring
- `🧪 test`: Adding/updating tests
- `⚡ perf`: Performance improvements
- `🔧 chore`: Maintenance tasks

### 📖 Examples
```bash
git commit -m "✨ feat(cocktails): add Bee's Knees recipe

- Classic 1920s cocktail with honey syrup
- Optimized for available ingredients
- Added historical context
- Includes garnish instructions"

git commit -m "🐛 fix(pumps): resolve TB6612FNG initialization race condition

- Added proper initialization sequencing
- Fixed GPIO setup timing issues
- Improved error handling
- Added hardware validation tests"
```

## 🔧 Hardware Development

### 🛠️ Hardware Setup
- **Raspberry Pi 4** (recommandé)
- **6x TB6612FNG** motor drivers
- **12x pompes péristaltiques**
- **Écran tactile rond 800x800**
- **Alimentation 12V/5A**

### ⚡ GPIO Configuration
- Respectez `hardware_config.py`
- Validez avec `HardwareValidator`
- Testez individuellement chaque pompe
- Documentez les modifications

### 🧪 Testing Hardware
```bash
# Test configuration GPIO
python -c "from src.hardware_config import HardwareValidator; print(HardwareValidator().validate_gpio_configuration())"

# Test contrôleurs
python -c "from src.tb6612_controller import pump_manager; pump_manager.initialize()"

# Test pompe individuelle
python -c "
from src.tb6612_controller import pump_manager
pump_manager.initialize()
pump_manager.start_pump(1, 50)
time.sleep(2)
pump_manager.stop_pump(1)
"
```

## 🎨 Design Guidelines

### 🏛️ Art Déco Principles
- **Géométrie**: Lignes droites, motifs symétriques
- **Couleurs**: Or, bordeaux, noir, argent
- **Typography**: Serif élégant, proportions classiques
- **Ornements**: Patterns géométriques, coins décoratifs

### 🖥️ Interface Standards
- **Responsive**: Adaptation écran rond
- **Touch-friendly**: Boutons minimum 40px
- **Accessibility**: Contraste, tailles de police
- **Performance**: 60fps, transitions fluides

### 🎭 Animation Guidelines
```python
# Utilisez les fonctions d'easing
def ease_in_out_cubic(t: float) -> float:
    if t < 0.5:
        return 4 * t * t * t
    return 1 - pow(-2 * t + 2, 3) / 2

# Animations standard
ANIMATION_DURATIONS = {
    'quick': 0.2,      # Boutons, hovers
    'normal': 0.5,     # Transitions écrans
    'slow': 1.0        # Animations complexes
}
```

## 📚 Documentation

### 📖 Documentation Requirements
- **Docstrings** pour toutes les fonctions publiques
- **Type hints** complets
- **README** mis à jour pour nouvelles features
- **API documentation** pour interfaces externes

### 🔍 Documentation Style
```python
def prepare_cocktail(
    cocktail_id: str, 
    size_multiplier: float = 1.0,
    custom_ingredients: Optional[Dict[str, float]] = None
) -> Tuple[bool, str]:
    """
    Prépare un cocktail avec paramètres personnalisés.
    
    Cette fonction gère la préparation complète d'un cocktail, incluant
    la validation des ingrédients, le calcul des volumes, et la coordination
    des pompes pour un résultat optimal.
    
    Args:
        cocktail_id: Identifiant unique du cocktail dans la base de données
        size_multiplier: Multiplicateur de taille (1.0 = normal, 0.5 = moitié)
        custom_ingredients: Ingrédients personnalisés {nom: volume_ml}
        
    Returns:
        Tuple contenant:
        - bool: True si préparation réussie, False sinon
        - str: Message de statut ou d'erreur détaillé
        
    Raises:
        ValueError: Si cocktail_id invalide ou size_multiplier hors limites
        RuntimeError: Si système de pompes non initialisé
        
    Example:
        >>> success, message = prepare_cocktail("old_fashioned", 1.5)
        >>> if success:
        ...     print(f"Cocktail prêt: {message}")
        
    Note:
        Cette fonction est thread-safe mais ne peut préparer qu'un
        cocktail à la fois. Utilisez get_preparation_status() pour
        vérifier l'état avant appel.
    """
    pass
```

## 🚀 Release Process

### 📋 Pre-Release Checklist
- [ ] Tous les tests passent
- [ ] Documentation mise à jour
- [ ] CHANGELOG.md complété
- [ ] Version bumped
- [ ] Hardware testé si applicable

### 🏷️ Version Numbering
- **MAJOR**: Breaking changes
- **MINOR**: New features
- **PATCH**: Bug fixes

Exemple: `v2.1.3`

### 📦 Release Steps
1. Créer release branch
2. Update version numbers
3. Generate changelog
4. Test complete system
5. Merge to main
6. Tag release
7. Create GitHub release

## 🤔 Questions & Support

### 💬 Où Poser des Questions
- **GitHub Issues**: Bugs et feature requests
- **GitHub Discussions**: Questions générales
- **Discord**: Chat en temps réel (si disponible)

### 📞 Contact Maintainers
- Créez une issue avec label `@maintainer`
- Pour problèmes sécurité: email privé

## 📄 License

Ce projet est sous licence MIT. Voir [LICENSE](LICENSE) pour détails.

---

**Merci de contribuer à Tipsy Elite ! Ensemble, créons la meilleure machine à cocktails Art Déco ! 🍸✨**