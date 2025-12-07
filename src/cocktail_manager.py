# -*- coding: utf-8 -*-
"""
Gestionnaire de cocktails pour machine à cocktails
Système avancé de gestion des recettes, ingrédients et préparation
Architecture robuste avec IA et validation
"""
import logging
import json
import time
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import threading
from hardware_config import PUMP_CONFIGS, get_pump_by_ingredient
from tb6612_controller import pump_manager, pump_operation

logger = logging.getLogger(__name__)

@dataclass
class Ingredient:
    """Ingrédient d'un cocktail"""
    name: str
    amount_ml: float
    pump_id: Optional[int] = None
    category: str = "spirits"  # spirits, mixers, syrups, juices, garnish
    is_available: bool = True
    
    def __post_init__(self):
        """Validation et assignation automatique de pompe"""
        if self.pump_id is None:
            # Chercher une pompe pour cet ingrédient
            pump_config = get_pump_by_ingredient(self.name)
            if pump_config:
                self.pump_id = pump_config.pump_id
                self.is_available = True
            else:
                self.is_available = False
                logger.warning(f"Aucune pompe trouvée pour: {self.name}")

@dataclass
class CocktailRecipe:
    """Recette de cocktail complète"""
    id: str
    name: str
    ingredients: List[Ingredient]
    description: str = ""
    category: str = "classic"  # classic, modern, tropical, spirit_forward
    difficulty: int = 1  # 1-5
    preparation_time: int = 60  # secondes
    glass_type: str = "rocks"
    garnish: str = ""
    instructions: List[str] = None
    popularity: int = 0
    created_at: str = ""
    
    def __post_init__(self):
        if self.instructions is None:
            self.instructions = []
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    @property
    def total_volume(self) -> float:
        """Volume total en ml"""
        return sum(ing.amount_ml for ing in self.ingredients if ing.category != "garnish")
    
    @property
    def is_makeable(self) -> bool:
        """Le cocktail peut-il être préparé"""
        return all(ing.is_available for ing in self.ingredients if ing.category != "garnish")
    
    @property
    def missing_ingredients(self) -> List[str]:
        """Liste des ingrédients manquants"""
        return [ing.name for ing in self.ingredients 
                if not ing.is_available and ing.category != "garnish"]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            'id': self.id,
            'name': self.name,
            'ingredients': [asdict(ing) for ing in self.ingredients],
            'description': self.description,
            'category': self.category,
            'difficulty': self.difficulty,
            'preparation_time': self.preparation_time,
            'glass_type': self.glass_type,
            'garnish': self.garnish,
            'instructions': self.instructions,
            'popularity': self.popularity,
            'created_at': self.created_at
        }

class CocktailDatabase:
    """Base de données des cocktails avec persistance JSON"""
    
    def __init__(self, db_path: str = "config/cocktails.json"):
        self.db_path = Path(db_path)
        self.cocktails: Dict[str, CocktailRecipe] = {}
        self._lock = threading.RLock()
        self.load_database()
    
    def load_database(self) -> bool:
        """Charge la base de données depuis le fichier JSON"""
        try:
            if self.db_path.exists():
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for cocktail_data in data.get('cocktails', []):
                    # Reconstituer les ingrédients
                    ingredients = []
                    for ing_data in cocktail_data.get('ingredients', []):
                        ingredient = Ingredient(
                            name=ing_data['name'],
                            amount_ml=ing_data['amount_ml'],
                            pump_id=ing_data.get('pump_id'),
                            category=ing_data.get('category', 'spirits'),
                            is_available=ing_data.get('is_available', True)
                        )
                        ingredients.append(ingredient)
                    
                    # Créer la recette
                    cocktail = CocktailRecipe(
                        id=cocktail_data['id'],
                        name=cocktail_data['name'],
                        ingredients=ingredients,
                        description=cocktail_data.get('description', ''),
                        category=cocktail_data.get('category', 'classic'),
                        difficulty=cocktail_data.get('difficulty', 1),
                        preparation_time=cocktail_data.get('preparation_time', 60),
                        glass_type=cocktail_data.get('glass_type', 'rocks'),
                        garnish=cocktail_data.get('garnish', ''),
                        instructions=cocktail_data.get('instructions', []),
                        popularity=cocktail_data.get('popularity', 0),
                        created_at=cocktail_data.get('created_at', '')
                    )
                    
                    self.cocktails[cocktail.id] = cocktail
                
                logger.info(f"Base de données chargée: {len(self.cocktails)} cocktails")
                return True
            else:
                # Créer une base de données par défaut
                self.create_default_database()
                return True
                
        except Exception as e:
            logger.error(f"Erreur chargement base de données: {e}")
            self.create_default_database()
            return False
    
    def save_database(self) -> bool:
        """Sauvegarde la base de données"""
        try:
            with self._lock:
                # Créer le dossier si nécessaire
                self.db_path.parent.mkdir(parents=True, exist_ok=True)
                
                data = {
                    'cocktails': [cocktail.to_dict() for cocktail in self.cocktails.values()],
                    'last_updated': datetime.now().isoformat()
                }
                
                # Sauvegarde atomique
                temp_path = self.db_path.with_suffix('.tmp')
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                temp_path.replace(self.db_path)
                logger.info("Base de données sauvegardée")
                return True
                
        except Exception as e:
            logger.error(f"Erreur sauvegarde base de données: {e}")
            return False
    
    def create_default_database(self):
        """Crée une base de données par défaut avec des cocktails classiques"""
        logger.info("Création base de données par défaut")
        
        # Cocktails classiques des années 1920
        default_cocktails = [
            {
                'id': 'old_fashioned',
                'name': 'Old Fashioned',
                'ingredients': [
                    {'name': 'Whisky', 'amount_ml': 60, 'category': 'spirits'},
                    {'name': 'Simple syrup', 'amount_ml': 5, 'category': 'syrups'},
                    {'name': 'Bitters', 'amount_ml': 2, 'category': 'syrups'}
                ],
                'description': 'Le roi des cocktails, symbole de l\'élégance prohibition',
                'category': 'classic',
                'difficulty': 2,
                'glass_type': 'rocks',
                'garnish': 'Orange peel',
                'instructions': [
                    'Verser le whisky dans le verre',
                    'Ajouter le sirop et les bitters',
                    'Mélanger délicatement',
                    'Garnir avec le zeste d\'orange'
                ]
            },
            {
                'id': 'gin_fizz',
                'name': 'Gin Fizz',
                'ingredients': [
                    {'name': 'Gin', 'amount_ml': 45, 'category': 'spirits'},
                    {'name': 'Jus de citron', 'amount_ml': 20, 'category': 'juices'},
                    {'name': 'Simple syrup', 'amount_ml': 10, 'category': 'syrups'},
                    {'name': 'Eau gazeuse', 'amount_ml': 50, 'category': 'mixers'}
                ],
                'description': 'Rafraîchissant et élégant, parfait pour les soirées chaudes',
                'category': 'classic',
                'difficulty': 2,
                'glass_type': 'highball',
                'garnish': 'Citron',
                'instructions': [
                    'Mélanger gin, jus de citron et sirop',
                    'Ajouter la glace',
                    'Compléter avec l\'eau gazeuse',
                    'Garnir avec le citron'
                ]
            },
            {
                'id': 'sidecar',
                'name': 'Sidecar', 
                'ingredients': [
                    {'name': 'Brandy', 'amount_ml': 50, 'category': 'spirits'},
                    {'name': 'Triple Sec', 'amount_ml': 20, 'category': 'spirits'},
                    {'name': 'Jus de citron', 'amount_ml': 15, 'category': 'juices'}
                ],
                'description': 'Sophistiqué et équilibré, né dans les bars parisiens',
                'category': 'classic',
                'difficulty': 3,
                'glass_type': 'coupe',
                'garnish': 'Sucre sur le bord',
                'instructions': [
                    'Sucrer le bord du verre',
                    'Mélanger tous les ingrédients',
                    'Servir dans le verre givré',
                    'Garnir élégamment'
                ]
            },
            {
                'id': 'bee_knees',
                'name': 'Bee\'s Knees',
                'ingredients': [
                    {'name': 'Gin', 'amount_ml': 60, 'category': 'spirits'},
                    {'name': 'Jus de citron', 'amount_ml': 20, 'category': 'juices'},
                    {'name': 'Sirop de miel', 'amount_ml': 15, 'category': 'syrups'}
                ],
                'description': 'Doux et aromatique, populaire pendant la prohibition',
                'category': 'classic',
                'difficulty': 2,
                'glass_type': 'coupe',
                'garnish': 'Zeste de citron',
                'instructions': [
                    'Mélanger tous les ingrédients',
                    'Shaker avec de la glace',
                    'Filtrer dans le verre',
                    'Garnir avec le zeste'
                ]
            },
            {
                'id': 'whiskey_sour',
                'name': 'Whiskey Sour',
                'ingredients': [
                    {'name': 'Whisky', 'amount_ml': 60, 'category': 'spirits'},
                    {'name': 'Jus de citron', 'amount_ml': 25, 'category': 'juices'},
                    {'name': 'Simple syrup', 'amount_ml': 15, 'category': 'syrups'}
                ],
                'description': 'Parfait équilibre entre doux et acide',
                'category': 'classic',
                'difficulty': 2,
                'glass_type': 'rocks',
                'garnish': 'Cerise et orange',
                'instructions': [
                    'Combiner whisky, jus et sirop',
                    'Shaker vigoureusement',
                    'Servir sur glace',
                    'Garnir avec fruits'
                ]
            },
            {
                'id': 'manhattan',
                'name': 'Manhattan',
                'ingredients': [
                    {'name': 'Whisky', 'amount_ml': 60, 'category': 'spirits'},
                    {'name': 'Vermouth rouge', 'amount_ml': 20, 'category': 'spirits'},
                    {'name': 'Bitters', 'amount_ml': 2, 'category': 'syrups'}
                ],
                'description': 'Cocktail sophistiqué de Manhattan, pur et puissant',
                'category': 'classic',
                'difficulty': 3,
                'glass_type': 'coupe',
                'garnish': 'Cerise',
                'instructions': [
                    'Mélanger délicatement les ingrédients',
                    'Refroidir sans diluer',
                    'Servir dans verre glacé',
                    'Garnir avec cerise de qualité'
                ]
            }
        ]
        
        for cocktail_data in default_cocktails:
            # Créer les ingrédients
            ingredients = []
            for ing_data in cocktail_data['ingredients']:
                ingredient = Ingredient(
                    name=ing_data['name'],
                    amount_ml=ing_data['amount_ml'],
                    category=ing_data['category']
                )
                ingredients.append(ingredient)
            
            # Créer la recette
            cocktail = CocktailRecipe(
                id=cocktail_data['id'],
                name=cocktail_data['name'],
                ingredients=ingredients,
                description=cocktail_data['description'],
                category=cocktail_data['category'],
                difficulty=cocktail_data['difficulty'],
                glass_type=cocktail_data['glass_type'],
                garnish=cocktail_data['garnish'],
                instructions=cocktail_data['instructions']
            )
            
            self.cocktails[cocktail.id] = cocktail
        
        self.save_database()
    
    def add_cocktail(self, cocktail: CocktailRecipe) -> bool:
        """Ajoute un cocktail à la base"""
        try:
            with self._lock:
                self.cocktails[cocktail.id] = cocktail
                self.save_database()
                logger.info(f"Cocktail ajouté: {cocktail.name}")
                return True
        except Exception as e:
            logger.error(f"Erreur ajout cocktail: {e}")
            return False
    
    def get_cocktail(self, cocktail_id: str) -> Optional[CocktailRecipe]:
        """Récupère un cocktail par ID"""
        return self.cocktails.get(cocktail_id)
    
    def get_all_cocktails(self) -> List[CocktailRecipe]:
        """Récupère tous les cocktails"""
        return list(self.cocktails.values())
    
    def get_makeable_cocktails(self) -> List[CocktailRecipe]:
        """Récupère les cocktails réalisables"""
        return [cocktail for cocktail in self.cocktails.values() if cocktail.is_makeable]
    
    def search_cocktails(self, query: str) -> List[CocktailRecipe]:
        """Recherche de cocktails par nom ou ingrédient"""
        query = query.lower()
        results = []
        
        for cocktail in self.cocktails.values():
            # Recherche par nom
            if query in cocktail.name.lower():
                results.append(cocktail)
                continue
            
            # Recherche par ingrédient
            for ingredient in cocktail.ingredients:
                if query in ingredient.name.lower():
                    results.append(cocktail)
                    break
        
        return results

class CocktailMaker:
    """Système de préparation de cocktails"""
    
    def __init__(self, database: CocktailDatabase):
        self.database = database
        self.current_order: Optional[CocktailRecipe] = None
        self.preparation_status = "idle"  # idle, preparing, completed, error
        self.progress_callback: Optional[callable] = None
        self._preparation_lock = threading.RLock()
    
    def set_progress_callback(self, callback: callable):
        """Définit le callback de progression"""
        self.progress_callback = callback
    
    def _notify_progress(self, step: str, progress: float):
        """Notifie la progression"""
        if self.progress_callback:
            self.progress_callback(step, progress)
    
    async def prepare_cocktail(self, cocktail_id: str, size_multiplier: float = 1.0) -> bool:
        """Prépare un cocktail de façon asynchrone"""
        try:
            with self._preparation_lock:
                if self.preparation_status != "idle":
                    logger.warning("Préparation déjà en cours")
                    return False
                
                cocktail = self.database.get_cocktail(cocktail_id)
                if not cocktail:
                    logger.error(f"Cocktail non trouvé: {cocktail_id}")
                    return False
                
                if not cocktail.is_makeable:
                    logger.error(f"Cocktail non réalisable: {cocktail.missing_ingredients}")
                    return False
                
                self.current_order = cocktail
                self.preparation_status = "preparing"
                
                logger.info(f"🍸 Début préparation: {cocktail.name}")
                self._notify_progress("Initialisation", 0)
                
                # Vérifier le système de pompes
                with pump_operation() as pump_sys:
                    # Préparation des ingrédients dans l'ordre optimal
                    total_steps = len([ing for ing in cocktail.ingredients if ing.category != "garnish"])
                    current_step = 0
                    
                    # Trier les ingrédients par catégorie pour un ordre optimal
                    sorted_ingredients = sorted(cocktail.ingredients, 
                                              key=lambda x: self._get_pour_order(x.category))
                    
                    for ingredient in sorted_ingredients:
                        if ingredient.category == "garnish":
                            continue
                        
                        if not ingredient.is_available or ingredient.pump_id is None:
                            logger.warning(f"Ingrédient indisponible: {ingredient.name}")
                            continue
                        
                        # Calculer le volume avec multiplicateur
                        volume = ingredient.amount_ml * size_multiplier
                        
                        step_name = f"Versement {ingredient.name}"
                        progress = (current_step / total_steps) * 100
                        self._notify_progress(step_name, progress)
                        
                        logger.info(f"  - Versement {volume:.1f}ml de {ingredient.name}")
                        
                        # Verser l'ingrédient
                        success = pump_sys.pour_volume(ingredient.pump_id, volume)
                        
                        if not success:
                            logger.error(f"Échec versement: {ingredient.name}")
                            self.preparation_status = "error"
                            return False
                        
                        # Pause entre les ingrédients
                        await asyncio.sleep(0.5)
                        current_step += 1
                    
                    # Finalisation
                    self._notify_progress("Finalisation", 95)
                    
                    # Instructions spéciales (mélange, etc.)
                    if cocktail.instructions:
                        logger.info("Instructions spéciales:")
                        for instruction in cocktail.instructions:
                            logger.info(f"  - {instruction}")
                    
                    # Garnissage
                    if cocktail.garnish:
                        self._notify_progress(f"Garnir avec {cocktail.garnish}", 98)
                        logger.info(f"  - Garnir avec: {cocktail.garnish}")
                    
                    self._notify_progress("Terminé", 100)
                    self.preparation_status = "completed"
                    
                    # Mettre à jour la popularité
                    cocktail.popularity += 1
                    self.database.save_database()
                    
                    logger.info(f"✅ Cocktail préparé avec succès: {cocktail.name}")
                    return True
        
        except Exception as e:
            logger.error(f"Erreur préparation cocktail: {e}")
            self.preparation_status = "error"
            return False
        
        finally:
            # Nettoyage même en cas d'erreur
            await asyncio.sleep(1)
            if self.preparation_status != "idle":
                self.preparation_status = "idle"
                self.current_order = None
    
    def _get_pour_order(self, category: str) -> int:
        """Définit l'ordre de versement optimal"""
        order = {
            'spirits': 1,    # Spiritueux en premier
            'syrups': 2,     # Sirops
            'juices': 3,     # Jus
            'mixers': 4,     # Mixers gazeux en dernier
            'garnish': 5     # Garnitures (non versées)
        }
        return order.get(category, 3)
    
    def stop_preparation(self):
        """Arrête la préparation en cours"""
        if self.preparation_status == "preparing":
            logger.warning("Arrêt de la préparation demandé")
            # Arrêt d'urgence des pompes
            pump_manager.emergency_stop()
            self.preparation_status = "idle"
            self.current_order = None
    
    def get_preparation_status(self) -> Dict[str, Any]:
        """Retourne le statut de préparation"""
        return {
            'status': self.preparation_status,
            'current_cocktail': self.current_order.name if self.current_order else None,
            'cocktail_id': self.current_order.id if self.current_order else None
        }

class CocktailManager:
    """Gestionnaire principal du système de cocktails"""
    
    def __init__(self):
        self.database = CocktailDatabase()
        self.maker = CocktailMaker(self.database)
        self.favorites: List[str] = []
        self._load_favorites()
    
    def _load_favorites(self):
        """Charge la liste des favoris"""
        try:
            favorites_path = Path("config/favorites.json")
            if favorites_path.exists():
                with open(favorites_path, 'r') as f:
                    data = json.load(f)
                    self.favorites = data.get('favorites', [])
        except Exception as e:
            logger.error(f"Erreur chargement favoris: {e}")
            self.favorites = []
    
    def save_favorites(self):
        """Sauvegarde la liste des favoris"""
        try:
            favorites_path = Path("config/favorites.json")
            favorites_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(favorites_path, 'w') as f:
                json.dump({'favorites': self.favorites}, f, indent=2)
        except Exception as e:
            logger.error(f"Erreur sauvegarde favoris: {e}")
    
    def get_popular_cocktails(self, limit: int = 10) -> List[CocktailRecipe]:
        """Récupère les cocktails les plus populaires"""
        cocktails = self.database.get_all_cocktails()
        return sorted(cocktails, key=lambda x: x.popularity, reverse=True)[:limit]
    
    def get_recommended_cocktails(self) -> List[CocktailRecipe]:
        """Récupère les cocktails recommandés"""
        # Algorithme simple: favoris + populaires + réalisables
        recommended = []
        
        # Ajouter les favoris disponibles
        for cocktail_id in self.favorites:
            cocktail = self.database.get_cocktail(cocktail_id)
            if cocktail and cocktail.is_makeable:
                recommended.append(cocktail)
        
        # Compléter avec les populaires
        popular = self.get_popular_cocktails(10)
        for cocktail in popular:
            if cocktail.is_makeable and cocktail not in recommended:
                recommended.append(cocktail)
        
        # Limiter à 6 recommandations
        return recommended[:6]
    
    def add_to_favorites(self, cocktail_id: str) -> bool:
        """Ajoute un cocktail aux favoris"""
        if cocktail_id not in self.favorites:
            self.favorites.append(cocktail_id)
            self.save_favorites()
            logger.info(f"Cocktail ajouté aux favoris: {cocktail_id}")
            return True
        return False
    
    def remove_from_favorites(self, cocktail_id: str) -> bool:
        """Retire un cocktail des favoris"""
        if cocktail_id in self.favorites:
            self.favorites.remove(cocktail_id)
            self.save_favorites()
            logger.info(f"Cocktail retiré des favoris: {cocktail_id}")
            return True
        return False
    
    def is_favorite(self, cocktail_id: str) -> bool:
        """Vérifie si un cocktail est favori"""
        return cocktail_id in self.favorites

# Instance globale du gestionnaire
cocktail_manager = CocktailManager()

def get_cocktail_manager() -> CocktailManager:
    """Récupère l'instance du gestionnaire de cocktails"""
    return cocktail_manager

def initialize_cocktail_system() -> bool:
    """Initialise le système de cocktails"""
    try:
        # Le gestionnaire est déjà initialisé
        logger.info("✅ Système de cocktails initialisé")
        return True
    except Exception as e:
        logger.error(f"❌ Erreur initialisation système cocktails: {e}")
        return False

if __name__ == "__main__":
    # Test du système
    import asyncio
    
    async def test_system():
        manager = get_cocktail_manager()
        
        # Test récupération cocktails
        cocktails = manager.database.get_makeable_cocktails()
        print(f"Cocktails disponibles: {len(cocktails)}")
        
        for cocktail in cocktails[:3]:
            print(f"  - {cocktail.name}: {cocktail.total_volume}ml")
        
        # Test préparation (simulation)
        if cocktails:
            print(f"\nTest préparation: {cocktails[0].name}")
            success = await manager.maker.prepare_cocktail(cocktails[0].id, 0.5)
            print(f"Résultat: {'✅ Succès' if success else '❌ Échec'}")
    
    asyncio.run(test_system())