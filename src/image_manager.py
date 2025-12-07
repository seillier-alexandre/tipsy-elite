# -*- coding: utf-8 -*-
"""
Gestionnaire d'images pour machine à cocktails Tipsy Elite
Chargement, cache et gestion des images avec fallbacks Art Déco
"""
import logging
import pygame
import os
from typing import Dict, Optional, Tuple, List
from pathlib import Path
from dataclasses import dataclass
import threading
import time

logger = logging.getLogger(__name__)

@dataclass
class ImageMetadata:
    """Métadonnées d'une image"""
    path: str
    size: Tuple[int, int]
    format: str
    loaded_at: float
    access_count: int = 0
    last_access: float = 0.0

class ImageCache:
    """Cache intelligent pour images avec LRU et préchargement"""
    
    def __init__(self, max_size: int = 50, max_memory_mb: int = 100):
        self.max_size = max_size
        self.max_memory_mb = max_memory_mb
        self.cache: Dict[str, pygame.Surface] = {}
        self.metadata: Dict[str, ImageMetadata] = {}
        self._lock = threading.RLock()
        self.current_memory_mb = 0.0
    
    def get(self, key: str) -> Optional[pygame.Surface]:
        """Récupère une image du cache"""
        with self._lock:
            if key in self.cache:
                # Mettre à jour statistiques d'accès
                self.metadata[key].access_count += 1
                self.metadata[key].last_access = time.time()
                return self.cache[key]
        return None
    
    def put(self, key: str, surface: pygame.Surface, metadata: ImageMetadata):
        """Ajoute une image au cache"""
        with self._lock:
            # Calculer la taille en mémoire (approximative)
            image_size_mb = (surface.get_width() * surface.get_height() * 4) / (1024 * 1024)
            
            # Nettoyer si nécessaire
            while (len(self.cache) >= self.max_size or 
                   self.current_memory_mb + image_size_mb > self.max_memory_mb):
                self._evict_lru()
            
            self.cache[key] = surface
            self.metadata[key] = metadata
            self.current_memory_mb += image_size_mb
    
    def _evict_lru(self):
        """Évict l'image la moins récemment utilisée"""
        if not self.cache:
            return
        
        # Trouver l'image LRU
        lru_key = min(self.metadata.keys(), 
                      key=lambda k: self.metadata[k].last_access)
        
        # Calculer et soustraire la taille
        surface = self.cache[lru_key]
        image_size_mb = (surface.get_width() * surface.get_height() * 4) / (1024 * 1024)
        self.current_memory_mb -= image_size_mb
        
        # Supprimer
        del self.cache[lru_key]
        del self.metadata[lru_key]
        
        logger.debug(f"Éviction cache: {lru_key}")
    
    def clear(self):
        """Vide le cache"""
        with self._lock:
            self.cache.clear()
            self.metadata.clear()
            self.current_memory_mb = 0.0
    
    def get_stats(self) -> Dict[str, any]:
        """Statistiques du cache"""
        with self._lock:
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'memory_mb': round(self.current_memory_mb, 2),
                'max_memory_mb': self.max_memory_mb,
                'hit_rate': self._calculate_hit_rate()
            }
    
    def _calculate_hit_rate(self) -> float:
        """Calcule le taux de succès du cache"""
        if not self.metadata:
            return 0.0
        
        total_accesses = sum(meta.access_count for meta in self.metadata.values())
        return len(self.metadata) / max(1, total_accesses)

class ImageManager:
    """Gestionnaire principal des images avec Art Déco styling"""
    
    def __init__(self, base_path: str = "assets/images"):
        self.base_path = Path(base_path)
        self.cache = ImageCache()
        self.default_images = {}
        self._preload_thread = None
        self._stop_preload = False
        
        # Initialiser pygame pour les images
        if not pygame.get_init():
            pygame.init()
        
        self._load_default_images()
    
    def _load_default_images(self):
        """Charge les images par défaut"""
        default_paths = {
            'cocktail': self.base_path / "default_cocktail.png",
            'ingredient': self.base_path / "default_ingredient.png", 
            'loading': self.base_path / "loading_placeholder.png"
        }
        
        for key, path in default_paths.items():
            if path.exists():
                try:
                    surface = pygame.image.load(str(path))
                    self.default_images[key] = surface
                    logger.info(f"Image par défaut chargée: {key}")
                except Exception as e:
                    logger.error(f"Erreur chargement image par défaut {key}: {e}")
                    self.default_images[key] = self._create_fallback_image(key)
            else:
                # Créer image de fallback
                self.default_images[key] = self._create_fallback_image(key)
    
    def _create_fallback_image(self, image_type: str) -> pygame.Surface:
        """Crée une image de fallback Art Déco"""
        size = (400, 300) if image_type == 'cocktail' else (150, 150)
        surface = pygame.Surface(size, pygame.SRCALPHA)
        
        # Couleurs Art Déco
        colors = {
            'gold': (212, 175, 55),
            'bronze': (176, 141, 87),
            'charcoal': (54, 69, 79),
            'cream': (245, 235, 215)
        }
        
        # Fond charbon
        surface.fill(colors['charcoal'])
        
        # Cadre doré
        pygame.draw.rect(surface, colors['gold'], 
                        (5, 5, size[0]-10, size[1]-10), 3)
        
        # Motif central selon le type
        center = (size[0]//2, size[1]//2)
        
        if image_type == 'cocktail':
            # Forme de verre
            pygame.draw.circle(surface, colors['bronze'], 
                             (center[0], center[1]+20), 30, 3)
        elif image_type == 'ingredient':
            # Forme de bouteille
            pygame.draw.rect(surface, colors['bronze'],
                           (center[0]-15, center[1]-40, 30, 80), 3)
        
        return surface
    
    def load_image(self, image_path: str, size: Optional[Tuple[int, int]] = None, 
                   cache_key: Optional[str] = None) -> pygame.Surface:
        """Charge une image avec cache et redimensionnement"""
        # Générer clé de cache
        if cache_key is None:
            cache_key = f"{image_path}_{size}" if size else image_path
        
        # Vérifier cache
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        
        # Charger depuis disque
        full_path = self.base_path / image_path
        
        if not full_path.exists():
            logger.warning(f"Image non trouvée: {full_path}")
            return self._get_default_image('cocktail', size)
        
        try:
            surface = pygame.image.load(str(full_path))
            
            # Redimensionner si nécessaire
            if size is not None:
                surface = pygame.transform.smoothscale(surface, size)
            
            # Optimiser pour l'affichage
            if surface.get_alpha() is not None:
                surface = surface.convert_alpha()
            else:
                surface = surface.convert()
            
            # Mettre en cache
            metadata = ImageMetadata(
                path=str(full_path),
                size=surface.get_size(),
                format=full_path.suffix,
                loaded_at=time.time()
            )
            self.cache.put(cache_key, surface, metadata)
            
            logger.debug(f"Image chargée: {image_path}")
            return surface
            
        except Exception as e:
            logger.error(f"Erreur chargement image {full_path}: {e}")
            return self._get_default_image('cocktail', size)
    
    def load_cocktail_image(self, cocktail_id: str, image_type: str = 'main',
                           size: Optional[Tuple[int, int]] = None) -> pygame.Surface:
        """Charge l'image d'un cocktail spécifique"""
        # Mapping des types d'images
        type_mapping = {
            'main': f"cocktails/{cocktail_id}_main.jpg",
            'thumb': f"cocktails/thumbnails/{cocktail_id}_thumb.png", 
            'ingredients': f"cocktails/ingredients/{cocktail_id}_ingredients.jpg",
            'preparation': f"cocktails/preparation/{cocktail_id}_prep.jpg",
            'serving': f"cocktails/serving/{cocktail_id}_served.jpg"
        }
        
        image_path = type_mapping.get(image_type, type_mapping['main'])
        return self.load_image(image_path, size, f"cocktail_{cocktail_id}_{image_type}_{size}")
    
    def load_ingredient_image(self, ingredient_id: str, 
                             size: Optional[Tuple[int, int]] = None) -> pygame.Surface:
        """Charge l'image d'un ingrédient"""
        image_path = f"ingredients/{ingredient_id}.png"
        return self.load_image(image_path, size, f"ingredient_{ingredient_id}_{size}")
    
    def _get_default_image(self, image_type: str, 
                          size: Optional[Tuple[int, int]] = None) -> pygame.Surface:
        """Récupère une image par défaut redimensionnée"""
        default = self.default_images.get(image_type)
        
        if default is None:
            default = self._create_fallback_image(image_type)
        
        if size is not None and default.get_size() != size:
            return pygame.transform.smoothscale(default, size)
        
        return default
    
    def preload_cocktail_images(self, cocktail_ids: List[str], 
                               priority_types: List[str] = ['main', 'thumb']):
        """Précharge les images des cocktails en arrière-plan"""
        def preload_worker():
            for cocktail_id in cocktail_ids:
                if self._stop_preload:
                    break
                
                for image_type in priority_types:
                    if self._stop_preload:
                        break
                    
                    try:
                        self.load_cocktail_image(cocktail_id, image_type)
                        time.sleep(0.1)  # Éviter surcharge
                    except Exception as e:
                        logger.error(f"Erreur préchargement {cocktail_id}.{image_type}: {e}")
        
        if self._preload_thread and self._preload_thread.is_alive():
            self._stop_preload = True
            self._preload_thread.join(timeout=2.0)
        
        self._stop_preload = False
        self._preload_thread = threading.Thread(target=preload_worker, daemon=True)
        self._preload_thread.start()
        
        logger.info(f"Préchargement démarré pour {len(cocktail_ids)} cocktails")
    
    def get_cache_stats(self) -> Dict[str, any]:
        """Statistiques détaillées du cache"""
        stats = self.cache.get_stats()
        stats.update({
            'default_images_loaded': len(self.default_images),
            'preload_active': (self._preload_thread is not None and 
                              self._preload_thread.is_alive())
        })
        return stats
    
    def cleanup(self):
        """Nettoie les ressources"""
        if self._preload_thread and self._preload_thread.is_alive():
            self._stop_preload = True
            self._preload_thread.join(timeout=2.0)
        
        self.cache.clear()
        logger.info("ImageManager nettoyé")

# Instance globale
image_manager = ImageManager()

def get_image_manager() -> ImageManager:
    """Récupère l'instance du gestionnaire d'images"""
    return image_manager

def load_cocktail_image(cocktail_id: str, image_type: str = 'main', 
                       size: Optional[Tuple[int, int]] = None) -> pygame.Surface:
    """Fonction utilitaire pour charger image cocktail"""
    return image_manager.load_cocktail_image(cocktail_id, image_type, size)

def load_ingredient_image(ingredient_id: str, 
                         size: Optional[Tuple[int, int]] = None) -> pygame.Surface:
    """Fonction utilitaire pour charger image ingrédient"""
    return image_manager.load_ingredient_image(ingredient_id, size)

if __name__ == "__main__":
    # Test du gestionnaire d'images
    import asyncio
    
    def test_image_manager():
        print("Test ImageManager...")
        
        # Test chargement cocktail
        gin_image = load_cocktail_image('gin_tonic', 'main', (400, 300))
        print(f"✅ Image Gin Tonic chargée: {gin_image.get_size()}")
        
        # Test thumbnail
        thumb = load_cocktail_image('gin_tonic', 'thumb', (150, 150))
        print(f"✅ Miniature chargée: {thumb.get_size()}")
        
        # Test image manquante (fallback)
        missing = load_cocktail_image('cocktail_inexistant', 'main')
        print(f"✅ Fallback fonctionnel: {missing.get_size()}")
        
        # Statistiques
        stats = image_manager.get_cache_stats()
        print(f"📊 Cache: {stats}")
        
        print("🎯 ImageManager testé avec succès!")
    
    test_image_manager()