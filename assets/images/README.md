# Assets Images - Tipsy Elite Cocktail Machine

## Structure des répertoires

```
assets/images/
├── cocktails/           # Images principales des cocktails
│   ├── thumbnails/      # Miniatures pour interface (150x150px)
│   ├── ingredients/     # Photos ingrédients par cocktail
│   ├── preparation/     # Étapes de préparation
│   └── serving/         # Présentation finale
├── ingredients/         # Images des ingrédients individuels
├── ui/                  # Éléments interface utilisateur
└── branding/           # Logos et éléments de marque
```

## Convention de nommage

### Cocktails
- **Main**: `{cocktail_id}_main.jpg` (ex: `gin_tonic_main.jpg`)
- **Thumbnail**: `{cocktail_id}_thumb.jpg` 
- **Ingrédients**: `{cocktail_id}_ingredients.jpg`
- **Préparation**: `{cocktail_id}_prep.jpg`
- **Service**: `{cocktail_id}_served.jpg`

### Ingrédients
- **Individual**: `{ingredient_id}.png` (ex: `gin.png`)
- **Category**: `category_{category_name}.png`

## Spécifications techniques

### Tailles recommandées
- **Thumbnails**: 150x150px (PNG avec transparence)
- **Main images**: 800x600px (JPG haute qualité)
- **Ingredient photos**: 400x400px (PNG avec transparence)
- **UI elements**: Variables selon usage

### Qualité
- **Compression JPG**: 85-90%
- **Format PNG**: Optimisé pour web
- **Palette couleurs**: Art Déco (or, bronze, bordeaux)

## Images Art Déco requises

### Style visuel 1920s
- **Éclairage**: Warm, golden hour
- **Backgrounds**: Dark wood, marble, brass
- **Props**: Crystal glasses, silver shakers, vintage garnishes
- **Color palette**: Gold (#D4AF37), Bronze (#CD7F32), Burgundy (#800020)

### Composition
- **Rule of thirds** appliquée
- **Symétrie Art Déco** dans arrangement
- **Depth of field** pour focus cocktail
- **High contrast** pour drama visuel

## Images manquantes par défaut

En cas d'image manquante, le système utilisera:
- `default_cocktail.png` - Image générique cocktail
- `default_ingredient.png` - Placeholder ingrédient
- `loading_placeholder.png` - Animation de chargement

## Optimisation

Toutes les images doivent être:
- **Optimisées** pour le web (TinyPNG recommandé)
- **Responsive** (format adapté écran tactile)
- **Cohérentes** en style Art Déco
- **Nommées** selon convention stricte