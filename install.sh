#!/bin/bash
# Script d'installation automatique pour Tipsy Elite

set -e

echo "[INSTALL] Installation de Tipsy Elite"

# Détecter l'utilisateur et le répertoire
USER_NAME=$(whoami)
INSTALL_DIR=$(pwd)

echo "[INFO] Utilisateur: $USER_NAME"
echo "[INFO] Répertoire: $INSTALL_DIR"

# Installer les dépendances
echo "[INSTALL] Installation des dépendances..."
sudo apt update
sudo apt install -y python3-pygame python3-rpi.gpio python3-spidev python3-pip

# Installer les packages Python (si dans un venv)
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "[INFO] Environnement virtuel détecté: $VIRTUAL_ENV"
    pip install pygame RPi.GPIO spidev
else
    echo "[INFO] Installation système des packages Python"
    # Les packages sont déjà installés via apt
fi

# Créer le service systemd
echo "[INSTALL] Création du service systemd..."
sudo tee /etc/systemd/system/tipsy-elite.service > /dev/null << EOF
[Unit]
Description=Tipsy Elite Cocktail Machine
After=network.target

[Service]
Type=simple
User=$USER_NAME
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python src/main.py
Restart=always
RestartSec=10
Environment=DISPLAY=:0

[Install]
WantedBy=multi-user.target
EOF

# Configurer l'auto-login
echo "[INSTALL] Configuration auto-login..."
sudo systemctl set-default graphical.target
sudo systemctl enable lightdm.service

# Configurer l'auto-login pour l'utilisateur
sudo mkdir -p /etc/lightdm/lightdm.conf.d/
sudo tee /etc/lightdm/lightdm.conf.d/12-autologin.conf > /dev/null << EOF
[Seat:*]
autologin-user=$USER_NAME
autologin-user-timeout=0
EOF

# Créer le script de démarrage automatique
mkdir -p /home/$USER_NAME/.config/autostart
tee /home/$USER_NAME/.config/autostart/tipsy-elite.desktop > /dev/null << EOF
[Desktop Entry]
Type=Application
Name=Tipsy Elite
Exec=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/src/main.py
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF

# Ne pas activer le service systemd (on utilise autostart à la place)
echo "[INSTALL] Configuration du démarrage graphique..."
sudo systemctl daemon-reload

# Créer le script de gestion
echo "[INSTALL] Création des scripts de gestion..."
tee tipsy-control.sh > /dev/null << EOF
#!/bin/bash
case "\$1" in
    start)
        sudo systemctl start tipsy-elite.service
        echo "Tipsy Elite démarré"
        ;;
    stop)
        sudo systemctl stop tipsy-elite.service
        echo "Tipsy Elite arrêté"
        ;;
    restart)
        sudo systemctl restart tipsy-elite.service
        echo "Tipsy Elite redémarré"
        ;;
    status)
        sudo systemctl status tipsy-elite.service
        ;;
    logs)
        sudo journalctl -u tipsy-elite.service -f
        ;;
    *)
        echo "Usage: \$0 {start|stop|restart|status|logs}"
        exit 1
        ;;
esac
EOF

chmod +x tipsy-control.sh

echo "[OK] Installation terminée !"
echo ""
echo "Commandes disponibles :"
echo "  ./tipsy-control.sh start   - Démarrer le service"
echo "  ./tipsy-control.sh stop    - Arrêter le service"  
echo "  ./tipsy-control.sh restart - Redémarrer le service"
echo "  ./tipsy-control.sh status  - Voir le statut"
echo "  ./tipsy-control.sh logs    - Voir les logs"
echo ""
echo "Pour démarrer maintenant : ./tipsy-control.sh start"
echo "Le service démarrera automatiquement au prochain boot."