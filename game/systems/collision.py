"""Gameplay-aware collision checks (lane + depth + height), pure logic."""
from __future__ import annotations

from game import config
from game.entities.coin import Coin
from game.entities.obstacle import Obstacle
from game.player.player import Player


def _depth_overlap(prev_z: float, z: float, length: float, half_depth: float) -> bool:
    """Swept overlap along the z axis so fast frames cannot tunnel through."""
    lo = min(prev_z, z)
    hi = max(prev_z, z) + length
    return lo < half_depth and hi > -half_depth


def check_obstacle_collision(player: Player, obstacle: Obstacle) -> bool:
    """True if the player's current lane, depth and height intersect the obstacle."""
    if abs(player.lane_pos - obstacle.lane) >= config.LANE_HIT_WIDTH:
        return False
    if not _depth_overlap(obstacle.prev_z, obstacle.z, obstacle.length, config.PLAYER_HALF_DEPTH):
        return False
    bottom = player.y
    top = player.y + player.height
    f = config.VERTICAL_FORGIVENESS
    return bottom < obstacle.y1 - f and top > obstacle.y0 + f


def check_coin_collision(player: Player, coin: Coin) -> bool:
    if coin.collected:
        return False
    if abs(player.lane_pos - coin.lane) >= config.COIN_PICKUP_LANE:
        return False
    if not _depth_overlap(coin.prev_z, coin.z, 0.0, config.COIN_PICKUP_DEPTH):
        return False
    return player.y - 0.2 <= coin.y <= player.y + player.height + 0.2
