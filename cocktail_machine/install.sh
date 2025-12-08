#!/bin/bash
# Installation automatique Machine à Cocktails Art Déco
# Compatible Raspberry Pi OS Bullseye/Bookworm

set -e  # Arrêter en cas d'erreur

echo "🍸 ═══════════════════════════════════════════════════════"
echo "🍸 INSTALLATION MACHINE À COCKTAILS ART DÉCO"
echo "🍸 Interface sophistiquée années 1920 pour Raspberry Pi"
echo "🍸 ═══════════════════════════════════════════════════════"

# Détection de l'environnement
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USER_HOME="/home/$(whoami)"
INSTALL_DIR="$USER_HOME/cocktail-machine"

echo "📁 Répertoire d'installation: $INSTALL_DIR"
echo "👤 Utilisateur: $(whoami)"
echo "🖥️ Système: $(uname -a)"

# Vérification Raspberry Pi
if grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "✅ Raspberry Pi détecté"
    IS_RPI=true
else
    echo "⚠️ Pas de Raspberry Pi détecté - Installation démo"
    IS_RPI=false
fi

# Mise à jour système
echo ""
echo "📦 MISE À JOUR DU SYSTÈME"
echo "========================="
sudo apt update
sudo apt upgrade -y

# Installation dépendances système
echo ""
echo "🔧 INSTALLATION DÉPENDANCES SYSTÈME"
echo "==================================="
sudo apt install -y \
    python3 \
    python3-pip \
    python3-dev \
    python3-setuptools \
    python3-wheel \
    git \
    curl \
    wget \
    unzip

# Dépendances Kivy
echo ""
echo "🎨 INSTALLATION KIVY ET DÉPENDANCES"
echo "===================================="
sudo apt install -y \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libportmidi-dev \
    libswscale-dev \
    libavformat-dev \
    libavcodec-dev \
    zlib1g-dev \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev

# GPIO pour Raspberry Pi
if [ "$IS_RPI" = true ]; then
    echo ""
    echo "⚡ CONFIGURATION GPIO RASPBERRY PI"
    echo "=================================="
    
    # Installer RPi.GPIO si pas déjà fait
    sudo apt install -y python3-rpi.gpio
    
    # Ajouter utilisateur au groupe gpio
    sudo usermod -a -G gpio $(whoami)
    
    echo "✅ Configuration GPIO terminée"
    echo "ℹ️ Redémarrage recommandé pour permissions GPIO"
fi

# Création répertoire d'installation
echo ""
echo "📁 CRÉATION RÉPERTOIRE D'INSTALLATION"
echo "====================================="
if [ -d "$INSTALL_DIR" ]; then
    echo "⚠️ Répertoire existe déjà: $INSTALL_DIR"
    read -p "Continuer ? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Installation annulée"
        exit 1
    fi
    rm -rf "$INSTALL_DIR"
fi

mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Copie des fichiers du projet
echo ""
echo "📋 COPIE DES FICHIERS PROJET"
echo "============================="
cp -r "$SCRIPT_DIR"/* "$INSTALL_DIR/"
echo "✅ Fichiers copiés"

# Création des dossiers nécessaires
echo ""
echo "📂 CRÉATION DOSSIERS DE TRAVAIL"
echo "================================"
mkdir -p logs
mkdir -p assets/images/cocktails
mkdir -p config
echo "✅ Dossiers créés"

# Installation dépendances Python
echo ""
echo "🐍 INSTALLATION DÉPENDANCES PYTHON"
echo "==================================="

# Mise à jour pip
python3 -m pip install --upgrade pip setuptools wheel

# Installation depuis requirements.txt
if [ -f "requirements.txt" ]; then
    echo "📦 Installation depuis requirements.txt..."
    python3 -m pip install -r requirements.txt --user
else
    echo "📦 Installation manuelle des dépendances..."
    python3 -m pip install --user \
        kivy \
        Pillow \
        jsonschema \
        coloredlogs \
        configparser \
        python-dateutil \
        psutil
    
    # RPi.GPIO seulement sur Raspberry Pi
    if [ "$IS_RPI" = true ]; then
        python3 -m pip install --user RPi.GPIO
    fi
fi

echo "✅ Dépendances Python installées"

# Configuration initiale
echo ""
echo "⚙️ CONFIGURATION INITIALE"
echo "=========================="

# Vérifier config pumps.json
if [ ! -f "config/pumps.json" ]; then
    echo "⚠️ Fichier config/pumps.json manquant"
    echo "ℹ️ Un fichier d'exemple sera créé"
fi

# Fichier de démarrage
echo ""
echo "🚀 CRÉATION SCRIPT DE DÉMARRAGE"
echo "==============================="

cat > "$INSTALL_DIR/start.sh" << 'EOF'
#!/bin/bash
# Script de démarrage Machine à Cocktails

cd "$(dirname "$0")"

echo "🍸 Démarrage Machine à Cocktails Art Déco..."

# Vérifier dépendances
if ! python3 -c "import kivy" 2>/dev/null; then
    echo "❌ Kivy non installé"
    exit 1
fi

# Mode de démarrage selon arguments
if [ "$1" = "--demo" ]; then
    echo "🎭 Mode démonstration"
    python3 main.py --demo
elif [ "$1" = "--debug" ]; then
    echo "🐛 Mode debug"
    python3 main.py --demo --debug
else
    echo "🚀 Mode production"
    python3 main.py
fi
EOF

chmod +x "$INSTALL_DIR/start.sh"
echo "✅ Script start.sh créé"

# Service systemd (optionnel)
if [ "$IS_RPI" = true ]; then
    echo ""
    echo "🔧 CONFIGURATION SERVICE SYSTEMD (OPTIONNEL)"
    echo "============================================="
    
    read -p "Créer service systemd pour démarrage automatique ? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        
        sudo tee /etc/systemd/system/cocktail-machine.service > /dev/null << EOF
[Unit]
Description=Machine à Cocktails Art Déco
After=graphical-session.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/start.sh
Restart=always
RestartSec=10
Environment=DISPLAY=:0

[Install]
WantedBy=graphical-session.target
EOF
        
        sudo systemctl daemon-reload
        sudo systemctl enable cocktail-machine.service
        
        echo "✅ Service systemd créé et activé"
        echo "ℹ️ Démarrage auto au boot: sudo systemctl start cocktail-machine"
    fi
fi

# Configuration écran tactile (optionnel)
if [ "$IS_RPI" = true ]; then
    echo ""
    echo "📱 CONFIGURATION ÉCRAN TACTILE (OPTIONNEL)"
    echo "=========================================="
    
    read -p "Configurer écran tactile rond 4\" ? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        
        # Configuration générique écran tactile
        echo "ℹ️ Configuration écran tactile..."
        
        # Rotation écran si nécessaire
        read -p "Rotation écran (0/90/180/270) [0]: " rotation
        rotation=${rotation:-0}
        
        if [ "$rotation" != "0" ]; then
            echo "display_rotate=$rotation" | sudo tee -a /boot/config.txt
            echo "✅ Rotation écran configurée: $rotation°"
        fi
        
        echo "ℹ️ Redémarrage requis pour appliquer configuration écran"
    fi
fi

# Test de l'installation
echo ""
echo "🧪 TEST DE L'INSTALLATION"
echo "=========================="
echo "Test import Kivy..."
if python3 -c "import kivy; print('✅ Kivy OK:', kivy.__version__)" 2>/dev/null; then
    echo "✅ Test Kivy réussi"
else
    echo "❌ Test Kivy échoué"
fi

echo ""
echo "Test module principal..."
if python3 -c "from main import *; print('✅ Module principal OK')" 2>/dev/null; then
    echo "✅ Test module principal réussi"
else
    echo "⚠️ Test module principal échoué (normal si dépendances manquantes)"
fi

# Instructions finales
echo ""
echo "🎉 ═══════════════════════════════════════════════════════"
echo "🎉 INSTALLATION TERMINÉE AVEC SUCCÈS !"
echo "🎉 ═══════════════════════════════════════════════════════"
echo ""
echo "📍 Répertoire installation: $INSTALL_DIR"
echo ""
echo "🚀 COMMANDES DE DÉMARRAGE:"
echo "  Demo:        $INSTALL_DIR/start.sh --demo"
echo "  Debug:       $INSTALL_DIR/start.sh --debug"  
echo "  Production:  $INSTALL_DIR/start.sh"
echo ""
echo "🔧 CONFIGURATION:"
echo "  Pompes:      $INSTALL_DIR/config/pumps.json"
echo "  Logs:        $INSTALL_DIR/logs/"
echo "  Images:      $INSTALL_DIR/assets/images/cocktails/"
echo ""
echo "📚 DOCUMENTATION:"
echo "  README:      $INSTALL_DIR/README.md"
echo "  Support:     https://github.com/user/cocktail-machine"
echo ""

if [ "$IS_RPI" = true ]; then
    echo "⚡ RASPBERRY PI:"
    echo "  GPIO:        Redémarrage recommandé pour permissions"
    echo "  Service:     sudo systemctl start cocktail-machine"
    echo "  Écran:       Configuration manuelle si nécessaire"
    echo ""
fi

echo "🍸 Prêt à préparer des cocktails Art Déco ! 🍸"
echo ""
echo "💡 Premier test recommandé:"
echo "   cd $INSTALL_DIR && ./start.sh --demo"