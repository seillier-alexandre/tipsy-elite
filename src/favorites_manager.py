# -*- coding: utf-8 -*-
"""
Gestionnaire de favoris pour la machine à cocktails Tipsy Elite
Système de favoris persistant avec synchronisation et recommandations
"""
import json
import logging
import threading
import time
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class FavoriteEntry:
    """Entrée de favori avec métadonnées"""
    cocktail_id: str
    name: str
    added_at: str
    last_ordered: Optional[str] = None
    order_count: int = 0
    rating: int = 5  # 1-5 étoiles
    tags: List[str] = None
    notes: str = ""
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

@dataclass
class UserProfile:
    """Profil utilisateur avec préférences"""
    user_id: str
    name: str
    created_at: str
    preferences: Dict[str, any] = None
    favorite_spirits: List[str] = None
    disliked_ingredients: List[str] = None
    preferred_strength: int = 3  # 1-5
    preferred_complexity: int = 3  # 1-5
    last_active: str = ""
    
    def __post_init__(self):
        if self.preferences is None:
            self.preferences = {}
        if self.favorite_spirits is None:
            self.favorite_spirits = []
        if self.disliked_ingredients is None:
            self.disliked_ingredients = []

class FavoritesManager:
    """Gestionnaire principal des favoris avec support multi-utilisateurs"""
    
    def __init__(self, data_dir: str = "config"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.favorites_file = self.data_dir / "favorites.json"
        self.profiles_file = self.data_dir / "user_profiles.json"
        
        self.favorites: Dict[str, List[FavoriteEntry]] = {}  # user_id -> favorites
        self.user_profiles: Dict[str, UserProfile] = {}
        self.current_user = "default"
        
        self._lock = threading.RLock()
        self._load_data()
    
    def _load_data(self):
        """Charge les données depuis les fichiers"""
        try:
            # Charger favoris
            if self.favorites_file.exists():
                with open(self.favorites_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for user_id, fav_data in data.items():
                    self.favorites[user_id] = [
                        FavoriteEntry(**entry) for entry in fav_data
                    ]
            
            # Charger profils utilisateurs
            if self.profiles_file.exists():
                with open(self.profiles_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for user_id, profile_data in data.items():
                    self.user_profiles[user_id] = UserProfile(**profile_data)
            
            # Créer utilisateur par défaut si nécessaire
            if "default" not in self.user_profiles:
                self.create_user_profile("default", "Utilisateur Principal")
            
            logger.info(f"Favoris chargés: {len(self.favorites)} utilisateurs")
            
        except Exception as e:
            logger.error(f"Erreur chargement favoris: {e}")
            self._create_default_data()
    
    def _create_default_data(self):
        """Crée les données par défaut"""
        self.create_user_profile("default", "Utilisateur Principal")
        self._save_data()
    
    def _save_data(self):
        """Sauvegarde les données"""
        try:
            with self._lock:
                # Sauvegarder favoris
                favorites_data = {}
                for user_id, favorites in self.favorites.items():
                    favorites_data[user_id] = [asdict(fav) for fav in favorites]
                
                with open(self.favorites_file, 'w', encoding='utf-8') as f:
                    json.dump(favorites_data, f, indent=2, ensure_ascii=False)
                
                # Sauvegarder profils
                profiles_data = {}
                for user_id, profile in self.user_profiles.items():
                    profiles_data[user_id] = asdict(profile)
                
                with open(self.profiles_file, 'w', encoding='utf-8') as f:
                    json.dump(profiles_data, f, indent=2, ensure_ascii=False)
                
                logger.debug("Données favoris sauvegardées")
                
        except Exception as e:
            logger.error(f"Erreur sauvegarde favoris: {e}")
    
    def create_user_profile(self, user_id: str, name: str) -> UserProfile:
        """Crée un nouveau profil utilisateur"""
        with self._lock:
            profile = UserProfile(
                user_id=user_id,
                name=name,
                created_at=datetime.now().isoformat(),
                last_active=datetime.now().isoformat()
            )
            
            self.user_profiles[user_id] = profile
            self.favorites[user_id] = []
            
            self._save_data()
            logger.info(f"Profil utilisateur créé: {name} ({user_id})")
            return profile
    
    def set_current_user(self, user_id: str) -> bool:
        """Définit l'utilisateur actuel"""
        if user_id in self.user_profiles:
            self.current_user = user_id
            self.user_profiles[user_id].last_active = datetime.now().isoformat()
            self._save_data()
            logger.info(f"Utilisateur actuel: {self.user_profiles[user_id].name}")
            return True
        return False
    
    def add_favorite(self, cocktail_id: str, cocktail_name: str, 
                     rating: int = 5, tags: List[str] = None, notes: str = "") -> bool:
        """Ajoute un cocktail aux favoris"""
        try:
            with self._lock:
                user_favorites = self.favorites.get(self.current_user, [])
                
                # Vérifier si déjà favori
                if any(fav.cocktail_id == cocktail_id for fav in user_favorites):
                    logger.warning(f"Cocktail {cocktail_id} déjà en favoris")
                    return False
                
                # Créer nouvelle entrée
                favorite = FavoriteEntry(
                    cocktail_id=cocktail_id,
                    name=cocktail_name,
                    added_at=datetime.now().isoformat(),
                    rating=max(1, min(5, rating)),  # Limiter 1-5
                    tags=tags or [],
                    notes=notes
                )
                
                user_favorites.append(favorite)
                self.favorites[self.current_user] = user_favorites
                
                self._save_data()
                logger.info(f"Favori ajouté: {cocktail_name} pour {self.current_user}")
                return True
                
        except Exception as e:
            logger.error(f"Erreur ajout favori: {e}")
            return False
    
    def remove_favorite(self, cocktail_id: str) -> bool:
        """Retire un cocktail des favoris"""
        try:
            with self._lock:
                user_favorites = self.favorites.get(self.current_user, [])
                
                # Trouver et supprimer
                initial_count = len(user_favorites)
                user_favorites = [fav for fav in user_favorites if fav.cocktail_id != cocktail_id]
                
                if len(user_favorites) < initial_count:
                    self.favorites[self.current_user] = user_favorites
                    self._save_data()
                    logger.info(f"Favori supprimé: {cocktail_id}")
                    return True
                else:
                    logger.warning(f"Cocktail {cocktail_id} non trouvé dans les favoris")
                    return False
                    
        except Exception as e:
            logger.error(f"Erreur suppression favori: {e}")
            return False
    
    def is_favorite(self, cocktail_id: str) -> bool:
        """Vérifie si un cocktail est en favoris"""
        user_favorites = self.favorites.get(self.current_user, [])
        return any(fav.cocktail_id == cocktail_id for fav in user_favorites)
    
    def get_favorites(self, user_id: Optional[str] = None) -> List[FavoriteEntry]:
        """Récupère les favoris d'un utilisateur"""
        target_user = user_id or self.current_user
        return self.favorites.get(target_user, []).copy()
    
    def get_favorite_ids(self, user_id: Optional[str] = None) -> List[str]:
        """Récupère les IDs des cocktails favoris"""
        favorites = self.get_favorites(user_id)
        return [fav.cocktail_id for fav in favorites]
    
    def update_favorite(self, cocktail_id: str, rating: Optional[int] = None,
                       tags: Optional[List[str]] = None, notes: Optional[str] = None) -> bool:
        """Met à jour un favori existant"""
        try:
            with self._lock:
                user_favorites = self.favorites.get(self.current_user, [])
                
                for favorite in user_favorites:
                    if favorite.cocktail_id == cocktail_id:
                        if rating is not None:
                            favorite.rating = max(1, min(5, rating))
                        if tags is not None:
                            favorite.tags = tags
                        if notes is not None:
                            favorite.notes = notes
                        
                        self._save_data()
                        return True
                
                return False
                
        except Exception as e:
            logger.error(f"Erreur mise à jour favori: {e}")
            return False
    
    def record_order(self, cocktail_id: str):
        """Enregistre une commande pour un favori"""
        try:
            with self._lock:
                user_favorites = self.favorites.get(self.current_user, [])
                
                for favorite in user_favorites:
                    if favorite.cocktail_id == cocktail_id:
                        favorite.order_count += 1
                        favorite.last_ordered = datetime.now().isoformat()
                        self._save_data()
                        break
                        
        except Exception as e:
            logger.error(f"Erreur enregistrement commande: {e}")
    
    def get_most_ordered(self, limit: int = 10) -> List[FavoriteEntry]:
        """Récupère les favoris les plus commandés"""
        favorites = self.get_favorites()
        return sorted(favorites, key=lambda x: x.order_count, reverse=True)[:limit]
    
    def get_recently_added(self, days: int = 30, limit: int = 10) -> List[FavoriteEntry]:
        """Récupère les favoris récemment ajoutés"""
        cutoff_date = datetime.now() - timedelta(days=days)
        favorites = self.get_favorites()
        
        recent = [
            fav for fav in favorites 
            if datetime.fromisoformat(fav.added_at) > cutoff_date
        ]
        
        return sorted(recent, key=lambda x: x.added_at, reverse=True)[:limit]
    
    def get_top_rated(self, limit: int = 10) -> List[FavoriteEntry]:
        """Récupère les favoris les mieux notés"""
        favorites = self.get_favorites()
        return sorted(favorites, key=lambda x: x.rating, reverse=True)[:limit]
    
    def search_favorites(self, query: str) -> List[FavoriteEntry]:
        """Recherche dans les favoris"""
        query_lower = query.lower()
        favorites = self.get_favorites()
        
        results = []
        for favorite in favorites:
            # Recherche dans nom, tags, et notes
            if (query_lower in favorite.name.lower() or
                any(query_lower in tag.lower() for tag in favorite.tags) or
                query_lower in favorite.notes.lower()):
                results.append(favorite)
        
        return results
    
    def get_favorites_by_tag(self, tag: str) -> List[FavoriteEntry]:
        """Récupère les favoris par tag"""
        favorites = self.get_favorites()
        return [fav for fav in favorites if tag.lower() in [t.lower() for t in fav.tags]]
    
    def get_all_tags(self) -> Set[str]:
        """Récupère tous les tags utilisés"""
        favorites = self.get_favorites()
        tags = set()
        for favorite in favorites:
            tags.update(favorite.tags)
        return tags
    
    def get_recommendations(self, limit: int = 5) -> List[str]:
        """Génère des recommandations basées sur les favoris"""
        try:
            # Import conditionnel pour éviter dépendance circulaire
            from cocktail_manager import get_cocktail_manager
            
            cocktail_manager = get_cocktail_manager()
            all_cocktails = cocktail_manager.database.get_all_cocktails() if cocktail_manager and cocktail_manager.database else []
            favorite_ids = self.get_favorite_ids()
            
            if not favorite_ids:
                # Pas de favoris, retourner les plus populaires
                popular = cocktail_manager.get_popular_cocktails(limit)
                return [c.id for c in popular]
            
            # Analyser les favoris pour trouver des patterns
            favorite_cocktails = [
                c for c in all_cocktails if c.id in favorite_ids
            ]
            
            # Analyser ingrédients préférés
            ingredient_scores = {}
            for cocktail in favorite_cocktails:
                for ingredient in cocktail.ingredients:
                    ingredient_scores[ingredient.name] = ingredient_scores.get(ingredient.name, 0) + 1
            
            # Scorer les cocktails non favoris
            recommendations = []
            for cocktail in all_cocktails:
                if cocktail.id not in favorite_ids and cocktail.is_makeable:
                    score = 0
                    for ingredient in cocktail.ingredients:
                        score += ingredient_scores.get(ingredient.name, 0)
                    
                    if score > 0:
                        recommendations.append((cocktail.id, score))
            
            # Trier et retourner les meilleurs
            recommendations.sort(key=lambda x: x[1], reverse=True)
            return [rec[0] for rec in recommendations[:limit]]
            
        except Exception as e:
            logger.error(f"Erreur génération recommandations: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, any]:
        """Récupère les statistiques des favoris"""
        favorites = self.get_favorites()
        
        if not favorites:
            return {
                'total_favorites': 0,
                'average_rating': 0,
                'most_common_tags': [],
                'total_orders': 0
            }
        
        # Calculer statistiques
        total_orders = sum(fav.order_count for fav in favorites)
        average_rating = sum(fav.rating for fav in favorites) / len(favorites)
        
        # Tags les plus fréquents
        tag_counts = {}
        for favorite in favorites:
            for tag in favorite.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        most_common_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_favorites': len(favorites),
            'average_rating': round(average_rating, 1),
            'most_common_tags': most_common_tags,
            'total_orders': total_orders,
            'oldest_favorite': min(favorites, key=lambda x: x.added_at).added_at if favorites else None,
            'newest_favorite': max(favorites, key=lambda x: x.added_at).added_at if favorites else None
        }
    
    def export_favorites(self, format: str = 'json') -> Optional[str]:
        """Exporte les favoris dans différents formats"""
        try:
            favorites = self.get_favorites()
            
            if format == 'json':
                data = {
                    'user': self.user_profiles[self.current_user].name,
                    'exported_at': datetime.now().isoformat(),
                    'favorites': [asdict(fav) for fav in favorites]
                }
                return json.dumps(data, indent=2, ensure_ascii=False)
            
            elif format == 'csv':
                import csv
                from io import StringIO
                
                output = StringIO()
                writer = csv.writer(output)
                
                # En-têtes
                writer.writerow([
                    'Cocktail ID', 'Name', 'Rating', 'Order Count',
                    'Added At', 'Last Ordered', 'Tags', 'Notes'
                ])
                
                # Données
                for fav in favorites:
                    writer.writerow([
                        fav.cocktail_id, fav.name, fav.rating, fav.order_count,
                        fav.added_at, fav.last_ordered, ';'.join(fav.tags), fav.notes
                    ])
                
                return output.getvalue()
            
        except Exception as e:
            logger.error(f"Erreur export favoris: {e}")
            return None
    
    def import_favorites(self, data: str, format: str = 'json') -> bool:
        """Importe des favoris depuis différents formats"""
        try:
            if format == 'json':
                import_data = json.loads(data)
                favorites_data = import_data.get('favorites', [])
                
                with self._lock:
                    for fav_data in favorites_data:
                        if not self.is_favorite(fav_data['cocktail_id']):
                            favorite = FavoriteEntry(**fav_data)
                            user_favorites = self.favorites.get(self.current_user, [])
                            user_favorites.append(favorite)
                            self.favorites[self.current_user] = user_favorites
                
                self._save_data()
                logger.info(f"Favoris importés: {len(favorites_data)} entrées")
                return True
                
        except Exception as e:
            logger.error(f"Erreur import favoris: {e}")
            return False

# Instance globale
favorites_manager = FavoritesManager()

def get_favorites_manager() -> FavoritesManager:
    """Récupère l'instance du gestionnaire de favoris"""
    return favorites_manager

if __name__ == "__main__":
    # Tests du système de favoris
    manager = get_favorites_manager()
    
    print("🌟 Test du système de favoris")
    
    # Ajouter quelques favoris de test
    manager.add_favorite("gin_tonic", "Gin Tonic", 5, ["classique", "rafraîchissant"])
    manager.add_favorite("negroni", "Negroni", 4, ["bitter", "sophistiqué"])
    manager.add_favorite("manhattan", "Manhattan", 5, ["strong", "elegant"])
    
    # Afficher favoris
    favorites = manager.get_favorites()
    print(f"📋 Favoris: {len(favorites)}")
    for fav in favorites:
        print(f"  - {fav.name} ({fav.rating}⭐) {fav.tags}")
    
    # Test recherche
    results = manager.search_favorites("gin")
    print(f"🔍 Recherche 'gin': {len(results)} résultats")
    
    # Statistiques
    stats = manager.get_statistics()
    print(f"📊 Statistiques: {stats}")
    
    print("✅ Tests terminés")