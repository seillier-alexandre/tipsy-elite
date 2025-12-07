# Auto-Start Configuration - Machine à Cocktails Tipsy Elite

## Configuration du démarrage automatique sur Raspberry Pi

Cette configuration permet à la machine à cocktails de démarrer automatiquement au boot du Raspberry Pi.

### 🔧 Installation

1. **Copier les fichiers sur le Raspberry Pi** :
```bash
# Copier le projet dans le répertoire home de l'utilisateur pi
sudo cp -r /path/to/cocktail.bzh /home/pi/
sudo chown -R pi:pi /home/pi/cocktail.bzh
```

2. **Installer le service systemd** :
```bash
cd /home/pi/cocktail.bzh
sudo ./install_service.sh
```

### 🚀 Commandes de contrôle

```bash
# Démarrer le service
sudo systemctl start cocktail-machine

# Arrêter le service
sudo systemctl stop cocktail-machine

# Redémarrer le service
sudo systemctl restart cocktail-machine

# Voir le statut
sudo systemctl status cocktail-machine

# Voir les logs en temps réel
sudo journalctl -u cocktail-machine -f

# Désactiver le démarrage automatique
sudo systemctl disable cocktail-machine

# Réactiver le démarrage automatique
sudo systemctl enable cocktail-machine
```

### 📁 Fichiers créés

- `cocktail-machine.service` : Fichier de service systemd
- `install_service.sh` : Script d'installation automatique
- `src/main.py` : Point d'entrée principal (rendu exécutable)

### ⚙️ Configuration du service

Le service est configuré pour :

- **Utilisateur** : `pi`
- **Répertoire de travail** : `/home/pi/cocktail.bzh`
- **Démarrage** : Après le réseau et l'interface graphique
- **Redémarrage** : Automatique en cas d'erreur
- **Groupes** : Accès aux GPIO, SPI, I2C
- **Variables d'environnement** : Configuration pour écran tactile

### 🔍 Dépannage

**Le service ne démarre pas :**
```bash
# Vérifier les logs d'erreur
sudo journalctl -u cocktail-machine -n 50

# Vérifier la configuration
sudo systemctl cat cocktail-machine

# Tester le démarrage manuel
cd /home/pi/cocktail.bzh
./src/main.py
```

**Problèmes de permissions GPIO :**
```bash
# Ajouter l'utilisateur pi aux groupes nécessaires
sudo usermod -a -G gpio,spi,i2c pi

# Redémarrer le système
sudo reboot
```

**Problèmes d'affichage :**
```bash
# Vérifier la variable DISPLAY
echo $DISPLAY

# Configurer l'affichage pour l'utilisateur pi
export DISPLAY=:0
```

### 🎯 Fonctionnalités

- **Démarrage automatique** au boot du Raspberry Pi
- **Interface tactile** Art Déco complète
- **Gestion des 12 pompes** avec TB6612FNG
- **Système de cocktails** avec vraies images
- **Nettoyage automatique** programmé
- **Logs détaillés** via journalctl
- **Arrêt propre** via signaux système

### 🔧 Customisation

Pour modifier la configuration du service :

1. Éditer le fichier service :
```bash
sudo nano /etc/systemd/system/cocktail-machine.service
```

2. Recharger systemd :
```bash
sudo systemctl daemon-reload
```

3. Redémarrer le service :
```bash
sudo systemctl restart cocktail-machine
```

### 💡 Notes importantes

- Le service attend 10 secondes avant de démarrer pour laisser le système se stabiliser
- L'interface utilise SDL pour l'affichage sur écran tactile
- Les logs sont sauvegardés dans `/tmp/cocktail_machine.log` et accessibles via `journalctl`
- Le système de pompes est initialisé avec validation complète de la configuration GPIO