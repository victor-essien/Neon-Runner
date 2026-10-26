"""Perspective projection shared by everything drawn in the 3-lane world.

World axes: x = lanes (0 = centre lane), z = metres ahead of the player,
y = metres above the track.
"""
from __future__ import annotations

from game import config

CX = config.SCREEN_WIDTH / 2


def depth_scale(z: float) -> float:
    z = max(z, -config.FOCAL * 0.85)
    return config.FOCAL / (config.FOCAL + z)


def project(x: float, z: float, y: float = 0.0) -> tuple[float, float, float]:
    """World -> (screen_x, screen_y, scale)."""
    s = depth_scale(z)
    sx = CX + x * config.LANE_WIDTH_PX * s
    sy = config.HORIZON_Y + (config.GROUND_Y - config.HORIZON_Y) * s - y * config.PX_PER_M * s
    return sx, sy, s
