"""
Scheduler de veille automatique — Scraping nocturne uniquement.

Le scraping se lance UNIQUEMENT la nuit (entre 00h00 et 05h00) pour ne pas
impacter les performances de la plateforme pendant la journée de travail.
Fuseau horaire: Africa/Casablanca (GMT+1, Maroc).
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# Heure de début du scraping nocturne (minuit)
NIGHT_START_HOUR = 0
# Heure de fin: le scraping ne se lance plus après cette heure
NIGHT_END_HOUR = 5


class VeilleScheduler:
    """Scheduler asyncio pour le scraping automatique — mode nocturne."""

    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._last_run: Optional[datetime] = None
        self._next_run: Optional[datetime] = None
        self._last_results: Dict[str, int] = {}
        self._cycle_count = 0

    @property
    def is_running(self) -> bool:
        return self._running and self._task is not None and not self._task.done()

    def get_status(self) -> dict:
        """Retourne l'état actuel du scheduler."""
        now = datetime.now()
        is_night = NIGHT_START_HOUR <= now.hour < NIGHT_END_HOUR
        return {
            "is_running": self.is_running,
            "mode": "nocturne",
            "scraping_window": f"{NIGHT_START_HOUR:02d}:00 - {NIGHT_END_HOUR:02d}:00",
            "is_night_window": is_night,
            "current_time": now.strftime("%H:%M:%S"),
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "next_run": self._next_run.isoformat() if self._next_run else None,
            "cycle_count": self._cycle_count,
            "last_results": self._last_results,
        }

    def start(self):
        """Démarre le scheduler nocturne."""
        if self.is_running:
            logger.warning("Scheduler already running.")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(
            f"🌙 Veille Scheduler started — scraping window: "
            f"{NIGHT_START_HOUR:02d}:00 - {NIGHT_END_HOUR:02d}:00"
        )

    def stop(self):
        """Arrête le scheduler."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            logger.info("🛑 Veille Scheduler stopped.")

    async def run_now(self) -> Dict[str, int]:
        """Force un cycle de scraping immédiatement (ignore la fenêtre horaire)."""
        logger.info("⚡ Manual scraping cycle triggered (force).")
        return await self._execute_cycle()

    def _seconds_until_next_night(self) -> float:
        """Calcule le nombre de secondes avant la prochaine fenêtre nocturne."""
        now = datetime.now()
        # Si on est dans la fenêtre nocturne, lancer maintenant
        if NIGHT_START_HOUR <= now.hour < NIGHT_END_HOUR:
            return 0

        # Sinon, calculer quand sera le prochain minuit
        tomorrow = now.replace(
            hour=NIGHT_START_HOUR, minute=0, second=0, microsecond=0
        )
        if now.hour >= NIGHT_END_HOUR:
            tomorrow += timedelta(days=1)
        
        delta = (tomorrow - now).total_seconds()
        return max(delta, 0)

    async def _run_loop(self):
        """Boucle principale: attend la nuit puis scrape."""
        while self._running:
            try:
                # Calculer le temps d'attente jusqu'à la prochaine nuit
                wait_seconds = self._seconds_until_next_night()

                if wait_seconds > 0:
                    next_run = datetime.now() + timedelta(seconds=wait_seconds)
                    self._next_run = next_run
                    logger.info(
                        f"😴 Scheduler idle — next scraping at "
                        f"{next_run.strftime('%Y-%m-%d %H:%M')} "
                        f"(in {wait_seconds/3600:.1f}h)"
                    )
                    await asyncio.sleep(wait_seconds)

                if not self._running:
                    break

                # Exécuter le cycle de scraping nocturne
                self._next_run = datetime.now()
                await self._execute_cycle()

                # Après le cycle, dormir jusqu'à la prochaine nuit (demain)
                # On attend au minimum 20h pour ne pas refaire un cycle le même soir
                await asyncio.sleep(20 * 3600)

            except asyncio.CancelledError:
                logger.info("Scheduler loop cancelled.")
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}", exc_info=True)
                # En cas d'erreur, attendre 1h avant de réessayer
                await asyncio.sleep(3600)

    async def _execute_cycle(self) -> Dict[str, int]:
        """
        Exécute un cycle SOURCE PAR SOURCE avec pauses, pour ne pas
        surcharger le système même la nuit.
        """
        from app.scraping.orchestrator import ScrapingOrchestrator
        from app.scraping.sources_registry import SOURCES_REGISTRY

        self._cycle_count += 1
        self._last_run = datetime.now()
        total_sources = len(SOURCES_REGISTRY)
        logger.info(
            f"🔄 Night scraping cycle #{self._cycle_count} — "
            f"{total_sources} sources to process"
        )

        orchestrator = ScrapingOrchestrator()
        results: Dict[str, int] = {}

        for i, (source_id, config) in enumerate(SOURCES_REGISTRY.items(), 1):
            if not self._running:
                logger.info("Scheduler stopped mid-cycle.")
                break

            logger.info(f"  [{i}/{total_sources}] {config.get('name', source_id)} ...")
            try:
                count = await asyncio.wait_for(
                    orchestrator.run_single_source(source_id, config, limit=5),
                    timeout=180  # 3 min max par source
                )
                results[source_id] = count
                logger.info(f"  ✓ {source_id}: {count} docs")
            except asyncio.TimeoutError:
                results[source_id] = 0
                logger.warning(f"  ⏰ {source_id}: timeout")
            except Exception as e:
                results[source_id] = 0
                logger.error(f"  ❌ {source_id}: {e}")

            # Pause de 15s entre sources
            if self._running:
                await asyncio.sleep(15)

        self._last_results = results
        total_docs = sum(results.values())
        logger.info(
            f"✅ Night cycle #{self._cycle_count} done: "
            f"{total_docs} docs from {len(results)} sources"
        )
        return results


# Singleton global
_scheduler: Optional[VeilleScheduler] = None


def get_scheduler() -> VeilleScheduler:
    """Retourne l'instance singleton du scheduler."""
    global _scheduler
    if _scheduler is None:
        _scheduler = VeilleScheduler()
    return _scheduler
