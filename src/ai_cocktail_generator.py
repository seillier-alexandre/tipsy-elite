# -*- coding: utf-8 -*-
"""
Générateur IA de cocktails pour machine à cocktails Tipsy Elite
Intégration OpenAI pour création automatique de recettes
"""
import json
import logging
import asyncio
import openai
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import re
import time
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class AIGeneratedCocktail:
    """Cocktail généré par IA"""
    name: str
    description: str
    ingredients: List[Dict[str, any]]
    instructions: List[str]
    glass_type: str
    garnish: str
    difficulty: int
    category: str
    story: str = ""
    inspiration: str = ""
    generated_at: str = ""
    ai_confidence: float = 0.0
    
    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.now().isoformat()

class CocktailAI:
    """Générateur IA de cocktails avec OpenAI"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.model = model
        self.client = None
        
        # Configuration
        self.max_tokens = 1000
        self.temperature = 0.8  # Créativité élevée
        self.max_retries = 3
        
        # Cache des générations récentes
        self.generation_cache = {}
        self.cache_max_size = 50
        
        # Templates de prompts
        self.prompts = self._load_prompts()
        
        if api_key:
            self.set_api_key(api_key)
    
    def set_api_key(self, api_key: str):
        """Configure la clé API OpenAI"""
        self.api_key = api_key
        try:
            openai.api_key = api_key
            self.client = openai.OpenAI(api_key=api_key)
            logger.info("Client OpenAI configuré")
        except Exception as e:
            logger.error(f"Erreur configuration OpenAI: {e}")
            self.client = None
    
    def _load_prompts(self) -> Dict[str, str]:
        """Charge les templates de prompts"""
        return {
            "classic_cocktail": """
Tu es un mixologue expert spécialisé dans les cocktails classiques des années 1920-1940.
Crée un cocktail sophistiqué en utilisant principalement ces ingrédients disponibles: {available_ingredients}

Contraintes:
- Utilise UNIQUEMENT les ingrédients de la liste fournie
- Maximum 5 ingrédients par cocktail
- Style Art Déco / Prohibition
- Équilibre parfait des saveurs

Retourne UNIQUEMENT un objet JSON valide avec cette structure:
{{
  "name": "nom du cocktail",
  "description": "description en 2 phrases max",
  "ingredients": [
    {{"name": "nom_ingredient", "amount_ml": 50, "category": "spirits/mixers/juices/syrups"}}
  ],
  "instructions": ["étape 1", "étape 2", "étape 3"],
  "glass_type": "rocks/coupe/martini/highball",
  "garnish": "garniture",
  "difficulty": 2,
  "category": "classic",
  "story": "histoire courte du cocktail"
}}
""",
            
            "creative_cocktail": """
Tu es un mixologue créatif moderne qui révolutionne l'art du cocktail.
Crée un cocktail innovant avec ces ingrédients: {available_ingredients}

Style demandé: {style}
Force alcoolisée: {strength}/5
Complexité: {complexity}/5

Contraintes:
- Utilise UNIQUEMENT les ingrédients disponibles
- Maximum 6 ingrédients
- Nom créatif et mémorable
- Innovation dans les proportions ou techniques

Retourne UNIQUEMENT un JSON valide:
{{
  "name": "nom créatif",
  "description": "description alléchante",
  "ingredients": [
    {{"name": "ingredient", "amount_ml": 45, "category": "type"}}
  ],
  "instructions": ["technique", "mélange", "service"],
  "glass_type": "type_verre",
  "garnish": "garniture_créative",
  "difficulty": {complexity},
  "category": "modern",
  "story": "inspiration du cocktail",
  "inspiration": "source d'inspiration"
}}
""",
            
            "seasonal_cocktail": """
Tu es un expert en cocktails saisonniers et ambiances.
Crée un cocktail parfait pour: {occasion} en {season}

Ingrédients disponibles: {available_ingredients}
Ambiance: {mood}

Critères:
- Adapté à la saison et l'occasion
- Utilise les ingrédients disponibles
- Évoque l'ambiance demandée
- Histoire/contexte intéressant

JSON uniquement:
{{
  "name": "nom évocateur",
  "description": "description sensorielle",
  "ingredients": [{{"name": "ingredient", "amount_ml": 40, "category": "type"}}],
  "instructions": ["préparation", "service"],
  "glass_type": "verre",
  "garnish": "garniture",
  "difficulty": 3,
  "category": "seasonal",
  "story": "contexte saisonnier"
}}
""",
            
            "ingredient_spotlight": """
Tu es un expert qui sublime un ingrédient principal.
Crée un cocktail qui met en valeur: {main_ingredient}

Ingrédients complémentaires disponibles: {available_ingredients}

Objectif:
- {main_ingredient} doit être la star
- Sublimer ses qualités uniques
- Équilibre parfait avec les compléments
- Technique de préparation optimale

JSON résultat:
{{
  "name": "nom qui évoque {main_ingredient}",
  "description": "comment {main_ingredient} est sublimé",
  "ingredients": [{{"name": "{main_ingredient}", "amount_ml": 60, "category": "spirits"}}],
  "instructions": ["technique pour {main_ingredient}", "assemblage"],
  "glass_type": "verre_optimal",
  "garnish": "qui complète {main_ingredient}",
  "difficulty": 3,
  "category": "spirit_forward",
  "story": "pourquoi ce cocktail sublime {main_ingredient}"
}}
"""
        }
    
    async def generate_cocktail(self, 
                              available_ingredients: List[str],
                              style: str = "classic",
                              strength: int = 3,
                              complexity: int = 3,
                              special_request: str = "") -> Optional[AIGeneratedCocktail]:
        """Génère un cocktail avec l'IA"""
        
        if not self.client:
            logger.error("Client OpenAI non configuré")
            return None
        
        try:
            # Sélectionner le prompt approprié
            prompt_key = self._select_prompt_type(style, special_request)
            prompt_template = self.prompts[prompt_key]
            
            # Personnaliser le prompt
            prompt = self._customize_prompt(
                prompt_template,
                available_ingredients,
                style,
                strength,
                complexity,
                special_request
            )
            
            # Vérifier le cache
            cache_key = self._generate_cache_key(prompt)
            if cache_key in self.generation_cache:
                logger.info("Cocktail trouvé en cache")
                return self.generation_cache[cache_key]
            
            # Générer avec l'IA
            logger.info(f"Génération cocktail IA: {style}, force:{strength}, complexité:{complexity}")
            
            response = await self._call_openai_api(prompt)
            
            if response:
                cocktail = self._parse_ai_response(response)
                
                if cocktail:
                    # Valider et nettoyer
                    validated_cocktail = self._validate_cocktail(cocktail, available_ingredients)
                    
                    if validated_cocktail:
                        # Ajouter au cache
                        self._add_to_cache(cache_key, validated_cocktail)
                        return validated_cocktail
            
            logger.warning("Échec génération cocktail IA")
            return None
            
        except Exception as e:
            logger.error(f"Erreur génération cocktail IA: {e}")
            return None
    
    async def generate_random_cocktail(self, available_ingredients: List[str]) -> Optional[AIGeneratedCocktail]:
        """Génère un cocktail aléatoire créatif"""
        import random
        
        styles = ["classic", "modern", "tropical", "elegant", "bold", "refined"]
        style = random.choice(styles)
        strength = random.randint(2, 5)
        complexity = random.randint(2, 4)
        
        return await self.generate_cocktail(available_ingredients, style, strength, complexity)
    
    async def generate_ingredient_cocktail(self, 
                                         main_ingredient: str,
                                         available_ingredients: List[str]) -> Optional[AIGeneratedCocktail]:
        """Génère un cocktail centré sur un ingrédient spécifique"""
        
        # Retirer l'ingrédient principal de la liste pour éviter duplication
        other_ingredients = [ing for ing in available_ingredients if ing.lower() != main_ingredient.lower()]
        
        prompt_template = self.prompts["ingredient_spotlight"]
        prompt = prompt_template.format(
            main_ingredient=main_ingredient,
            available_ingredients=", ".join(other_ingredients)
        )
        
        response = await self._call_openai_api(prompt)
        
        if response:
            cocktail = self._parse_ai_response(response)
            if cocktail:
                return self._validate_cocktail(cocktail, available_ingredients)
        
        return None
    
    async def suggest_improvements(self, cocktail_data: Dict) -> Optional[str]:
        """Suggère des améliorations pour un cocktail existant"""
        
        if not self.client:
            return None
        
        prompt = f"""
Analyse ce cocktail et suggère 3 améliorations concrètes:

Cocktail: {cocktail_data.get('name', 'Sans nom')}
Ingrédients: {cocktail_data.get('ingredients', [])}
Instructions: {cocktail_data.get('instructions', [])}

Suggestions d'amélioration:
1. Équilibre des saveurs
2. Technique de préparation  
3. Présentation/garniture

Réponds en français, soyez concis et pratique.
"""
        
        try:
            response = await self._call_openai_api(prompt)
            return response
        except Exception as e:
            logger.error(f"Erreur suggestions IA: {e}")
            return None
    
    def _select_prompt_type(self, style: str, special_request: str) -> str:
        """Sélectionne le type de prompt approprié"""
        
        if "saison" in special_request.lower() or "occasion" in special_request.lower():
            return "seasonal_cocktail"
        elif style in ["classic", "prohibition", "vintage"]:
            return "classic_cocktail"
        else:
            return "creative_cocktail"
    
    def _customize_prompt(self, template: str, ingredients: List[str], 
                         style: str, strength: int, complexity: int, special_request: str) -> str:
        """Personnalise le prompt selon les paramètres"""
        
        # Variables de base
        variables = {
            "available_ingredients": ", ".join(ingredients),
            "style": style,
            "strength": strength,
            "complexity": complexity
        }
        
        # Variables pour cocktail saisonnier
        if "seasonal" in template:
            variables.update({
                "occasion": "soirée élégante",
                "season": "hiver",
                "mood": "sophistiquée"
            })
        
        # Appliquer les variables
        try:
            return template.format(**variables)
        except KeyError:
            # Si certaines variables manquent, utiliser le template de base
            return template.replace("{available_ingredients}", ", ".join(ingredients))
    
    async def _call_openai_api(self, prompt: str) -> Optional[str]:
        """Appelle l'API OpenAI avec gestion des erreurs"""
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "Tu es un mixologue expert qui crée des cocktails sophistiqués. Réponds UNIQUEMENT avec du JSON valide."
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                )
                
                content = response.choices[0].message.content
                logger.debug(f"Réponse IA reçue: {len(content)} caractères")
                return content
                
            except Exception as e:
                logger.warning(f"Tentative {attempt + 1}/{self.max_retries} échouée: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Backoff exponentiel
                else:
                    logger.error("Toutes les tentatives API échouées")
                    return None
        
        return None
    
    def _parse_ai_response(self, response: str) -> Optional[AIGeneratedCocktail]:
        """Parse la réponse IA en objet cocktail"""
        
        try:
            # Nettoyer la réponse (enlever markdown, etc.)
            cleaned = self._clean_json_response(response)
            
            # Parser JSON
            data = json.loads(cleaned)
            
            # Créer objet cocktail
            cocktail = AIGeneratedCocktail(**data)
            
            logger.info(f"Cocktail IA parsé: {cocktail.name}")
            return cocktail
            
        except json.JSONDecodeError as e:
            logger.error(f"Erreur parsing JSON IA: {e}")
            logger.debug(f"Réponse problématique: {response[:200]}...")
            return None
        except Exception as e:
            logger.error(f"Erreur création cocktail IA: {e}")
            return None
    
    def _clean_json_response(self, response: str) -> str:
        """Nettoie la réponse IA pour extraire le JSON"""
        
        # Enlever les blocs markdown
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*$', '', response)
        
        # Enlever texte avant/après JSON
        json_start = response.find('{')
        json_end = response.rfind('}')
        
        if json_start != -1 and json_end != -1:
            return response[json_start:json_end + 1]
        
        return response.strip()
    
    def _validate_cocktail(self, cocktail: AIGeneratedCocktail, 
                          available_ingredients: List[str]) -> Optional[AIGeneratedCocktail]:
        """Valide et nettoie un cocktail généré"""
        
        try:
            # Vérifier nom
            if not cocktail.name or len(cocktail.name) < 3:
                logger.warning("Nom de cocktail invalide")
                return None
            
            # Vérifier ingrédients disponibles
            valid_ingredients = []
            for ingredient in cocktail.ingredients:
                ingredient_name = ingredient.get('name', '')
                
                # Vérifier si l'ingrédient est disponible
                if self._is_ingredient_available(ingredient_name, available_ingredients):
                    # Valider quantité
                    amount = ingredient.get('amount_ml', 30)
                    if isinstance(amount, str):
                        try:
                            amount = float(amount)
                        except:
                            amount = 30
                    
                    # Limiter quantité raisonnable
                    amount = max(5, min(200, amount))
                    
                    valid_ingredients.append({
                        'name': ingredient_name,
                        'amount_ml': amount,
                        'category': ingredient.get('category', 'spirits')
                    })
                else:
                    logger.warning(f"Ingrédient non disponible ignoré: {ingredient_name}")
            
            if len(valid_ingredients) < 2:
                logger.warning("Pas assez d'ingrédients valides")
                return None
            
            cocktail.ingredients = valid_ingredients
            
            # Valider autres champs
            cocktail.difficulty = max(1, min(5, cocktail.difficulty))
            
            if not cocktail.glass_type:
                cocktail.glass_type = "rocks"
            
            if not cocktail.category:
                cocktail.category = "modern"
            
            # Calculer confiance IA
            cocktail.ai_confidence = self._calculate_confidence(cocktail, available_ingredients)
            
            logger.info(f"Cocktail validé: {cocktail.name} ({cocktail.ai_confidence:.1f}% confiance)")
            return cocktail
            
        except Exception as e:
            logger.error(f"Erreur validation cocktail: {e}")
            return None
    
    def _is_ingredient_available(self, ingredient_name: str, available_ingredients: List[str]) -> bool:
        """Vérifie si un ingrédient est disponible"""
        ingredient_lower = ingredient_name.lower()
        
        for available in available_ingredients:
            if ingredient_lower in available.lower() or available.lower() in ingredient_lower:
                return True
        
        return False
    
    def _calculate_confidence(self, cocktail: AIGeneratedCocktail, available_ingredients: List[str]) -> float:
        """Calcule un score de confiance pour le cocktail généré"""
        
        score = 0.0
        
        # Nom créatif et cohérent (20%)
        if len(cocktail.name) > 5 and ' ' in cocktail.name:
            score += 20
        
        # Tous les ingrédients disponibles (30%)
        if all(self._is_ingredient_available(ing['name'], available_ingredients) 
               for ing in cocktail.ingredients):
            score += 30
        
        # Instructions détaillées (20%)
        if len(cocktail.instructions) >= 3:
            score += 20
        
        # Description engageante (15%)
        if len(cocktail.description) > 30:
            score += 15
        
        # Histoire/contexte (15%)
        if cocktail.story and len(cocktail.story) > 20:
            score += 15
        
        return min(100, score)
    
    def _generate_cache_key(self, prompt: str) -> str:
        """Génère une clé de cache pour un prompt"""
        import hashlib
        return hashlib.md5(prompt.encode()).hexdigest()[:12]
    
    def _add_to_cache(self, key: str, cocktail: AIGeneratedCocktail):
        """Ajoute un cocktail au cache"""
        if len(self.generation_cache) >= self.cache_max_size:
            # Supprimer le plus ancien
            oldest_key = next(iter(self.generation_cache))
            del self.generation_cache[oldest_key]
        
        self.generation_cache[key] = cocktail
    
    def get_generation_stats(self) -> Dict[str, any]:
        """Récupère les statistiques de génération"""
        return {
            'cache_size': len(self.generation_cache),
            'api_configured': self.client is not None,
            'model': self.model,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature
        }

# Fonctions utilitaires
def create_cocktail_from_ai(ai_cocktail: AIGeneratedCocktail) -> Dict:
    """Convertit un cocktail IA en format système"""
    try:
        from cocktail_manager import CocktailRecipe, Ingredient
        from datetime import datetime
        
        # Créer les ingrédients
        ingredients = []
        for ing_data in ai_cocktail.ingredients:
            ingredient = Ingredient(
                name=ing_data['name'],
                amount_ml=float(ing_data['amount_ml']),
                category=ing_data.get('category', 'spirits')
            )
            ingredients.append(ingredient)
        
        # Générer ID unique
        import re
        cocktail_id = re.sub(r'[^a-zA-Z0-9_]', '_', ai_cocktail.name.lower())
        
        # Créer la recette
        cocktail = CocktailRecipe(
            id=cocktail_id,
            name=ai_cocktail.name,
            ingredients=ingredients,
            description=ai_cocktail.description,
            instructions=ai_cocktail.instructions,
            glass_type=ai_cocktail.glass_type,
            garnish=ai_cocktail.garnish,
            difficulty=ai_cocktail.difficulty,
            category=ai_cocktail.category,
            story=ai_cocktail.story,
            created_at=datetime.now().isoformat()
        )
        
        return cocktail
        
    except Exception as e:
        logger.error(f"Erreur conversion cocktail IA: {e}")
        return None

# Instance globale
cocktail_ai = CocktailAI()

def get_cocktail_ai() -> CocktailAI:
    """Récupère l'instance du générateur IA"""
    return cocktail_ai

if __name__ == "__main__":
    # Test du générateur IA (nécessite clé API)
    import asyncio
    
    async def test_ai():
        ai = get_cocktail_ai()
        
        # Test avec ingrédients de démo
        available = [
            "Vodka", "Gin", "Rhum", "Whisky",
            "Jus d'orange", "Jus de cranberry", "Sprite",
            "Grenadine", "Triple Sec"
        ]
        
        print("🤖 Test générateur IA de cocktails")
        print(f"📋 Ingrédients disponibles: {len(available)}")
        
        if not ai.api_key:
            print("⚠️ Clé API OpenAI non configurée - mode démo")
            return
        
        # Générer cocktail créatif
        cocktail = await ai.generate_cocktail(
            available_ingredients=available,
            style="modern",
            strength=3,
            complexity=2
        )
        
        if cocktail:
            print(f"✨ Cocktail généré: {cocktail.name}")
            print(f"📝 Description: {cocktail.description}")
            print(f"🥃 Ingrédients: {len(cocktail.ingredients)}")
            print(f"⭐ Confiance: {cocktail.ai_confidence}%")
        else:
            print("❌ Échec génération")
    
    # asyncio.run(test_ai())