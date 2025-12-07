#!/bin/bash
# Script d'installation du service auto-start pour machine à cocktails
# Utilisation: sudo ./install_service.sh

set -e

echo "🍸 Installation du service auto-start Cocktail Machine..."

# Variables
SERVICE_NAME="cocktail-machine"
SERVICE_FILE="${SERVICE_NAME}.service"
SYSTEMD_DIR="/etc/systemd/system"
PROJECT_DIR="/home/pi/cocktail.bzh"

# Vérifications préalables
if [ "$EUID" -ne 0 ]; then
    echo "❌ Ce script doit être exécuté avec sudo"
    exit 1
fi

if [ ! -f "$SERVICE_FILE" ]; then
    echo "❌ Fichier service non trouvé: $SERVICE_FILE"
    exit 1
fi

if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ Répertoire projet non trouvé: $PROJECT_DIR"
    exit 1
fi

# Vérifier que l'utilisateur pi existe
if ! id "pi" &>/dev/null; then
    echo "❌ Utilisateur 'pi' non trouvé"
    exit 1
fi

echo "✅ Vérifications préalables OK"

# Copier le fichier service
echo "📁 Installation du service..."
cp "$SERVICE_FILE" "$SYSTEMD_DIR/"
chmod 644 "$SYSTEMD_DIR/$SERVICE_FILE"

# Recharger systemd
echo "🔄 Rechargement systemd..."
systemctl daemon-reload

# Activer le service
echo "🚀 Activation du service..."
systemctl enable "$SERVICE_NAME"

# Afficher le statut
echo "📊 Statut du service:"
systemctl status "$SERVICE_NAME" --no-pager || true

echo ""
echo "✅ Installation terminée!"
echo ""
echo "Commandes utiles:"
echo "  - Démarrer:        sudo systemctl start $SERVICE_NAME"
echo "  - Arrêter:         sudo systemctl stop $SERVICE_NAME" 
echo "  - Redémarrer:      sudo systemctl restart $SERVICE_NAME"
echo "  - Voir les logs:   sudo journalctl -u $SERVICE_NAME -f"
echo "  - Désactiver:      sudo systemctl disable $SERVICE_NAME"
echo ""
echo "🔧 Le service démarrera automatiquement au prochain boot"
echo "📝 Pour tester maintenant: sudo systemctl start $SERVICE_NAME"