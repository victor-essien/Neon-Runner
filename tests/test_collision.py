import random

from game import config
from game.controller.actions import Action
from game.core.session import GameSession
from game.entities.coin import Coin
from game.entities.obstacle import Obstacle
from game.player.player import Player
from game.systems.collision import check_obstacle_collision
from game.world.spawner import row_is_passable


def at_player(ob):
    ob.z = 0.0
    ob.prev_z = 0.0
    return ob


def test_barrier_hits_grounded_player_in_same_lane():
    assert check_obstacle_collision(Player(), at_player(Obstacle.barrier(1, 0)))


def test_barrier_in_other_lane_is_safe():
    assert not check_obstacle_collision(Player(), at_player(Obstacle.barrier(0, 0)))


def test_jump_clears_barrier():
    p = Player()
    p.jump()
    for _ in range(18):
        p.update(0.01)
    assert p.y > config.BARRIER_HEIGHT
    assert not check_obstacle_collision(p, at_player(Obstacle.barrier(1, 0)))


def test_overhead_requires_slide():
    ob = at_player(Obstacle.overhead(1, 0))
    assert check_obstacle_collision(Player(), ob)
    p = Player()
    p.slide()
    assert not check_obstacle_collision(p, ob)


def test_jumping_into_overhead_still_collides():
    p = Player()
    p.jump()
    for _ in range(12):
        p.update(0.01)
    assert check_obstacle_collision(p, at_player(Obstacle.overhead(1, 0)))


def test_train_cannot_be_jumped():
    p = Player()
    p.jump()
    for _ in range(40):
        p.update(0.01)
    assert check_obstacle_collision(p, at_player(Obstacle.train(1, 0, 9)))


def test_fast_frame_does_not_tunnel_through_barrier():
    s = GameSession(spawn=False)
    s.world.add_obstacle(Obstacle.barrier(1, 0.9))
    s.update(0.05)                         # barrier moves ~0.8 m, crossing the player
    assert s.crashed


def test_collision_causes_game_over_in_session():
    s = GameSession(spawn=False)
    s.world.add_obstacle(Obstacle.train(1, 3.0, 9))
    for _ in range(60):
        s.update(1 / 60)
    assert s.crashed


def test_dodging_by_lane_change_survives():
    s = GameSession(spawn=False)
    s.world.add_obstacle(Obstacle.train(1, 12.0, 9))
    s.apply_action(Action.LEFT)
    for _ in range(120):
        s.update(1 / 60)
    assert not s.crashed


def test_coin_increases_count_and_score():
    s = GameSession(spawn=False)
    s.world.add_coin(Coin(1, 0.5))
    before = s.scoring.score
    s.update(1 / 60)
    assert s.scoring.coins == 1
    assert s.scoring.score >= before + config.COIN_SCORE


def test_spawner_never_creates_impossible_rows():
    s = GameSession(rng=random.Random(1))
    for _ in range(60 * 240):                 # 4 simulated minutes
        s.player.lane_pos = 1.0               # invulnerable observer
        s.world.update(1 / 60, s.speed, s.difficulty)
        s.difficulty.update(1 / 60)
    rows: dict[float, list] = {}
    for ob in s.world.obstacles:
        rows.setdefault(round(ob.z, 3), []).append(ob)
    assert all(row_is_passable(r) for r in rows.values())


def test_row_passability_rules():
    assert not row_is_passable([Obstacle.train(l, 0, 9) for l in range(3)])
    assert not row_is_passable([Obstacle.barrier(0, 0), Obstacle.overhead(1, 0), Obstacle.barrier(2, 0)])
    assert row_is_passable([Obstacle.barrier(l, 0) for l in range(3)])
    assert row_is_passable([Obstacle.train(0, 0, 9), Obstacle.train(1, 0, 9)])
