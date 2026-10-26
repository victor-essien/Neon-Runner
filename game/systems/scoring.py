"""Score, coins, distance and persistent high score."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from game import config

log = logging.getLogger(__name__)


class HighScoreStore:
    """Tiny JSON file store. Failures are logged, never raised."""

    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = Path(path) if path else config.HIGH_SCORE_FILE

    def load(self) -> int:
        try:
            return max(0, int(json.loads(self.path.read_text())["high_score"]))
        except (OSError, ValueError, KeyError, TypeError):
            return 0

    def save(self, value: int) -> bool:
        try:
            self.path.write_text(json.dumps({"high_score": int(value)}))
            return True
        except OSError as exc:
            log.warning("Could not save high score: %s", exc)
            return False


class Scoring:
    def __init__(self, store: Optional[HighScoreStore] = None) -> None:
        self.store = store
        self.distance = 0.0
        self.coins = 0
        self.high_score = store.load() if store else 0

    def reset(self) -> None:
        self.distance = 0.0
        self.coins = 0
        if self.store:
            self.high_score = self.store.load()

    @property
    def score(self) -> int:
        return int(self.distance * config.SCORE_PER_METER) + self.coins * config.COIN_SCORE

    def add_distance(self, metres: float) -> None:
        self.distance += metres

    def add_coin(self) -> None:
        self.coins += 1

    def finalize(self) -> bool:
        """Call at game over. Returns True when a new high score was set."""
        if self.score > self.high_score:
            self.high_score = self.score
            if self.store:
                self.store.save(self.high_score)
            return True
        return False
