"""Lane helpers."""
from __future__ import annotations

from game import config


def lane_offset(lane_pos: float) -> float:
    """Lane index (0..2) -> centred lane units (-1..+1) used by the camera."""
    return lane_pos - (config.LANE_COUNT - 1) / 2.0
