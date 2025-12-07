# 🍸 Tipsy Elite - Machine à Cocktails Années 1920

Une machine à cocktails automatisée avec interface Art Déco sophistiquée, conçue pour Raspberry Pi avec contrôleurs TB6612FNG et écran tactile rond.

## ✨ Caractéristiques

### 🎨 Interface Utilisateur
- **Design Art Déco authentique années 1920**
- **Écran tactile rond optimisé**
- **Animations fluides et transitions élégantes**
- **Palette de couleurs prohibition (or, bordeaux, noir)**
- **Typographie period-appropriate**

### ⚙️ Hardware
- **Raspberry Pi** (toutes versions récentes supportées)
- **6x Contrôleurs TB6612FNG** (12 pompes péristaltiques)
- **Écran tactile rond 800x800px**
- **Pompes péristaltiques haute précision**
- **Capteurs de niveau et débit**
- **Système de nettoyage intégré**

### 🍹 Fonctionnalités Cocktails
- **Base de données de cocktails classiques**
- **Recettes années 1920 authentiques**
- **Système de dosage précis**
- **Gestion automatique des ingrédients**
- **Favoris et recommandations**
- **Historique des préparations**

### 🧼 Nettoyage Automatique
- **Cycles de nettoyage programmés**
- **Nettoyage rapide entre cocktails**
- **Nettoyage approfondi périodique**
- **Désinfection automatique**
- **Maintenance prédictive**

## 🚀 Installation

### Prérequis
```bash
# Raspberry Pi OS (recommandé: Bullseye ou plus récent)
# Python 3.8+
# Git

# Mise à jour système
sudo apt update && sudo apt upgrade -y

# Dépendances système
sudo apt install -y python3-pip python3-venv python3-dev
sudo apt install -y libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev
sudo apt install -y libfreetype6-dev libjpeg-dev libpng-dev
```

### Installation
```bash
# Cloner le repository
git clone https://github.com/votre-username/cocktail.bzh.git
cd cocktail.bzh

# Créer environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Configuration permissions GPIO (Raspberry Pi)
sudo usermod -a -G gpio $USER
```

### Configuration Hardware

1. **Connexions TB6612FNG**
   - Voir `src/hardware_config.py` pour le mapping des pins
   - 6 contrôleurs TB6612FNG pour 12 pompes
   - Alimentation 12V pour les pompes

2. **Écran Tactile**
   - Configuration automatique pour écran rond 800x800
   - Calibrage tactile dans les paramètres

3. **Pompes Péristaltiques**
   - Débit nominal: 2.5-3.5 ml/s selon l'ingrédient
   - Calibrage individuel automatique

## 📖 Utilisation

### Démarrage
```bash
# Mode normal (avec hardware)
python src/main.py

# Mode démo (sans hardware)
python src/main.py --demo

# Mode debug
python src/main.py --debug

# Mode asynchrone
python src/main.py --async
```

### Navigation
- **Écran d'accueil**: Splash automatique avec branding
- **Menu principal**: Cocktails, Nettoyage, Paramètres
- **Sélection cocktails**: Interface circulaire intuitive
- **Préparation**: Progression en temps réel
- **Nettoyage**: Cycles automatiques et manuels

### Configuration
```bash
# Fichiers de configuration dans config/
├── cocktails.json      # Base de données cocktails
├── pump_config.json    # Configuration pompes
├── settings.json       # Paramètres système
└── cleaning_history.json  # Historique nettoyage
```

## 🔧 Architecture Technique

### Structure du Code
```
src/
├── main.py                 # Point d'entrée principal
├── hardware_config.py      # Configuration hardware
├── tb6612_controller.py    # Contrôleur pompes TB6612FNG
├── art_deco_interface.py   # Interface utilisateur
├── cocktail_manager.py     # Gestion cocktails et recettes
└── cleaning_system.py     # Système de nettoyage
```

### Modules Principaux

#### Hardware Controller (`tb6612_controller.py`)
- Gestion des 6 contrôleurs TB6612FNG
- Contrôle PWM précis des pompes
- Sécurité et monitoring en temps réel
- Gestion des erreurs et récupération

#### Cocktail Manager (`cocktail_manager.py`)
- Base de données de recettes sophistiquée
- Algorithme de dosage précis
- Système de recommandations
- Gestion des favoris et historique

#### Interface Art Déco (`art_deco_interface.py`)
- Rendu Pygame optimisé pour écran rond
- Animations et transitions fluides
- Système d'événements tactiles
- Design responsive et élégant

#### Cleaning System (`cleaning_system.py`)
- Cycles de nettoyage automatisés
- Planification intelligente
- Monitoring de l'état sanitaire
- Maintenance prédictive

## 🎯 Cocktails Disponibles

### Classiques Années 1920
- **Old Fashioned** - Le roi des cocktails prohibition
- **Gin Fizz** - Rafraîchissant et élégant
- **Sidecar** - Sophistication parisienne
- **Bee's Knees** - Douceur prohibition
- **Whiskey Sour** - Équilibre parfait
- **Manhattan** - Puissance new-yorkaise

### Fonctionnalités Avancées
- Dosage précis au millilitre
- Adaptation aux préférences (fort/doux)
- Suggestions basées sur les ingrédients disponibles
- Mode "découverte" pour nouveaux cocktails

## 🧼 Système de Nettoyage

### Cycles Automatiques
- **Quick**: Rinçage rapide entre cocktails (25s)
- **Standard**: Nettoyage quotidien complet (90s)
- **Deep**: Maintenance hebdomadaire (5min)
- **Sanitize**: Désinfection ciblée (50s)

### Maintenance Prédictive
- Surveillance des performances
- Alertes de maintenance
- Historique complet
- Planification automatique

## 🔒 Sécurité

### Hardware
- Arrêt d'urgence immédiat
- Protection contre les fuites
- Monitoring température/pression
- Validation des commandes

### Software
- Gestion d'erreurs robuste
- Logs détaillés
- Récupération automatique
- Mode dégradé sécurisé

## 🛠️ Développement

### Tests
```bash
# Tests unitaires
pytest tests/ -v

# Tests d'intégration
pytest tests/integration/ -v

# Tests hardware (Raspberry Pi uniquement)
pytest tests/hardware/ -v
```

### Contribution
1. Fork le projet
2. Créer une branche feature
3. Commits conventionnels
4. Tests complets
5. Pull request

### Standards Code
- **Black** pour le formatage
- **Type hints** obligatoires
- **Docstrings** pour toutes les fonctions
- **Tests** pour toute nouvelle fonctionnalité

## 📊 Monitoring

### Métriques Disponibles
- Nombre de cocktails préparés
- Temps de préparation moyen
- État des pompes
- Historique des nettoyages
- Consommation par ingrédient

### Logs
```bash
# Logs système dans logs/
├── tipsy.log           # Log principal
├── hardware.log        # Events hardware
├── cleaning.log        # Cycles de nettoyage
└── errors.log          # Erreurs système
```

## 🎨 Personnalisation

### Interface
- Modification des couleurs dans `art_deco_interface.py`
- Animations personnalisables
- Textes et langues configurables

### Cocktails
- Ajouter nouvelles recettes via l'interface
- Import/export de bases de données
- Calibrage des proportions

## 📞 Support

### Problèmes Courants
1. **Pompes ne fonctionnent pas**: Vérifier connexions GPIO
2. **Interface lente**: Optimiser configuration Raspberry Pi
3. **Nettoyage bloqué**: Mode manuel disponible
4. **Écran tactile non-responsif**: Calibrage dans paramètres

### Diagnostics
```bash
# Test complet du système
python src/main.py --test

# Vérification hardware
python -c "from src.hardware_config import HardwareValidator; HardwareValidator().validate_gpio_configuration()"

# Test des pompes
python -c "from src.tb6612_controller import pump_manager; pump_manager.initialize()"
```

## 📄 Licence

Ce projet est sous licence MIT. Voir `LICENSE` pour plus de détails.

## 🙏 Remerciements

- **Concept-Bytes/Tipsy** - Inspiration originale
- **Communauté Raspberry Pi** - Support technique
- **Art Déco Movement** - Inspiration design
- **Prohibition Era** - Authenticité historique

---

*Créé avec passion pour l'art du cocktail et l'élégance des années 1920* 🥃✨