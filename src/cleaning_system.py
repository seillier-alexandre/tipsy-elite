# -*- coding: utf-8 -*-
"""
Système de nettoyage automatique pour machine à cocktails
Nettoyage intelligent avec cycles programmés et maintenance préventive
Architecture sécurisée avec monitoring en temps réel
"""
import logging
import time
import json
import asyncio
import threading
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
from hardware_config import PUMP_CONFIGS, CLEANING_PUMP_CONFIG, TIMING_CONFIG
from tb6612_controller import pump_manager, pump_operation

logger = logging.getLogger(__name__)

class CleaningPhase(Enum):
    """Phases du cycle de nettoyage"""
    RINSE = "rinse"           # Rinçage initial
    CLEAN = "clean"           # Nettoyage avec solution
    SANITIZE = "sanitize"     # Désinfection
    FINAL_RINSE = "final_rinse"  # Rinçage final
    DRY = "dry"               # Séchage

class CleaningMode(Enum):
    """Modes de nettoyage"""
    QUICK = "quick"           # Nettoyage rapide (entre cocktails)
    STANDARD = "standard"     # Nettoyage standard (fin de service)
    DEEP = "deep"             # Nettoyage approfondi (maintenance)
    SANITIZE_ONLY = "sanitize"  # Désinfection uniquement

@dataclass
class CleaningCycle:
    """Configuration d'un cycle de nettoyage"""
    mode: CleaningMode
    phases: List[CleaningPhase]
    duration_per_phase: Dict[CleaningPhase, int]  # secondes
    solution_volume: Dict[CleaningPhase, float]   # ml
    pressure: int = 80  # Pourcentage de pression
    temperature: Optional[int] = None  # Température si capteur disponible
    
    @property
    def total_duration(self) -> int:
        """Durée totale du cycle en secondes"""
        return sum(self.duration_per_phase.values())

# Configuration des cycles de nettoyage
CLEANING_CYCLES = {
    CleaningMode.QUICK: CleaningCycle(
        mode=CleaningMode.QUICK,
        phases=[CleaningPhase.RINSE, CleaningPhase.CLEAN],
        duration_per_phase={
            CleaningPhase.RINSE: 10,
            CleaningPhase.CLEAN: 15
        },
        solution_volume={
            CleaningPhase.RINSE: 50.0,
            CleaningPhase.CLEAN: 30.0
        },
        pressure=60
    ),
    
    CleaningMode.STANDARD: CleaningCycle(
        mode=CleaningMode.STANDARD,
        phases=[CleaningPhase.RINSE, CleaningPhase.CLEAN, CleaningPhase.SANITIZE, CleaningPhase.FINAL_RINSE],
        duration_per_phase={
            CleaningPhase.RINSE: 20,
            CleaningPhase.CLEAN: 30,
            CleaningPhase.SANITIZE: 25,
            CleaningPhase.FINAL_RINSE: 15
        },
        solution_volume={
            CleaningPhase.RINSE: 100.0,
            CleaningPhase.CLEAN: 75.0,
            CleaningPhase.SANITIZE: 50.0,
            CleaningPhase.FINAL_RINSE: 100.0
        },
        pressure=80
    ),
    
    CleaningMode.DEEP: CleaningCycle(
        mode=CleaningMode.DEEP,
        phases=[CleaningPhase.RINSE, CleaningPhase.CLEAN, CleaningPhase.SANITIZE, 
                CleaningPhase.FINAL_RINSE, CleaningPhase.DRY],
        duration_per_phase={
            CleaningPhase.RINSE: 30,
            CleaningPhase.CLEAN: 60,
            CleaningPhase.SANITIZE: 45,
            CleaningPhase.FINAL_RINSE: 30,
            CleaningPhase.DRY: 120
        },
        solution_volume={
            CleaningPhase.RINSE: 150.0,
            CleaningPhase.CLEAN: 100.0,
            CleaningPhase.SANITIZE: 75.0,
            CleaningPhase.FINAL_RINSE: 150.0,
            CleaningPhase.DRY: 0.0
        },
        pressure=100
    ),
    
    CleaningMode.SANITIZE_ONLY: CleaningCycle(
        mode=CleaningMode.SANITIZE_ONLY,
        phases=[CleaningPhase.SANITIZE, CleaningPhase.FINAL_RINSE],
        duration_per_phase={
            CleaningPhase.SANITIZE: 30,
            CleaningPhase.FINAL_RINSE: 20
        },
        solution_volume={
            CleaningPhase.SANITIZE: 60.0,
            CleaningPhase.FINAL_RINSE: 80.0
        },
        pressure=75
    )
}

@dataclass
class CleaningStatus:
    """État du système de nettoyage"""
    is_running: bool = False
    current_mode: Optional[CleaningMode] = None
    current_phase: Optional[CleaningPhase] = None
    progress_percent: float = 0.0
    phase_start_time: Optional[float] = None
    cycle_start_time: Optional[float] = None
    estimated_completion: Optional[datetime] = None
    pumps_being_cleaned: List[int] = None
    error_message: str = ""
    last_cleaning: Optional[datetime] = None
    
    def __post_init__(self):
        if self.pumps_being_cleaned is None:
            self.pumps_being_cleaned = []

class CleaningHistory:
    """Historique des nettoyages"""
    
    def __init__(self, history_file: str = "config/cleaning_history.json"):
        self.history_file = Path(history_file)
        self.history: List[Dict[str, Any]] = []
        self._load_history()
    
    def _load_history(self):
        """Charge l'historique depuis le fichier"""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.history = data.get('cleaning_history', [])
                logger.info(f"Historique de nettoyage chargé: {len(self.history)} entrées")
        except Exception as e:
            logger.error(f"Erreur chargement historique: {e}")
            self.history = []
    
    def add_cleaning_record(self, mode: CleaningMode, duration: float, 
                          success: bool, details: Dict[str, Any] = None):
        """Ajoute un enregistrement de nettoyage"""
        record = {
            'timestamp': datetime.now().isoformat(),
            'mode': mode.value,
            'duration_seconds': duration,
            'success': success,
            'details': details or {}
        }
        
        self.history.append(record)
        
        # Garder seulement les 100 derniers enregistrements
        if len(self.history) > 100:
            self.history = self.history[-100:]
        
        self._save_history()
    
    def _save_history(self):
        """Sauvegarde l'historique"""
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump({'cleaning_history': self.history}, f, indent=2)
        except Exception as e:
            logger.error(f"Erreur sauvegarde historique: {e}")
    
    def get_recent_cleanings(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Récupère les nettoyages récents"""
        return self.history[-limit:] if limit <= len(self.history) else self.history
    
    def get_last_cleaning_by_mode(self, mode: CleaningMode) -> Optional[Dict[str, Any]]:
        """Récupère le dernier nettoyage d'un mode spécifique"""
        for record in reversed(self.history):
            if record['mode'] == mode.value and record['success']:
                return record
        return None

class MaintenanceScheduler:
    """Planificateur de maintenance automatique"""
    
    def __init__(self, history: CleaningHistory):
        self.history = history
        self.maintenance_config = self._load_maintenance_config()
    
    def _load_maintenance_config(self) -> Dict[str, Any]:
        """Charge la configuration de maintenance"""
        return {
            'quick_cleaning_interval': 5,      # Cocktails entre nettoyages rapides
            'standard_cleaning_interval': 24,  # Heures entre nettoyages standards
            'deep_cleaning_interval': 168,     # Heures entre nettoyages approfondis (7 jours)
            'max_cocktails_without_cleaning': 10,
            'auto_cleaning_enabled': True
        }
    
    def needs_cleaning(self, cocktails_made: int = 0) -> Tuple[bool, CleaningMode]:
        """Détermine si un nettoyage est nécessaire"""
        now = datetime.now()
        
        # Vérifier le nettoyage rapide (basé sur le nombre de cocktails)
        if cocktails_made >= self.maintenance_config['quick_cleaning_interval']:
            return True, CleaningMode.QUICK
        
        # Vérifier le nettoyage standard (toutes les 24h)
        last_standard = self.history.get_last_cleaning_by_mode(CleaningMode.STANDARD)
        if last_standard:
            last_time = datetime.fromisoformat(last_standard['timestamp'])
            hours_since = (now - last_time).total_seconds() / 3600
            if hours_since >= self.maintenance_config['standard_cleaning_interval']:
                return True, CleaningMode.STANDARD
        else:
            # Aucun nettoyage standard dans l'historique
            return True, CleaningMode.STANDARD
        
        # Vérifier le nettoyage approfondi (toutes les semaines)
        last_deep = self.history.get_last_cleaning_by_mode(CleaningMode.DEEP)
        if last_deep:
            last_time = datetime.fromisoformat(last_deep['timestamp'])
            hours_since = (now - last_time).total_seconds() / 3600
            if hours_since >= self.maintenance_config['deep_cleaning_interval']:
                return True, CleaningMode.DEEP
        else:
            # Aucun nettoyage approfondi dans l'historique
            return True, CleaningMode.DEEP
        
        return False, CleaningMode.QUICK
    
    def get_next_scheduled_cleaning(self) -> Tuple[datetime, CleaningMode]:
        """Calcule le prochain nettoyage programmé"""
        now = datetime.now()
        
        # Calculer les prochaines échéances
        schedules = []
        
        # Nettoyage standard
        last_standard = self.history.get_last_cleaning_by_mode(CleaningMode.STANDARD)
        if last_standard:
            last_time = datetime.fromisoformat(last_standard['timestamp'])
            next_standard = last_time + timedelta(hours=self.maintenance_config['standard_cleaning_interval'])
        else:
            next_standard = now
        schedules.append((next_standard, CleaningMode.STANDARD))
        
        # Nettoyage approfondi
        last_deep = self.history.get_last_cleaning_by_mode(CleaningMode.DEEP)
        if last_deep:
            last_time = datetime.fromisoformat(last_deep['timestamp'])
            next_deep = last_time + timedelta(hours=self.maintenance_config['deep_cleaning_interval'])
        else:
            next_deep = now
        schedules.append((next_deep, CleaningMode.DEEP))
        
        # Retourner la prochaine échéance
        return min(schedules)

class CleaningSystem:
    """Système principal de nettoyage"""
    
    def __init__(self):
        self.status = CleaningStatus()
        self.history = CleaningHistory()
        self.scheduler = MaintenanceScheduler(self.history)
        self.progress_callback: Optional[callable] = None
        self._cleaning_lock = threading.RLock()
        self._stop_requested = False
        
        # Compteur de cocktails pour maintenance
        self.cocktails_since_cleaning = 0
    
    def set_progress_callback(self, callback: callable):
        """Définit le callback de progression"""
        self.progress_callback = callback
    
    def _notify_progress(self, phase: str, progress: float, message: str = ""):
        """Notifie la progression"""
        self.status.progress_percent = progress
        if self.progress_callback:
            self.progress_callback(phase, progress, message)
    
    async def start_cleaning(self, mode: CleaningMode, 
                           pump_ids: Optional[List[int]] = None) -> bool:
        """Démarre un cycle de nettoyage"""
        try:
            with self._cleaning_lock:
                if self.status.is_running:
                    logger.warning("Nettoyage déjà en cours")
                    return False
                
                # Initialiser le statut
                self.status.is_running = True
                self.status.current_mode = mode
                self.status.current_phase = None
                self.status.progress_percent = 0.0
                self.status.cycle_start_time = time.time()
                self.status.error_message = ""
                self._stop_requested = False
                
                # Pompes à nettoyer
                if pump_ids is None:
                    pump_ids = [pump.pump_id for pump in PUMP_CONFIGS]
                self.status.pumps_being_cleaned = pump_ids
                
                # Cycle de nettoyage
                cycle = CLEANING_CYCLES[mode]
                self.status.estimated_completion = datetime.now() + timedelta(seconds=cycle.total_duration)
                
                logger.info(f"[CLEANING] Début nettoyage {mode.value} - Pompes: {pump_ids}")
                logger.info(f"   Phases: {[p.value for p in cycle.phases]}")
                logger.info(f"   Durée estimée: {cycle.total_duration}s")
                
                # Exécuter les phases
                total_phases = len(cycle.phases)
                for i, phase in enumerate(cycle.phases):
                    if self._stop_requested:
                        logger.info("Arrêt du nettoyage demandé")
                        break
                    
                    self.status.current_phase = phase
                    self.status.phase_start_time = time.time()
                    
                    phase_progress_base = (i / total_phases) * 100
                    phase_progress_span = (1 / total_phases) * 100
                    
                    await self._execute_cleaning_phase(phase, cycle, pump_ids, 
                                                     phase_progress_base, phase_progress_span)
                
                # Finalisation
                if not self._stop_requested:
                    self._notify_progress("Nettoyage terminé", 100, "Système propre")
                    
                    # Enregistrer dans l'historique
                    duration = time.time() - self.status.cycle_start_time
                    self.history.add_cleaning_record(
                        mode, duration, True, 
                        {'pumps_cleaned': pump_ids, 'phases_completed': len(cycle.phases)}
                    )
                    
                    # Réinitialiser le compteur
                    if mode in [CleaningMode.STANDARD, CleaningMode.DEEP]:
                        self.cocktails_since_cleaning = 0
                    
                    self.status.last_cleaning = datetime.now()
                    logger.info(f"[OK] Nettoyage terminé avec succès en {duration:.1f}s")
                    success = True
                else:
                    logger.warning("[WARNING] Nettoyage interrompu")
                    success = False
                
                # Nettoyer le statut
                self.status.is_running = False
                self.status.current_mode = None
                self.status.current_phase = None
                self.status.progress_percent = 0.0
                
                return success
        
        except Exception as e:
            logger.error(f"Erreur nettoyage: {e}")
            self.status.is_running = False
            self.status.error_message = str(e)
            
            # Arrêt d'urgence des pompes
            pump_manager.emergency_stop()
            return False
    
    async def _execute_cleaning_phase(self, phase: CleaningPhase, cycle: CleaningCycle,
                                    pump_ids: List[int], base_progress: float, 
                                    progress_span: float):
        """Exécute une phase de nettoyage"""
        duration = cycle.duration_per_phase[phase]
        solution_volume = cycle.solution_volume.get(phase, 0)
        
        phase_name = {
            CleaningPhase.RINSE: "Rinçage",
            CleaningPhase.CLEAN: "Nettoyage",
            CleaningPhase.SANITIZE: "Désinfection",
            CleaningPhase.FINAL_RINSE: "Rinçage final",
            CleaningPhase.DRY: "Séchage"
        }[phase]
        
        logger.info(f"  Phase: {phase_name} ({duration}s)")
        
        with pump_operation() as pump_sys:
            if phase == CleaningPhase.DRY:
                # Phase de séchage (pas de liquide)
                await self._dry_phase(duration, base_progress, progress_span, pump_ids)
            else:
                # Phase avec solution de nettoyage
                await self._liquid_phase(phase, duration, solution_volume, cycle.pressure,
                                       pump_ids, pump_sys, base_progress, progress_span)
    
    async def _liquid_phase(self, phase: CleaningPhase, duration: int, 
                          solution_volume: float, pressure: int, pump_ids: List[int],
                          pump_sys, base_progress: float, progress_span: float):
        """Exécute une phase avec liquide"""
        # Utiliser la pompe de nettoyage si disponible
        if CLEANING_PUMP_CONFIG and solution_volume > 0:
            # Activer la pompe de solution de nettoyage
            if phase == CleaningPhase.RINSE or phase == CleaningPhase.FINAL_RINSE:
                # Utiliser de l'eau pour le rinçage
                logger.info(f"    Rinçage avec {solution_volume}ml d'eau")
            else:
                # Utiliser la solution de nettoyage
                logger.info(f"    Application {solution_volume}ml de solution")
                
                # Démarrer la pompe de solution
                if CLEANING_PUMP_CONFIG is None:
                    logger.error("Configuration pompe de nettoyage non définie")
                    return False
                
                pump_sys.start_pump(CLEANING_PUMP_CONFIG.pump_id, pressure)
                await asyncio.sleep(solution_volume / CLEANING_PUMP_CONFIG.effective_flow_rate)
                pump_sys.stop_pump(CLEANING_PUMP_CONFIG.pump_id)
        
        # Faire circuler dans les pompes de cocktail
        start_time = time.time()
        
        while time.time() - start_time < duration:
            if self._stop_requested:
                break
            
            # Progression de la phase
            phase_progress = (time.time() - start_time) / duration
            total_progress = base_progress + (phase_progress * progress_span)
            self._notify_progress(
                f"{phase.value.replace('_', ' ').title()}", 
                total_progress,
                f"Nettoyage des pompes {pump_ids}"
            )
            
            # Faire circuler alternativement dans les pompes
            for pump_id in pump_ids:
                if self._stop_requested:
                    break
                
                # Pulse court pour faire circuler
                pump_sys.start_pump(pump_id, pressure // 2)
                await asyncio.sleep(0.5)
                pump_sys.stop_pump(pump_id)
                await asyncio.sleep(0.2)
            
            await asyncio.sleep(1)
    
    async def _dry_phase(self, duration: int, base_progress: float, 
                        progress_span: float, pump_ids: List[int]):
        """Exécute la phase de séchage"""
        start_time = time.time()
        
        while time.time() - start_time < duration:
            if self._stop_requested:
                break
            
            # Progression de la phase
            phase_progress = (time.time() - start_time) / duration
            total_progress = base_progress + (phase_progress * progress_span)
            
            remaining = duration - (time.time() - start_time)
            self._notify_progress(
                "Séchage", 
                total_progress,
                f"Séchage en cours... {remaining:.0f}s restantes"
            )
            
            await asyncio.sleep(2)
    
    def stop_cleaning(self):
        """Arrête le nettoyage en cours"""
        if self.status.is_running:
            logger.info("Arrêt du nettoyage demandé")
            self._stop_requested = True
            
            # Arrêt d'urgence des pompes
            pump_manager.emergency_stop()
    
    def get_cleaning_status(self) -> Dict[str, Any]:
        """Retourne le statut du nettoyage"""
        return {
            'is_running': self.status.is_running,
            'mode': self.status.current_mode.value if self.status.current_mode else None,
            'phase': self.status.current_phase.value if self.status.current_phase else None,
            'progress': self.status.progress_percent,
            'estimated_completion': self.status.estimated_completion.isoformat() if self.status.estimated_completion else None,
            'pumps_being_cleaned': self.status.pumps_being_cleaned,
            'error': self.status.error_message,
            'last_cleaning': self.status.last_cleaning.isoformat() if self.status.last_cleaning else None
        }
    
    def get_maintenance_info(self) -> Dict[str, Any]:
        """Retourne les informations de maintenance"""
        needs_cleaning, recommended_mode = self.scheduler.needs_cleaning(self.cocktails_since_cleaning)
        next_cleaning_time, next_mode = self.scheduler.get_next_scheduled_cleaning()
        
        return {
            'needs_cleaning': needs_cleaning,
            'recommended_mode': recommended_mode.value if needs_cleaning else None,
            'next_scheduled': next_cleaning_time.isoformat(),
            'next_scheduled_mode': next_mode.value,
            'cocktails_since_cleaning': self.cocktails_since_cleaning,
            'recent_cleanings': self.history.get_recent_cleanings(5)
        }
    
    def on_cocktail_made(self):
        """Appelé après chaque cocktail préparé"""
        self.cocktails_since_cleaning += 1
        
        # Vérifier si un nettoyage automatique est nécessaire
        if self.scheduler.maintenance_config['auto_cleaning_enabled']:
            needs_cleaning, mode = self.scheduler.needs_cleaning(self.cocktails_since_cleaning)
            if needs_cleaning and mode == CleaningMode.QUICK:
                logger.info(f"Nettoyage automatique déclenché après {self.cocktails_since_cleaning} cocktails")
                # Programmer un nettoyage rapide automatique
                threading.Thread(
                    target=lambda: asyncio.run(self.start_cleaning(CleaningMode.QUICK)),
                    daemon=True
                ).start()
    
    async def quick_rinse(self, pump_ids: Optional[List[int]] = None) -> bool:
        """Rinçage rapide entre cocktails"""
        if self.status.is_running:
            return False
        
        try:
            if pump_ids is None:
                pump_ids = [pump.pump_id for pump in PUMP_CONFIGS[:4]]  # Seulement les principales
            
            logger.info(f"Rinçage rapide des pompes: {pump_ids}")
            
            with pump_operation() as pump_sys:
                for pump_id in pump_ids:
                    # Pulse court de rinçage
                    pump_sys.start_pump(pump_id, 40)
                    await asyncio.sleep(1)
                    pump_sys.stop_pump(pump_id)
                    await asyncio.sleep(0.5)
            
            logger.info("[OK] Rinçage rapide terminé")
            return True
        
        except Exception as e:
            logger.error(f"Erreur rinçage rapide: {e}")
            return False

# Instance globale du système de nettoyage
cleaning_system = CleaningSystem()

def get_cleaning_system() -> CleaningSystem:
    """Récupère l'instance du système de nettoyage"""
    return cleaning_system

def initialize_cleaning_system() -> bool:
    """Initialise le système de nettoyage"""
    try:
        logger.info("[OK] Système de nettoyage initialisé")
        return True
    except Exception as e:
        logger.error(f"[ERROR] Erreur initialisation système nettoyage: {e}")
        return False

if __name__ == "__main__":
    # Test du système de nettoyage
    import asyncio
    
    async def test_cleaning():
        system = get_cleaning_system()
        
        # Test informations de maintenance
        maintenance_info = system.get_maintenance_info()
        print(f"Maintenance info: {maintenance_info}")
        
        # Test rinçage rapide
        print("\nTest rinçage rapide...")
        success = await system.quick_rinse([1, 2, 3])
        print(f"Rinçage: {'✅ Succès' if success else '❌ Échec'}")
        
        # Test cycle de nettoyage rapide
        print("\nTest nettoyage rapide...")
        
        def progress_callback(phase, progress, message):
            print(f"  {phase}: {progress:.1f}% - {message}")
        
        system.set_progress_callback(progress_callback)
        
        success = await system.start_cleaning(CleaningMode.QUICK, [1, 2])
        print(f"Nettoyage: {'✅ Succès' if success else '❌ Échec'}")
        
        # Afficher le statut final
        status = system.get_cleaning_status()
        print(f"Statut final: {status}")
    
    asyncio.run(test_cleaning())