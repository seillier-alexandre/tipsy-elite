#!/usr/bin/env python3
"""
Script de nettoyage GPIO pour libérer les ressources occupées
À exécuter avant de démarrer l'interface si des GPIO restent bloqués
"""
import RPi.GPIO as GPIO
import logging

def cleanup_gpio():
    """Nettoie tous les GPIO et libère les ressources"""
    try:
        print("🧹 Nettoyage des GPIO en cours...")
        
        # Nettoyer tous les GPIO
        GPIO.cleanup()
        print("✅ GPIO nettoyés avec succès")
        
        # Réinitialiser le mode de numérotation
        GPIO.setmode(GPIO.BCM)
        print("✅ Mode GPIO BCM réinitialisé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage GPIO: {e}")
        return False

def reset_gpio_system():
    """Reset complet du système GPIO"""
    try:
        print("🔄 Reset complet du système GPIO...")
        
        # Cleanup standard
        cleanup_gpio()
        
        # Force cleanup avec warnings supprimés
        GPIO.setwarnings(False)
        GPIO.cleanup()
        GPIO.setwarnings(True)
        
        print("✅ Reset GPIO terminé")
        return True
        
    except Exception as e:
        print(f"❌ Erreur reset GPIO: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Script de nettoyage GPIO Tipsy Elite")
    print("=" * 50)
    
    # Nettoyage standard
    if cleanup_gpio():
        print("\n🎉 Nettoyage réussi ! Vous pouvez maintenant relancer l'interface.")
    else:
        print("\n⚠️  Nettoyage standard échoué, tentative de reset forcé...")
        
        # Reset forcé en cas d'échec
        if reset_gpio_system():
            print("🎉 Reset forcé réussi !")
        else:
            print("❌ Reset échoué. Redémarrez le Raspberry Pi.")
            print("Commande: sudo reboot")
    
    print("=" * 50)