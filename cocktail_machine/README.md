# 🍸 Machine à Cocktails Art Déco - Interface Kivy

> Interface sophistiquée années 1920 pour machine à cocktails automatisée  
> Design Art Déco élégant optimisé pour écran tactile rond 4"

## ✨ Caractéristiques

### 🎨 Design Art Déco Authentique
- **Interface années 1920** avec motifs géométriques dorés
- **Palette de couleurs** : or, bronze, noir charbon, crème
- **Animations fluides** : rayons de soleil, transitions élégantes  
- **Optimisé pour écran rond** 4" (480x480px)

### 🍹 Fonctionnalités Complètes
- **Menu principal** : navigation intuitive entre cocktails
- **Préparation automatique** : contrôle des pompes péristaltiques
- **Système de nettoyage** : cycles automatiques des conduites
- **Réglages avancés** : calibration, paramètres système
- **Économiseur d'écran** : animations hypnotiques Art Déco

### ⚡ Système Hardware
- **10 pompes péristaltiques** avec contrôleurs TB6612FNG
- **GPIO Raspberry Pi** pour contrôle moteurs
- **Calibration automatique** des débits
- **Sécurités intégrées** : arrêt d'urgence, timeouts

## 📋 Prérequis

### Hardware Requis
- **Raspberry Pi 4** (recommandé) ou 3B+
- **Écran tactile rond 4"** (480x480 résolution)
- **10 pompes péristaltiques** 12V
- **10 contrôleurs moteur TB6612FNG**
- **Alimentation 12V/5A** pour pompes
- **Contenants** pour spiritueux et mixers

### Software Requis
```bash
# Raspberry Pi OS (Bullseye ou Bookworm)
# Python 3.8+ avec pip
sudo apt update && sudo apt upgrade -y

# Dépendances système
sudo apt install -y python3-pip python3-dev
sudo apt install -y python3-kivy
sudo apt install -y libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev
```

## 🚀 Installation

### 1. Cloner le Projet
```bash
git clone https://github.com/user/cocktail-machine.git
cd cocktail-machine/cocktail_machine
```

### 2. Installer les Dépendances Python
```bash
pip3 install -r requirements.txt
```

### 3. Configuration Initiale
```bash
# Créer les dossiers nécessaires
mkdir -p logs assets/images/cocktails config

# Copier les images de cocktails dans assets/images/cocktails/
# Adapter config/pumps.json selon votre cablage
```

### 4. Test en Mode Démonstration
```bash
# Démarrage démo (sans hardware)
python3 main.py --demo

# Mode debug avec logs détaillés
python3 main.py --demo --debug
```

## 📱 Utilisation

### Démarrage Production (Raspberry Pi)
```bash
# Démarrage normal avec hardware
python3 main.py

# Sans hardware (simulation)
python3 main.py --no-hardware

# Résolution personnalisée
python3 main.py --resolution 800x600
```

### Navigation Interface

#### 🏠 Menu Principal
- **Grille de cocktails** avec images et détails
- **Bouton Réglages** (⚙️) pour configuration
- **Bouton Nettoyage** (🧼) pour maintenance

#### 🍸 Écran Cocktail
- **Détails du cocktail** : ingrédients, instructions
- **Préparation automatique** avec barre de progression
- **Options doses** : simple, double
- **Arrêt d'urgence** possible à tout moment

#### 🧼 Nettoyage
- **Nettoyage individuel** par pompe
- **Cycle complet** automatisé
- **Progression en temps réel**
- **Arrêt d'urgence** système

#### ⚙️ Réglages
- **Système** : luminosité, sons, nettoyage auto
- **Cocktails** : doses, timeouts
- **Hardware** : calibration pompes, vitesses
- **Sauvegarde** automatique des paramètres

#### 🌙 Économiseur d'Écran
- **Activation automatique** après 5min d'inactivité
- **Animations Art Déco** hypnotiques
- **Horloge élégante** avec date
- **Sortie sur touch** quelconque

### Raccourcis Clavier (Mode Démo)
- **Échap** : Quitter l'application
- **F11** : Basculer plein écran
- **Ctrl+S** : Forcer économiseur d'écran

## 🔧 Configuration

### Fichier config/pumps.json
Configuration détaillée des pompes avec pins GPIO, débits, calibrations :

```json
{
  "pumps": {
    "pump_1": {
      "pwm_pin": 18,
      "in1_pin": 22, 
      "in2_pin": 23,
      "ingredient": "Gin",
      "flow_rate_ml_s": 2.5,
      "calibration_factor": 1.0,
      "enabled": true
    }
  }
}
```

### Calibration des Pompes
1. **Écran Réglages** > Hardware > Pompes
2. **Placer verre vide** sous sortie pompe
3. **Démarrer versement test** (ex: 50ml)
4. **Mesurer volume réel** obtenu
5. **Saisir mesure** pour ajuster calibration
6. **Facteur automatiquement** recalculé

### Ajout de Cocktails
Modifier `config/cocktails_real.json` :
```json
{
  "id": "nouveau_cocktail",
  "name": "Nom du Cocktail",
  "ingredients": [
    {"name": "Gin", "amount_ml": 50, "category": "spirits"},
    {"name": "Sprite", "amount_ml": 100, "category": "mixers"}
  ],
  "description": "Description du cocktail",
  "category": "classic",
  "difficulty": 1,
  "glass_type": "highball"
}
```

## 🛠️ Dépannage

### Problèmes Fréquents

#### Interface ne Démarre Pas
```bash
# Vérifier installation Kivy
python3 -c "import kivy; print(kivy.__version__)"

# Tester en mode démo
python3 main.py --demo --debug
```

#### Pompes ne Répondent Pas
```bash
# Vérifier permissions GPIO
sudo usermod -a -G gpio $USER

# Tester contrôleurs TB6612
python3 -c "from hardware.pumps import *; test_pump_system()"
```

#### Écran Tactile non Détecté
```bash
# Configuration dans ~/.kivy/config.ini
[input]
mouse = mouse,disable_multitouch
mtdev = probesysfs,provider=mtdev

# Redémarrer après changement
```

### Logs et Debug
```bash
# Consulter logs d'erreurs
tail -f logs/cocktail_machine.log

# Mode debug complet
python3 main.py --demo --debug

# Test modules individuels
python3 -m screens.menu  # Test écran menu
python3 -m hardware.pumps  # Test système pompes
```

## 🎯 Développement

### Structure du Projet
```
cocktail_machine/
├── main.py              # Application principale
├── screens/             # Écrans Kivy
│   ├── menu.py         # Menu principal
│   ├── cocktail.py     # Détail cocktail
│   ├── cleaning.py     # Nettoyage
│   ├── settings.py     # Réglages  
│   └── screensaver.py  # Économiseur
├── hardware/           # Contrôle hardware
│   └── pumps.py       # Système pompes GPIO
├── utils/             # Utilitaires
│   └── round_display.py # Support écran rond
├── theme/             # Style Art Déco
│   └── deco.kv        # Thème Kivy
└── config/            # Configurations
    ├── pumps.json     # Config pompes
    └── settings.json  # Paramètres app
```

### Ajout d'un Nouvel Écran
1. Créer `screens/nouvel_ecran.py`
2. Hériter de `RoundScreen`
3. Implémenter `_build_interface()`
4. Ajouter dans `main.py`

### Personnalisation du Thème
Modifier `theme/deco.kv` pour adapter :
- **Couleurs** : variables DECO_GOLD, DECO_BLACK...
- **Motifs** : lignes géométriques, bordures
- **Animations** : rotations, fades, glissements

## 📈 Performances

### Optimisations Appliquées
- **Lazy loading** des images cocktails
- **Cache intelligent** avec LRU
- **Animations 30 FPS** optimisées  
- **Threads séparés** pour hardware
- **Cleanup automatique** ressources

### Monitoring
```bash
# Utilisation RAM/CPU
htop

# Logs performance
grep "PERF" logs/cocktail_machine.log

# Profiling Python
python3 -m cProfile main.py --demo
```

## 🔒 Sécurité

### Mesures Intégrées
- **Timeouts** sur toutes opérations pompes
- **Volume maximum** par cocktail (300ml)
- **Arrêt d'urgence** accessible partout
- **Validation** des volumes saisis
- **Nettoyage obligatoire** après usage

### Configuration Sécurité
Dans `config/pumps.json`, section "safety" :
```json
{
  "safety": {
    "max_volume_per_cocktail": 300.0,
    "max_alcohol_per_cocktail": 150.0,
    "pump_timeout": 30.0,
    "emergency_stop_pins": [31, 33]
  }
}
```

## 📞 Support

### Communauté
- **Issues GitHub** : Rapporter bugs/demandes
- **Discussions** : Partager configurations
- **Wiki** : Documentation collaborative

### Contribution
1. **Fork** le projet
2. **Créer branche** feature/amelioration
3. **Commit** avec messages clairs
4. **Pull Request** avec description

## 🏆 Licence

Ce projet est sous licence **MIT** - voir fichier [LICENSE](LICENSE) pour détails.

---

## 🎭 Art Déco Credits

**Inspiration** : Mouvement artistique années 1920-1930  
**Palette** : Chrysler Building, Empire State Building  
**Motifs** : Géométrie, rayons de soleil, lignes droites  
**Élégance** : Prohibition era sophistication  

> *"L'Art Déco représente la modernité élégante et l'optimisme des années folles"*

---

**🍸 Santé ! Dégustez avec modération ! 🍸**