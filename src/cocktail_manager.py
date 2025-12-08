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

# Import conditionnel du gestionnaire d'images
try:
    from image_manager import get_image_manager
    IMAGE_SUPPORT = True
except ImportError:
    logger.warning("ImageManager non disponible - images désactivées")
    IMAGE_SUPPORT = False

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
    """Recette de cocktail complète avec support images et métadonnées étendues"""
    id: str
    name: str
    ingredients: List[Ingredient]
    description: str = ""
    category: str = "classic"  # classic, modern, tropical, prohibition, elegant
    difficulty: int = 1  # 1-5
    preparation_time: int = 60  # secondes
    glass_type: str = "rocks"
    garnish: str = ""
    instructions: List[str] = None
    popularity: int = 0
    created_at: str = ""
    
    # Nouvelles propriétés étendues
    display_name: str = ""
    era: str = ""
    origin: str = ""
    story: str = ""
    alcohol_content: float = 0.0
    total_volume_ml: float = 0.0
    cost_estimation: float = 0.0
    images: Dict[str, str] = None
    taste_profile: Dict[str, int] = None
    mood_tags: List[str] = None
    weather_tags: List[str] = None
    occasion_tags: List[str] = None
    
    def __post_init__(self):
        if self.instructions is None:
            self.instructions = []
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if self.images is None:
            self.images = {}
        if self.taste_profile is None:
            self.taste_profile = {}
        if self.mood_tags is None:
            self.mood_tags = []
        if self.weather_tags is None:
            self.weather_tags = []
        if self.occasion_tags is None:
            self.occasion_tags = []
        if not self.display_name:
            self.display_name = self.name
    
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
    
    def get_image_path(self, image_type: str = 'main') -> str:
        """Récupère le chemin d'une image du cocktail"""
        if IMAGE_SUPPORT and self.images:
            return self.images.get(image_type, self.images.get('main', ''))
        return f"cocktails/{self.id}_{image_type}.jpg"
    
    def load_image(self, image_type: str = 'main', size: Optional[Tuple[int, int]] = None):
        """Charge l'image du cocktail avec le gestionnaire d'images"""
        if IMAGE_SUPPORT:
            return get_image_manager().load_cocktail_image(self.id, image_type, size)
        return None
    
    def preload_images(self):
        """Précharge toutes les images du cocktail"""
        if IMAGE_SUPPORT:
            image_manager = get_image_manager()
            for image_type in ['main', 'thumb', 'ingredients']:
                try:
                    image_manager.load_cocktail_image(self.id, image_type)
                except Exception as e:
                    logger.debug(f"Erreur préchargement {self.id}.{image_type}: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire complet"""
        base_dict = {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'ingredients': [asdict(ing) for ing in self.ingredients],
            'description': self.description,
            'category': self.category,
            'difficulty': self.difficulty,
            'preparation_time': self.preparation_time,
            'glass_type': self.glass_type,
            'garnish': self.garnish,
            'instructions': self.instructions,
            'popularity': self.popularity,
            'created_at': self.created_at,
            'era': self.era,
            'origin': self.origin,
            'story': self.story,
            'alcohol_content': self.alcohol_content,
            'total_volume_ml': self.total_volume_ml,
            'cost_estimation': self.cost_estimation,
            'images': self.images,
            'taste_profile': self.taste_profile,
            'mood_tags': self.mood_tags,
            'weather_tags': self.weather_tags,
            'occasion_tags': self.occasion_tags
        }
        return base_dict

class CocktailDatabase:
    """Base de données des cocktails avec persistance JSON et support images"""
    
    def __init__(self, db_path: str = "config/cocktails_real.json", 
                 ingredients_db_path: str = "config/ingredients_database.json"):
        self.db_path = Path(db_path)
        self.ingredients_db_path = Path(ingredients_db_path)
        self.cocktails: Dict[str, CocktailRecipe] = {}
        self.ingredients_database: Dict[str, Dict] = {}
        self._lock = threading.RLock()
        self.load_ingredients_database()
        self.load_database()
    
    def load_ingredients_database(self) -> bool:
        """Charge la base de données des ingrédients"""
        try:
            if self.ingredients_db_path.exists():
                with open(self.ingredients_db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.ingredients_database = data.get('ingredients', {})
                    logger.info(f"Base d'ingrédients chargée: {len(self.ingredients_database)} catégories")
                    return True
        except Exception as e:
            logger.error(f"Erreur chargement base ingrédients: {e}")
        
        self.ingredients_database = {}
        return False
    
    def get_ingredient_info(self, ingredient_name: str) -> Optional[Dict]:
        """Récupère les informations détaillées d'un ingrédient"""
        for category, ingredients in self.ingredients_database.items():
            for ingredient_id, ingredient_data in ingredients.items():
                if (ingredient_data.get('name', '').lower() == ingredient_name.lower() or
                    ingredient_id.lower() == ingredient_name.lower().replace(' ', '_')):
                    return ingredient_data
        return None

    def load_database(self) -> bool:
        """Charge la base de données depuis le fichier JSON"""
        try:
            if self.db_path.exists():
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for cocktail_data in data.get('cocktails', []):
                    # Reconstituer les ingrédients avec informations enrichies
                    ingredients = []
                    for ing_data in cocktail_data.get('ingredients', []):
                        # Récupérer infos détaillées de l'ingrédient si disponible
                        ingredient_info = self.get_ingredient_info(ing_data['name'])
                        
                        ingredient = Ingredient(
                            name=ing_data['name'],
                            amount_ml=ing_data.get('amount_ml', 0.0),
                            pump_id=ing_data.get('pump_id'),
                            category=ing_data.get('category', 'spirits'),
                            is_available=ing_data.get('is_available', True)
                        )
                        
                        # Enrichir avec données de la base d'ingrédients
                        if ingredient_info and ingredient.pump_id is None:
                            # Essayer d'assigner automatiquement une pompe
                            pump_config = get_pump_by_ingredient(ingredient.name)
                            if pump_config:
                                ingredient.pump_id = pump_config.pump_id
                                ingredient.is_available = True
                        
                        ingredients.append(ingredient)
                    
                    # Extraire données recette étendue
                    recipe_data = cocktail_data.get('recipe', {})
                    presentation_data = cocktail_data.get('presentation', {})
                    
                    # Créer la recette complète
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
                        created_at=cocktail_data.get('created_at', ''),
                        # Nouvelles propriétés étendues
                        display_name=cocktail_data.get('display_name', cocktail_data['name']),
                        era=cocktail_data.get('era', ''),
                        origin=cocktail_data.get('origin', ''),
                        story=cocktail_data.get('story', ''),
                        alcohol_content=recipe_data.get('alcohol_content', 0.0),
                        total_volume_ml=recipe_data.get('total_volume_ml', 0.0),
                        cost_estimation=cocktail_data.get('cost_estimation', 0.0),
                        images=cocktail_data.get('images', {}),
                        taste_profile=presentation_data.get('taste_profile', {}),
                        mood_tags=cocktail_data.get('mood_tags', []),
                        weather_tags=cocktail_data.get('weather_tags', []),
                        occasion_tags=cocktail_data.get('occasion_tags', [])
                    )
                    
                    self.cocktails[cocktail.id] = cocktail
                
                logger.info(f"Base de données chargée: {len(self.cocktails)} cocktails")
                
                # Précharger les images en arrière-plan si support activé
                if IMAGE_SUPPORT and self.cocktails:
                    self._preload_cocktail_images()
                
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
        
        # Cocktails adaptés aux pompes disponibles
        default_cocktails = [
            {
                'id': 'gin_tonic',
                'name': 'Gin Tonic',
                'ingredients': [
                    {'name': 'Gin', 'amount_ml': 50, 'category': 'spirits'},
                    {'name': 'Sprite', 'amount_ml': 100, 'category': 'mixers'}
                ],
                'description': 'Classique rafraîchissant, simple et élégant',
                'category': 'classic',
                'difficulty': 1,
                'glass_type': 'highball',
                'garnish': 'Citron vert',
                'instructions': [
                    'Verser le gin sur glace',
                    'Compléter avec Sprite',
                    'Mélanger délicatement',
                    'Garnir avec citron vert'
                ]
            },
            {
                'id': 'vodka_cranberry',
                'name': 'Vodka Cranberry',
                'ingredients': [
                    {'name': 'Vodka', 'amount_ml': 45, 'category': 'spirits'},
                    {'name': 'Jus de cranberry', 'amount_ml': 90, 'category': 'juices'}
                ],
                'description': 'Cocktail fruité et coloré, parfait à toute heure',
                'category': 'modern',
                'difficulty': 1,
                'glass_type': 'rocks',
                'garnish': 'Cranberries',
                'instructions': [
                    'Mélanger vodka et jus',
                    'Servir sur glace',
                    'Garnir avec cranberries fraîches'
                ]
            },
            {
                'id': 'rum_cola',
                'name': 'Rum & Cola',
                'ingredients': [
                    {'name': 'Rhum', 'amount_ml': 50, 'category': 'spirits'},
                    {'name': 'Coca Cola', 'amount_ml': 120, 'category': 'mixers'}
                ],
                'description': 'Classique intemporel, Cuba Libre version simple',
                'category': 'classic',
                'difficulty': 1,
                'glass_type': 'highball',
                'garnish': 'Citron vert',
                'instructions': [
                    'Verser le rhum sur glace',
                    'Ajouter le Coca Cola',
                    'Mélanger légèrement',
                    'Garnir avec citron vert'
                ]
            },
            {
                'id': 'tequila_sunrise',
                'name': 'Tequila Sunrise',
                'ingredients': [
                    {'name': 'Tequila', 'amount_ml': 45, 'category': 'spirits'},
                    {'name': 'Jus d\'orange', 'amount_ml': 90, 'category': 'juices'},
                    {'name': 'Grenadine', 'amount_ml': 10, 'category': 'syrups'}
                ],
                'description': 'Magnifique dégradé de couleurs, goût tropical',
                'category': 'tropical',
                'difficulty': 2,
                'glass_type': 'highball',
                'garnish': 'Orange et cerise',
                'instructions': [
                    'Mélanger tequila et jus d\'orange',
                    'Ajouter la grenadine lentement',
                    'Observer le dégradé se former',
                    'Garnir avec fruits'
                ]
            },
            {
                'id': 'whisky_cola',
                'name': 'Whisky Cola',
                'ingredients': [
                    {'name': 'Whisky', 'amount_ml': 50, 'category': 'spirits'},
                    {'name': 'Coca Cola', 'amount_ml': 120, 'category': 'mixers'}
                ],
                'description': 'Jack & Coke version élégante, goût authentique',
                'category': 'classic',
                'difficulty': 1,
                'glass_type': 'rocks',
                'garnish': 'Citron',
                'instructions': [
                    'Verser le whisky sur glace',
                    'Compléter avec Coca Cola',
                    'Remuer délicatement',
                    'Garnir avec citron'
                ]
            },
            {
                'id': 'brandy_orange',
                'name': 'Brandy Orange',
                'ingredients': [
                    {'name': 'Brandy', 'amount_ml': 60, 'category': 'spirits'},
                    {'name': 'Jus d\'orange', 'amount_ml': 80, 'category': 'juices'},
                    {'name': 'Triple Sec', 'amount_ml': 10, 'category': 'spirits'}
                ],
                'description': 'Sophistiqué et fruité, notes d\'agrumes prononcées',
                'category': 'classic',
                'difficulty': 2,
                'glass_type': 'coupe',
                'garnish': 'Zeste d\'orange',
                'instructions': [
                    'Mélanger brandy et Triple Sec',
                    'Ajouter le jus d\'orange',
                    'Servir dans verre refroidi',
                    'Garnir avec zeste d\'orange'
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
    
    def _preload_cocktail_images(self):
        """Précharge les images des cocktails en arrière-plan"""
        try:
            cocktail_ids = list(self.cocktails.keys())
            image_manager = get_image_manager()
            image_manager.preload_cocktail_images(cocktail_ids, ['main', 'thumb'])
            logger.info(f"Préchargement images démarré pour {len(cocktail_ids)} cocktails")
        except Exception as e:
            logger.error(f"Erreur préchargement images: {e}")
    
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
    
    async def prepare_cocktail(self, cocktail_id: str, size_multiplier: float = 1.0, dose_mode: str = "single") -> bool:
        """Prépare un cocktail de façon asynchrone avec support simple/double dose"""
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
                
                # Calculer le multiplicateur selon le mode de dose
                final_multiplier = self._calculate_dose_multiplier(dose_mode, size_multiplier)
                
                self.current_order = cocktail
                self.preparation_status = "preparing"
                
                dose_text = "simple" if dose_mode == "single" else "double" if dose_mode == "double" else f"x{final_multiplier:.1f}"
                logger.info(f"[COCKTAIL] Début préparation: {cocktail.name} (dose {dose_text})")
                self._notify_progress("Initialisation", 0)
                
                # Vérifier le système de pompes
                try:
                    with pump_operation() as pump_sys:
                        if pump_sys is None:
                            logger.error("Système de pompes non disponible")
                            self._notify_error("Système de pompes non disponible")
                            return False
                        
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
                            
                            # Calculer le volume avec multiplicateur final
                            volume = ingredient.amount_ml * final_multiplier
                            
                            step_name = f"Versement {ingredient.name}"
                            progress = (current_step / total_steps) * 100
                            self._notify_progress(step_name, progress)
                            
                            logger.info(f"  - Versement {volume:.1f}ml de {ingredient.name}")
                            
                            # Verser l'ingrédient
                            success = await pump_sys.pour_volume(ingredient.pump_id, volume)
                            
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
                    
                    logger.info(f"[OK] Cocktail préparé avec succès: {cocktail.name}")
                    return True
                    
                except (RuntimeError, OSError) as e:
                    logger.error(f"Erreur système de pompes: {e}")
                    self._notify_error(f"Système de pompes indisponible: {e}")
                    return False
        
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
    
    def _calculate_dose_multiplier(self, dose_mode: str, base_multiplier: float = 1.0) -> float:
        """Calcule le multiplicateur de dose final"""
        dose_multipliers = {
            "single": 1.0,
            "double": 2.0,
            "half": 0.5,
            "triple": 3.0
        }
        
        dose_factor = dose_multipliers.get(dose_mode, 1.0)
        return base_multiplier * dose_factor
    
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
        logger.info("[OK] Système de cocktails initialisé")
        return True
    except Exception as e:
        logger.error(f"[ERROR] Erreur initialisation système cocktails: {e}")
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