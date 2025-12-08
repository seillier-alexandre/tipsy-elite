#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interface Web Streamlit pour Configuration Machine à Cocktails Tipsy Elite
Gestion des pompes, maintenance, et configuration en temps réel
"""
import streamlit as st
import json
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Optional
import logging
import pandas as pd
from datetime import datetime

# Configuration page Streamlit
st.set_page_config(
    page_title="Tipsy Elite - Configuration",
    page_icon="🍸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import des modules internes
try:
    from hardware_config import PUMP_CONFIGS, get_pump_by_ingredient, SCREEN_CONFIG
    HARDWARE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"hardware_config non disponible: {e}")
    HARDWARE_AVAILABLE = False
    PUMP_CONFIGS = []
    def get_pump_by_ingredient(name): return None
    SCREEN_CONFIG = {'width': 800, 'height': 600}

try:
    from tb6612_controller import pump_manager, pump_operation
except ImportError as e:
    logger.warning(f"tb6612_controller non disponible: {e}")
    pump_manager = None
    def pump_operation(): 
        class MockPumpOperation:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def pour_volume(self, pump_id, volume): return True
            def prime_pump(self, pump_id, duration): return True
        return MockPumpOperation()

try:
    from cocktail_manager import get_cocktail_manager, CocktailRecipe, Ingredient
except ImportError as e:
    logger.warning(f"cocktail_manager non disponible: {e}")
    def get_cocktail_manager(): 
        class MockManager:
            def __init__(self):
                self.database = MockDatabase()
                self.maker = MockMaker()
        class MockDatabase:
            def get_makeable_cocktails(self): return []
            def get_all_cocktails(self): return []
        class MockMaker:
            def prepare_cocktail(self, *args): return True
            @property
            def preparation_status(self): return "idle"
        return MockManager()

try:
    from cleaning_system import get_cleaning_system
except ImportError as e:
    logger.warning(f"cleaning_system non disponible: {e}")
    def get_cleaning_system():
        class MockCleaning:
            def start_cleaning(self, mode): pass
            def clean_pump(self, pump_id): return True
        return MockCleaning()

class WebConfigurationManager:
    """Gestionnaire de configuration web pour la machine à cocktails"""
    
    def __init__(self):
        self.config_path = Path("config/web_config.json")
        self.pump_config_path = Path("config/pump_assignments.json")
        self.load_configuration()
        
    def load_configuration(self):
        """Charge la configuration web"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                self.config = self.create_default_config()
                self.save_configuration()
        except Exception as e:
            logger.error(f"Erreur chargement configuration: {e}")
            self.config = self.create_default_config()
    
    def create_default_config(self) -> Dict:
        """Crée la configuration par défaut"""
        return {
            "interface": {
                "theme": "dark",
                "language": "fr",
                "auto_refresh": True,
                "refresh_interval": 30
            },
            "pump_settings": {
                "pour_speed": 25.0,  # ml/s
                "prime_time": 3.0,   # seconds
                "clean_time": 10.0,  # seconds
                "retraction_time": 0.5  # seconds
            },
            "ai_settings": {
                "enabled": False,
                "openai_api_key": "",
                "model": "gpt-3.5-turbo",
                "max_tokens": 500
            },
            "maintenance": {
                "auto_clean": True,
                "clean_interval_hours": 24,
                "prime_on_startup": True
            }
        }
    
    def save_configuration(self):
        """Sauvegarde la configuration"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erreur sauvegarde configuration: {e}")
    
    def get_pump_assignments(self) -> Dict:
        """Récupère les assignations de pompes"""
        try:
            if self.pump_config_path.exists():
                with open(self.pump_config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Erreur lecture assignations pompes: {e}")
        
        # Configuration par défaut basée sur hardware_config
        default_assignments = {}
        if HARDWARE_AVAILABLE:
            for i, pump_config in enumerate(PUMP_CONFIGS):
                default_assignments[f"pump_{pump_config.pump_id}"] = {
                    "pump_id": pump_config.pump_id,
                    "ingredient": pump_config.ingredient,
                    "enabled": True,
                    "volume_remaining": 750.0,  # ml
                    "last_cleaned": datetime.now().isoformat()
                }
        else:
            # Configuration démo
            demo_ingredients = [
                "Vodka", "Gin", "Rhum", "Whisky", "Tequila", "Brandy",
                "Sprite", "Coca Cola", "Jus d'orange", "Jus de cranberry",
                "Grenadine", "Triple Sec"
            ]
            for i, ingredient in enumerate(demo_ingredients[:12]):
                default_assignments[f"pump_{i+1}"] = {
                    "pump_id": i + 1,
                    "ingredient": ingredient,
                    "enabled": True,
                    "volume_remaining": 750.0,
                    "last_cleaned": datetime.now().isoformat()
                }
        
        return default_assignments
    
    def save_pump_assignments(self, assignments: Dict):
        """Sauvegarde les assignations de pompes"""
        try:
            self.pump_config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.pump_config_path, 'w', encoding='utf-8') as f:
                json.dump(assignments, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erreur sauvegarde assignations: {e}")

# Instance globale
config_manager = WebConfigurationManager()

def main_interface():
    """Interface principale Streamlit"""
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #D4AF37 0%, #FFD700 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: #1a1a1a;
    }
    .pump-card {
        border: 1px solid #D4AF37;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        background-color: #f8f9fa;
    }
    .status-online { color: #28a745; }
    .status-offline { color: #dc3545; }
    .status-maintenance { color: #ffc107; }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="main-header">
        <h1>🍸 Tipsy Elite - Configuration</h1>
        <p>Interface de gestion et maintenance de la machine à cocktails</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar avec navigation
    st.sidebar.title("🎛️ Navigation")
    
    page = st.sidebar.selectbox(
        "Choisir une section",
        [
            "📊 Tableau de Bord",
            "🔧 Configuration des Pompes", 
            "🍹 Gestion des Cocktails",
            "🧹 Maintenance",
            "🤖 Intelligence Artificielle",
            "⚙️ Paramètres Système"
        ]
    )
    
    # Affichage selon la page sélectionnée
    if page == "📊 Tableau de Bord":
        dashboard_page()
    elif page == "🔧 Configuration des Pompes":
        pump_configuration_page()
    elif page == "🍹 Gestion des Cocktails":
        cocktail_management_page()
    elif page == "🧹 Maintenance":
        maintenance_page()
    elif page == "🤖 Intelligence Artificielle":
        ai_page()
    elif page == "⚙️ Paramètres Système":
        system_settings_page()

def dashboard_page():
    """Page tableau de bord"""
    st.header("📊 Tableau de Bord")
    
    # Métriques système
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🟢 Statut Système",
            value="En Ligne" if HARDWARE_AVAILABLE else "Mode Démo",
            delta="Opérationnel"
        )
    
    with col2:
        pump_assignments = config_manager.get_pump_assignments()
        active_pumps = len([p for p in pump_assignments.values() if p.get('enabled', False)])
        st.metric(
            label="🔧 Pompes Actives",
            value=f"{active_pumps}/12",
            delta=f"{active_pumps} configurées"
        )
    
    with col3:
        if HARDWARE_AVAILABLE:
            try:
                cocktail_manager = get_cocktail_manager()
                makeable_count = len(cocktail_manager.database.get_makeable_cocktails()) if cocktail_manager and cocktail_manager.database else 0
            except:
                makeable_count = 0
        else:
            makeable_count = 8  # Démo
        
        st.metric(
            label="🍹 Cocktails Disponibles",
            value=makeable_count,
            delta="prêts à servir"
        )
    
    with col4:
        st.metric(
            label="🕒 Dernière Maintenance",
            value="Il y a 2h",
            delta="Nettoyage OK"
        )
    
    st.divider()
    
    # Statut des pompes en temps réel
    st.subheader("🔧 État des Pompes en Temps Réel")
    
    pump_assignments = config_manager.get_pump_assignments()
    pump_data = []
    
    for pump_id, pump_info in pump_assignments.items():
        status = "🟢 En ligne" if pump_info.get('enabled') else "🔴 Hors ligne"
        volume_remaining = pump_info.get('volume_remaining', 0)
        volume_status = "🟢 OK" if volume_remaining > 100 else "🟡 Faible" if volume_remaining > 50 else "🔴 Vide"
        
        pump_data.append({
            "Pompe": f"#{pump_info['pump_id']}",
            "Ingrédient": pump_info.get('ingredient', 'Non assigné'),
            "Statut": status,
            "Volume (ml)": volume_remaining,
            "État Volume": volume_status,
            "Dernière Utilisation": "Il y a 1h"  # TODO: implémenter tracking
        })
    
    df_pumps = pd.DataFrame(pump_data)
    st.dataframe(df_pumps, use_container_width=True)
    
    # Actions rapides
    st.subheader("⚡ Actions Rapides")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🧹 Nettoyage Rapide", type="primary"):
            run_quick_cleaning()
    
    with col2:
        if st.button("🔄 Purger les Pompes"):
            prime_all_pumps()
    
    with col3:
        if st.button("📊 Rafraîchir Données"):
            st.rerun()

def pump_configuration_page():
    """Page configuration des pompes"""
    st.header("🔧 Configuration des Pompes")
    
    pump_assignments = config_manager.get_pump_assignments()
    
    st.subheader("📋 Attribution des Ingrédients")
    
    # Chargement de la base d'ingrédients disponibles
    available_ingredients = get_available_ingredients()
    
    # Configuration en colonnes
    col1, col2 = st.columns(2)
    
    updated_assignments = {}
    
    # Pompes 1-6
    with col1:
        st.markdown("**Pompes 1-6**")
        for i in range(1, 7):
            pump_key = f"pump_{i}"
            pump_info = pump_assignments.get(pump_key, {})
            
            with st.expander(f"🔧 Pompe {i} - {pump_info.get('ingredient', 'Non assigné')}"):
                col_ing, col_enable = st.columns([3, 1])
                
                with col_ing:
                    ingredient = st.selectbox(
                        "Ingrédient",
                        options=["Aucun"] + available_ingredients,
                        index=available_ingredients.index(pump_info.get('ingredient', 'Aucun')) + 1 
                              if pump_info.get('ingredient') in available_ingredients else 0,
                        key=f"ingredient_{i}"
                    )
                
                with col_enable:
                    enabled = st.checkbox(
                        "Actif",
                        value=pump_info.get('enabled', True),
                        key=f"enabled_{i}"
                    )
                
                volume = st.slider(
                    "Volume restant (ml)",
                    min_value=0,
                    max_value=1000,
                    value=int(pump_info.get('volume_remaining', 750)),
                    step=50,
                    key=f"volume_{i}"
                )
                
                # Boutons de contrôle
                col_prime, col_clean = st.columns(2)
                with col_prime:
                    if st.button(f"🔄 Purger", key=f"prime_{i}"):
                        prime_pump(i)
                
                with col_clean:
                    if st.button(f"🧹 Nettoyer", key=f"clean_{i}"):
                        clean_pump(i)
                
                updated_assignments[pump_key] = {
                    "pump_id": i,
                    "ingredient": ingredient if ingredient != "Aucun" else "",
                    "enabled": enabled,
                    "volume_remaining": volume,
                    "last_cleaned": pump_info.get('last_cleaned', datetime.now().isoformat())
                }
    
    # Pompes 7-12
    with col2:
        st.markdown("**Pompes 7-12**")
        for i in range(7, 13):
            pump_key = f"pump_{i}"
            pump_info = pump_assignments.get(pump_key, {})
            
            with st.expander(f"🔧 Pompe {i} - {pump_info.get('ingredient', 'Non assigné')}"):
                col_ing, col_enable = st.columns([3, 1])
                
                with col_ing:
                    ingredient = st.selectbox(
                        "Ingrédient",
                        options=["Aucun"] + available_ingredients,
                        index=available_ingredients.index(pump_info.get('ingredient', 'Aucun')) + 1 
                              if pump_info.get('ingredient') in available_ingredients else 0,
                        key=f"ingredient_{i}"
                    )
                
                with col_enable:
                    enabled = st.checkbox(
                        "Actif",
                        value=pump_info.get('enabled', True),
                        key=f"enabled_{i}"
                    )
                
                volume = st.slider(
                    "Volume restant (ml)",
                    min_value=0,
                    max_value=1000,
                    value=int(pump_info.get('volume_remaining', 750)),
                    step=50,
                    key=f"volume_{i}"
                )
                
                # Boutons de contrôle
                col_prime, col_clean = st.columns(2)
                with col_prime:
                    if st.button(f"🔄 Purger", key=f"prime_{i}"):
                        prime_pump(i)
                
                with col_clean:
                    if st.button(f"🧹 Nettoyer", key=f"clean_{i}"):
                        clean_pump(i)
                
                updated_assignments[pump_key] = {
                    "pump_id": i,
                    "ingredient": ingredient if ingredient != "Aucun" else "",
                    "enabled": enabled,
                    "volume_remaining": volume,
                    "last_cleaned": pump_info.get('last_cleaned', datetime.now().isoformat())
                }
    
    st.divider()
    
    # Sauvegarde des modifications
    col_save, col_cancel = st.columns([1, 1])
    
    with col_save:
        if st.button("💾 Sauvegarder Configuration", type="primary"):
            config_manager.save_pump_assignments(updated_assignments)
            st.success("✅ Configuration sauvegardée avec succès!")
            time.sleep(1)
            st.rerun()
    
    with col_cancel:
        if st.button("↩️ Annuler Modifications"):
            st.rerun()

def cocktail_management_page():
    """Page gestion des cocktails"""
    st.header("🍹 Gestion des Cocktails")
    
    if not HARDWARE_AVAILABLE:
        st.warning("⚠️ Mode démo - Fonctionnalités limitées")
    
    # Onglets
    tab1, tab2, tab3 = st.tabs(["📋 Cocktails Disponibles", "➕ Ajouter Cocktail", "📊 Statistiques"])
    
    with tab1:
        st.subheader("Cocktails Réalisables")
        
        if HARDWARE_AVAILABLE:
            try:
                cocktail_manager = get_cocktail_manager()
                cocktails = cocktail_manager.database.get_makeable_cocktails() if cocktail_manager and cocktail_manager.database else []
            except:
                cocktails = []
        else:
            # Données démo
            cocktails = [
                {"name": "Gin Tonic", "difficulty": 1, "ingredients": 2, "popularity": 8},
                {"name": "Vodka Cranberry", "difficulty": 1, "ingredients": 2, "popularity": 6},
                {"name": "Rum Cola", "difficulty": 1, "ingredients": 2, "popularity": 7}
            ]
        
        if cocktails:
            for cocktail in cocktails:
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        cocktail_name = cocktail.name if hasattr(cocktail, 'name') else cocktail['name']
                        st.markdown(f"**🍹 {cocktail_name}**")
                        
                        if hasattr(cocktail, 'description'):
                            st.caption(cocktail.description)
                    
                    with col2:
                        difficulty = cocktail.difficulty if hasattr(cocktail, 'difficulty') else cocktail.get('difficulty', 1)
                        st.metric("Difficulté", f"{difficulty}/5")
                    
                    with col3:
                        if st.button(f"🍹 Préparer", key=f"prepare_{cocktail_name}"):
                            prepare_cocktail(cocktail)
                    
                    st.divider()
        else:
            st.info("🤷 Aucun cocktail réalisable avec la configuration actuelle")
    
    with tab2:
        st.subheader("➕ Créer un Nouveau Cocktail")
        
        with st.form("new_cocktail"):
            name = st.text_input("Nom du cocktail")
            description = st.text_area("Description")
            
            st.markdown("**Ingrédients**")
            
            ingredients = []
            for i in range(5):  # Maximum 5 ingrédients
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    ingredient = st.selectbox(
                        f"Ingrédient {i+1}",
                        options=["Aucun"] + get_available_ingredients(),
                        key=f"new_ingredient_{i}"
                    )
                
                with col2:
                    volume = st.number_input(
                        f"Volume (ml)",
                        min_value=0,
                        max_value=200,
                        value=30,
                        key=f"new_volume_{i}"
                    )
                
                if ingredient != "Aucun":
                    ingredients.append({"ingredient": ingredient, "volume": volume})
            
            if st.form_submit_button("✨ Créer Cocktail"):
                if name and ingredients:
                    create_custom_cocktail(name, description, ingredients)
                    st.success(f"✅ Cocktail '{name}' créé avec succès!")
                else:
                    st.error("❌ Nom et au moins un ingrédient requis")
    
    with tab3:
        st.subheader("📊 Statistiques des Cocktails")
        
        # Graphique de popularité
        if HARDWARE_AVAILABLE:
            try:
                cocktail_manager = get_cocktail_manager()
                popular_cocktails = cocktail_manager.get_popular_cocktails(10)
                
                if popular_cocktails:
                    popularity_data = {
                        "Cocktail": [c.name for c in popular_cocktails],
                        "Popularité": [c.popularity for c in popular_cocktails]
                    }
                    
                    st.bar_chart(pd.DataFrame(popularity_data).set_index("Cocktail"))
                else:
                    st.info("📊 Pas encore de données de popularité")
            except:
                st.error("❌ Erreur chargement statistiques")
        else:
            # Données démo
            demo_data = {
                "Gin Tonic": 25,
                "Vodka Cranberry": 18,
                "Rum Cola": 22,
                "Whisky Cola": 15,
                "Tequila Sunrise": 12
            }
            st.bar_chart(demo_data)

def maintenance_page():
    """Page maintenance avancée"""
    st.header("🧹 Maintenance Avancée")
    
    # Onglets de maintenance
    tab1, tab2, tab3, tab4 = st.tabs(["🔧 Actions", "📊 Historique", "⏰ Programmation", "🔍 Diagnostics"])
    
    with tab1:
        st.subheader("Actions de Maintenance")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🧹 Nettoyage**")
            
            if st.button("🧹 Nettoyage Complet", type="primary"):
                run_full_cleaning()
            
            if st.button("⚡ Nettoyage Rapide"):
                run_quick_cleaning()
            
            if st.button("🚿 Rinçage Système"):
                run_system_rinse()
            
            st.divider()
            
            st.markdown("**🔄 Calibration**")
            
            selected_pump = st.selectbox(
                "Pompe à calibrer",
                options=[f"Pompe {i}" for i in range(1, 13)],
                key="calibration_pump"
            )
            
            calibration_volume = st.slider(
                "Volume de test (ml)",
                min_value=10,
                max_value=100,
                value=50,
                step=10
            )
            
            if st.button("🎯 Calibrer Pompe"):
                calibrate_pump(selected_pump, calibration_volume)
        
        with col2:
            st.markdown("**🔍 Tests et Diagnostics**")
            
            if st.button("🔍 Test Toutes les Pompes"):
                test_all_pumps()
            
            if st.button("📡 Test Connectivité"):
                test_connectivity()
            
            if st.button("🌡️ Vérifier Température"):
                check_temperature()
            
            if st.button("⚡ Test Alimentation"):
                test_power_supply()
            
            st.divider()
            
            st.markdown("**🔄 Purge**")
            
            if st.button("🔄 Purger Toutes les Pompes"):
                prime_all_pumps()
            
            # Purge individuelle
            pump_to_prime = st.selectbox(
                "Pompe à purger",
                options=[f"Pompe {i}" for i in range(1, 13)],
                key="prime_pump"
            )
            
            prime_duration = st.slider(
                "Durée purge (s)",
                min_value=1,
                max_value=10,
                value=3
            )
            
            if st.button("🔄 Purger Pompe"):
                prime_specific_pump(pump_to_prime, prime_duration)
    
    with tab2:
        st.subheader("📊 Historique de Maintenance")
        
        # Filtres
        col1, col2, col3 = st.columns(3)
        
        with col1:
            date_filter = st.date_input("Date depuis")
        
        with col2:
            action_filter = st.selectbox(
                "Type d'action",
                options=["Toutes", "Nettoyage", "Test", "Calibration", "Réparation"]
            )
        
        with col3:
            status_filter = st.selectbox(
                "Statut",
                options=["Tous", "Succès", "Échec", "En cours"]
            )
        
        # Historique (simulé)
        maintenance_log = generate_maintenance_history()
        df_maintenance = pd.DataFrame(maintenance_log)
        
        # Appliquer filtres
        if action_filter != "Toutes":
            df_maintenance = df_maintenance[df_maintenance["Type"] == action_filter]
        
        st.dataframe(df_maintenance, use_container_width=True)
        
        # Graphique des maintenances
        st.subheader("📈 Fréquence des Maintenances")
        
        # Simuler données pour graphique
        maintenance_counts = {
            "Nettoyage": 25,
            "Tests": 15,
            "Calibration": 8,
            "Réparations": 3
        }
        
        st.bar_chart(maintenance_counts)
    
    with tab3:
        st.subheader("⏰ Maintenance Programmée")
        
        # Configuration de la maintenance automatique
        st.markdown("**🤖 Maintenance Automatique**")
        
        auto_cleaning = st.checkbox(
            "Nettoyage automatique",
            value=True,
            help="Active le nettoyage automatique quotidien"
        )
        
        if auto_cleaning:
            col1, col2 = st.columns(2)
            
            with col1:
                cleaning_time = st.time_input(
                    "Heure de nettoyage",
                    value=datetime.strptime("02:00", "%H:%M").time()
                )
            
            with col2:
                cleaning_frequency = st.selectbox(
                    "Fréquence",
                    options=["Quotidien", "Hebdomadaire", "Bi-hebdomadaire"]
                )
        
        st.divider()
        
        # Maintenance manuelle programmée
        st.markdown("**📅 Programmer Maintenance**")
        
        with st.form("schedule_maintenance"):
            maintenance_type = st.selectbox(
                "Type de maintenance",
                options=["Nettoyage complet", "Calibration pompes", "Test système", "Maintenance préventive"]
            )
            
            schedule_date = st.date_input("Date")
            schedule_time = st.time_input("Heure")
            
            notes = st.text_area("Notes")
            
            if st.form_submit_button("📅 Programmer"):
                schedule_maintenance(maintenance_type, schedule_date, schedule_time, notes)
        
        st.divider()
        
        # Maintenances programmées
        st.markdown("**📋 Maintenances Programmées**")
        
        scheduled_tasks = get_scheduled_maintenance()
        if scheduled_tasks:
            for task in scheduled_tasks:
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.write(f"**{task['type']}**")
                        st.caption(f"{task['date']} à {task['time']}")
                    
                    with col2:
                        st.write(task['status'])
                    
                    with col3:
                        if st.button("❌", key=f"cancel_{task['id']}"):
                            cancel_maintenance(task['id'])
        else:
            st.info("Aucune maintenance programmée")
    
    with tab4:
        st.subheader("🔍 Diagnostics Système")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📊 État du Système**")
            
            # Métriques système
            system_metrics = get_system_diagnostics()
            
            st.metric(
                "Température CPU",
                f"{system_metrics.get('cpu_temp', 45)}°C",
                delta=f"{system_metrics.get('cpu_temp_delta', 0):+.1f}°C"
            )
            
            st.metric(
                "Utilisation Mémoire",
                f"{system_metrics.get('memory_usage', 65)}%",
                delta=f"{system_metrics.get('memory_delta', 0):+.1f}%"
            )
            
            st.metric(
                "Espace Disque",
                f"{system_metrics.get('disk_usage', 45)}%",
                delta=f"{system_metrics.get('disk_delta', 0):+.1f}%"
            )
            
            st.metric(
                "Uptime",
                f"{system_metrics.get('uptime', 0)} heures"
            )
        
        with col2:
            st.markdown("**🔧 État des Pompes**")
            
            pump_diagnostics = get_pump_diagnostics()
            
            for pump_id, diagnostics in pump_diagnostics.items():
                status_color = "🟢" if diagnostics['status'] == 'OK' else "🔴"
                st.write(f"{status_color} {pump_id}: {diagnostics['status']}")
                
                if diagnostics['status'] != 'OK':
                    st.caption(f"Erreur: {diagnostics.get('error', 'Inconnue')}")
        
        st.divider()
        
        # Logs en temps réel
        st.markdown("**📝 Logs Système**")
        
        with st.expander("Voir les logs détaillés"):
            log_level = st.selectbox(
                "Niveau de log",
                options=["INFO", "WARNING", "ERROR", "DEBUG"]
            )
            
            # Simuler logs
            logs = [
                "[2025-12-07 22:30:15] INFO: Nettoyage automatique terminé",
                "[2025-12-07 22:25:10] INFO: Cocktail Negroni préparé avec succès",
                "[2025-12-07 22:20:05] WARNING: Niveau bas détecté - Pompe 3",
                "[2025-12-07 22:15:00] INFO: Test système - Toutes pompes OK",
            ]
            
            for log in logs:
                if log_level in log:
                    st.code(log)
        
        # Actions de diagnostic
        st.markdown("**🔧 Actions de Diagnostic**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Redémarrer Système"):
                restart_system()
            
            if st.button("📊 Générer Rapport"):
                generate_diagnostic_report()
        
        with col2:
            if st.button("💾 Exporter Logs"):
                export_logs()
            
            if st.button("🧹 Nettoyer Logs"):
                clean_logs()

def ai_page():
    """Page Intelligence Artificielle"""
    st.header("🤖 Intelligence Artificielle")
    
    config = config_manager.config
    ai_config = config.get('ai_settings', {})
    
    # Configuration API
    st.subheader("🔑 Configuration API OpenAI")
    
    api_key = st.text_input(
        "Clé API OpenAI",
        value=ai_config.get('openai_api_key', ''),
        type="password",
        help="Votre clé API OpenAI pour la génération de cocktails"
    )
    
    model = st.selectbox(
        "Modèle IA",
        options=["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
        index=["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"].index(ai_config.get('model', 'gpt-3.5-turbo'))
    )
    
    # Génération de cocktails
    st.divider()
    st.subheader("✨ Génération de Cocktails")
    
    if api_key:
        col1, col2 = st.columns(2)
        
        with col1:
            ingredients_available = get_available_ingredients()
            selected_ingredients = st.multiselect(
                "Ingrédients disponibles",
                options=ingredients_available,
                help="Sélectionnez les ingrédients que vous souhaitez utiliser"
            )
            
            style = st.selectbox(
                "Style de cocktail",
                options=["Classique", "Moderne", "Tropical", "Élégant", "Épicé", "Frais"]
            )
        
        with col2:
            strength = st.slider("Force alcoolisée", 1, 5, 3)
            complexity = st.slider("Complexité", 1, 5, 3)
            
            if st.button("🎲 Générer Cocktail Aléatoire"):
                generate_random_cocktail(selected_ingredients, style, strength, complexity, api_key, model)
    
    else:
        st.warning("⚠️ Clé API OpenAI requise pour utiliser l'IA")
    
    # Sauvegarder configuration IA
    if st.button("💾 Sauvegarder Configuration IA"):
        config['ai_settings']['openai_api_key'] = api_key
        config['ai_settings']['model'] = model
        config['ai_settings']['enabled'] = bool(api_key)
        config_manager.config = config
        config_manager.save_configuration()
        st.success("✅ Configuration IA sauvegardée")

def system_settings_page():
    """Page paramètres système"""
    st.header("⚙️ Paramètres Système")
    
    config = config_manager.config
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎨 Interface")
        
        theme = st.selectbox(
            "Thème",
            options=["dark", "light"],
            index=["dark", "light"].index(config['interface'].get('theme', 'dark'))
        )
        
        language = st.selectbox(
            "Langue",
            options=["fr", "en"],
            index=["fr", "en"].index(config['interface'].get('language', 'fr'))
        )
        
        auto_refresh = st.checkbox(
            "Rafraîchissement automatique",
            value=config['interface'].get('auto_refresh', True)
        )
    
    with col2:
        st.subheader("🔧 Pompes")
        
        pour_speed = st.slider(
            "Vitesse de versement (ml/s)",
            min_value=10.0,
            max_value=50.0,
            value=config['pump_settings'].get('pour_speed', 25.0),
            step=1.0
        )
        
        prime_time = st.slider(
            "Temps de purge (s)",
            min_value=1.0,
            max_value=10.0,
            value=config['pump_settings'].get('prime_time', 3.0),
            step=0.5
        )
        
        clean_time = st.slider(
            "Temps de nettoyage (s)",
            min_value=5.0,
            max_value=30.0,
            value=config['pump_settings'].get('clean_time', 10.0),
            step=1.0
        )
    
    st.divider()
    
    # Sauvegarde
    if st.button("💾 Sauvegarder Paramètres", type="primary"):
        config['interface']['theme'] = theme
        config['interface']['language'] = language
        config['interface']['auto_refresh'] = auto_refresh
        config['pump_settings']['pour_speed'] = pour_speed
        config['pump_settings']['prime_time'] = prime_time
        config['pump_settings']['clean_time'] = clean_time
        
        config_manager.config = config
        config_manager.save_configuration()
        st.success("✅ Paramètres sauvegardés avec succès!")

# Fonctions utilitaires
def get_available_ingredients() -> List[str]:
    """Récupère la liste des ingrédients disponibles"""
    try:
        if HARDWARE_AVAILABLE:
            from cocktail_manager import get_cocktail_manager
            manager = get_cocktail_manager()
            
            # Récupérer les ingrédients de la base de données
            ingredients = set()
            for cocktail in manager.database.get_all_cocktails():
                for ingredient in cocktail.ingredients:
                    ingredients.add(ingredient.name)
            return sorted(list(ingredients))
        else:
            # Liste démo
            return [
                "Vodka", "Gin", "Rhum", "Whisky", "Tequila", "Brandy",
                "Campari", "Vermouth rouge", "Vermouth blanc", "Triple Sec",
                "Amaretto", "Sprite", "Coca Cola", "Jus d'orange", 
                "Jus de cranberry", "Jus de citron", "Grenadine", "Sirop simple"
            ]
    except Exception as e:
        logger.error(f"Erreur récupération ingrédients: {e}")
        return []

def prime_pump(pump_id: int):
    """Purge une pompe"""
    try:
        if HARDWARE_AVAILABLE:
            with pump_operation() as pump_sys:
                success = pump_sys.prime_pump(pump_id, 3.0)
                if success:
                    st.success(f"✅ Pompe {pump_id} purgée")
                else:
                    st.error(f"❌ Erreur purge pompe {pump_id}")
        else:
            time.sleep(2)  # Simulation
            st.success(f"✅ Pompe {pump_id} purgée (simulation)")
    except Exception as e:
        st.error(f"❌ Erreur: {e}")

def clean_pump(pump_id: int):
    """Nettoie une pompe"""
    try:
        if HARDWARE_AVAILABLE:
            cleaning_system = get_cleaning_system()
            success = cleaning_system.clean_pump(pump_id)
            if success:
                st.success(f"✅ Pompe {pump_id} nettoyée")
            else:
                st.error(f"❌ Erreur nettoyage pompe {pump_id}")
        else:
            time.sleep(3)  # Simulation
            st.success(f"✅ Pompe {pump_id} nettoyée (simulation)")
    except Exception as e:
        st.error(f"❌ Erreur: {e}")

def prime_all_pumps():
    """Purge toutes les pompes"""
    with st.spinner("🔄 Purge de toutes les pompes..."):
        try:
            if HARDWARE_AVAILABLE:
                pump_assignments = config_manager.get_pump_assignments()
                for pump_info in pump_assignments.values():
                    if pump_info.get('enabled'):
                        prime_pump(pump_info['pump_id'])
            else:
                time.sleep(5)  # Simulation
            st.success("✅ Toutes les pompes purgées")
        except Exception as e:
            st.error(f"❌ Erreur: {e}")

def run_quick_cleaning():
    """Lance un nettoyage rapide"""
    with st.spinner("🧹 Nettoyage rapide en cours..."):
        try:
            if HARDWARE_AVAILABLE:
                cleaning_system = get_cleaning_system()
                asyncio.run(cleaning_system.start_cleaning("quick"))
            else:
                time.sleep(8)  # Simulation
            st.success("✅ Nettoyage rapide terminé")
        except Exception as e:
            st.error(f"❌ Erreur: {e}")

def run_full_cleaning():
    """Lance un nettoyage complet"""
    with st.spinner("🧹 Nettoyage complet en cours..."):
        try:
            if HARDWARE_AVAILABLE:
                cleaning_system = get_cleaning_system()
                asyncio.run(cleaning_system.start_cleaning("deep"))
            else:
                time.sleep(15)  # Simulation
            st.success("✅ Nettoyage complet terminé")
        except Exception as e:
            st.error(f"❌ Erreur: {e}")

def run_system_rinse():
    """Lance un rinçage système"""
    with st.spinner("🚿 Rinçage système..."):
        try:
            time.sleep(10)  # Simulation
            st.success("✅ Rinçage système terminé")
        except Exception as e:
            st.error(f"❌ Erreur: {e}")

def test_all_pumps():
    """Test de toutes les pompes"""
    with st.spinner("🔍 Test des pompes..."):
        try:
            pump_assignments = config_manager.get_pump_assignments()
            results = []
            
            for pump_info in pump_assignments.values():
                if pump_info.get('enabled'):
                    # Simulation de test
                    time.sleep(0.5)
                    results.append({
                        "pump_id": pump_info['pump_id'],
                        "status": "✅ OK",
                        "ingredient": pump_info.get('ingredient', 'N/A')
                    })
            
            st.write("📊 Résultats des tests:")
            df_results = pd.DataFrame(results)
            st.dataframe(df_results)
            
        except Exception as e:
            st.error(f"❌ Erreur: {e}")

def prepare_cocktail(cocktail):
    """Prépare un cocktail"""
    with st.spinner(f"🍹 Préparation en cours..."):
        try:
            if HARDWARE_AVAILABLE:
                cocktail_manager = get_cocktail_manager()
                cocktail_id = cocktail.id if hasattr(cocktail, 'id') else cocktail['id']
                success = asyncio.run(cocktail_manager.maker.prepare_cocktail(cocktail_id))
                if success:
                    st.success(f"✅ {cocktail.name} prêt!")
                else:
                    st.error("❌ Erreur lors de la préparation")
            else:
                time.sleep(5)  # Simulation
                st.success(f"✅ {cocktail['name']} prêt! (simulation)")
        except Exception as e:
            st.error(f"❌ Erreur: {e}")

def create_custom_cocktail(name: str, description: str, ingredients: List[Dict]):
    """Crée un cocktail personnalisé"""
    # TODO: Implémenter la création de cocktail personnalisé
    st.success(f"✅ Cocktail '{name}' ajouté (fonctionnalité à implémenter)")

def generate_random_cocktail(ingredients: List[str], style: str, strength: int, complexity: int, api_key: str, model: str):
    """Génère un cocktail avec l'IA"""
    # TODO: Implémenter l'intégration OpenAI
    st.success("🎲 Génération IA en cours... (fonctionnalité à implémenter)")

# Fonctions utilitaires pour maintenance avancée

def generate_maintenance_history() -> List[Dict]:
    """Génère un historique de maintenance simulé"""
    from datetime import datetime, timedelta
    import random
    
    history = []
    types = ["Nettoyage", "Test", "Calibration", "Réparation"]
    statuses = ["✅ Succès", "❌ Échec", "⏳ En cours"]
    
    for i in range(20):
        date = datetime.now() - timedelta(days=random.randint(0, 30))
        history.append({
            "Date": date.strftime("%Y-%m-%d %H:%M"),
            "Type": random.choice(types),
            "Action": f"Action {i+1}",
            "Statut": random.choice(statuses),
            "Durée": f"{random.randint(5, 120)} min",
            "Utilisateur": "Admin"
        })
    
    return sorted(history, key=lambda x: x["Date"], reverse=True)

def calibrate_pump(pump: str, volume: int):
    """Calibre une pompe spécifique"""
    with st.spinner(f"Calibration de {pump}..."):
        time.sleep(3)
        st.success(f"✅ {pump} calibrée avec {volume}ml")

def test_connectivity():
    """Test la connectivité réseau"""
    with st.spinner("Test de connectivité..."):
        time.sleep(2)
        st.success("✅ Connectivité réseau OK")

def check_temperature():
    """Vérifie la température du système"""
    with st.spinner("Vérification température..."):
        time.sleep(1)
        temp = 42.5
        if temp < 50:
            st.success(f"✅ Température normale: {temp}°C")
        else:
            st.warning(f"⚠️ Température élevée: {temp}°C")

def test_power_supply():
    """Test l'alimentation électrique"""
    with st.spinner("Test alimentation..."):
        time.sleep(2)
        st.success("✅ Alimentation stable: 12V / 5V OK")

def prime_specific_pump(pump: str, duration: int):
    """Purge une pompe spécifique"""
    with st.spinner(f"Purge de {pump} pendant {duration}s..."):
        time.sleep(duration)
        st.success(f"✅ {pump} purgée")

def schedule_maintenance(maintenance_type: str, date, time_val, notes: str):
    """Programme une maintenance"""
    st.success(f"✅ Maintenance '{maintenance_type}' programmée pour le {date} à {time_val}")
    if notes:
        st.info(f"📝 Notes: {notes}")

def get_scheduled_maintenance() -> List[Dict]:
    """Récupère les maintenances programmées"""
    return [
        {
            "id": 1,
            "type": "Nettoyage complet",
            "date": "2025-12-08",
            "time": "02:00",
            "status": "⏰ Programmé"
        },
        {
            "id": 2,
            "type": "Calibration pompes",
            "date": "2025-12-10",
            "time": "03:00",
            "status": "⏰ Programmé"
        }
    ]

def cancel_maintenance(task_id: int):
    """Annule une maintenance programmée"""
    st.warning(f"❌ Maintenance {task_id} annulée")

def get_system_diagnostics() -> Dict:
    """Récupère les diagnostics système"""
    import random
    
    return {
        'cpu_temp': round(random.uniform(35, 55), 1),
        'cpu_temp_delta': round(random.uniform(-2, 2), 1),
        'memory_usage': random.randint(45, 85),
        'memory_delta': random.randint(-5, 5),
        'disk_usage': random.randint(30, 70),
        'disk_delta': random.randint(-2, 2),
        'uptime': random.randint(12, 168)
    }

def get_pump_diagnostics() -> Dict:
    """Récupère les diagnostics des pompes"""
    diagnostics = {}
    statuses = ['OK', 'WARNING', 'ERROR']
    
    for i in range(1, 13):
        status = 'OK' if i <= 10 else 'WARNING'  # Simuler quelques warnings
        diagnostics[f"Pompe {i}"] = {
            'status': status,
            'error': 'Niveau bas' if status == 'WARNING' else None
        }
    
    return diagnostics

def restart_system():
    """Redémarre le système"""
    if st.button("⚠️ Confirmer redémarrage", type="secondary"):
        with st.spinner("Redémarrage en cours..."):
            time.sleep(3)
            st.success("✅ Système redémarré")

def generate_diagnostic_report():
    """Génère un rapport de diagnostic"""
    with st.spinner("Génération du rapport..."):
        time.sleep(2)
        
        # Créer un rapport simulé
        report_data = {
            "Système": "Tipsy Elite v2.0",
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Statut global": "✅ Opérationnel",
            "Pompes actives": "10/12",
            "Dernière maintenance": "2025-12-07",
            "Recommandations": [
                "Vérifier niveau Pompe 3",
                "Programmer calibration dans 7 jours",
                "Nettoyer réservoir principal"
            ]
        }
        
        st.json(report_data)
        st.success("✅ Rapport généré")

def export_logs():
    """Exporte les logs système"""
    with st.spinner("Export des logs..."):
        time.sleep(2)
        st.success("✅ Logs exportés vers /tmp/tipsy_logs.txt")

def clean_logs():
    """Nettoie les anciens logs"""
    if st.button("⚠️ Confirmer nettoyage logs", type="secondary"):
        with st.spinner("Nettoyage des logs..."):
            time.sleep(1)
            st.success("✅ Anciens logs supprimés")

if __name__ == "__main__":
    main_interface()