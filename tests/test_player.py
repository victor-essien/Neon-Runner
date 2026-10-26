from game import config
from game.player.player import Player, PlayerState


def test_left_from_lane_0_is_ignored():
    p = Player()
    assert p.move_left() and p.lane == 0
    assert not p.move_left()
    assert p.lane == 0


def test_right_from_lane_2_is_ignored():
    p = Player()
    p.move_right()
    assert not p.move_right()
    assert p.lane == 2


def test_lane_change_is_smooth():
    p = Player()
    p.move_left()
    p.update(config.LANE_CHANGE_DURATION / 2)
    assert 0.0 < p.lane_pos < 1.0          # interpolating, not teleporting
    p.update(config.LANE_CHANGE_DURATION)
    assert p.lane_pos == 0.0


def test_jump_only_when_grounded():
    p = Player()
    assert p.jump()
    p.update(0.05)
    vy = p.vy
    assert not p.jump()                     # no double jump
    assert p.vy <= vy
    for _ in range(100):
        p.update(0.02)
    assert p.grounded and p.y == 0.0 and p.state is PlayerState.RUNNING


def test_jump_apex_clears_barrier_height():
    p = Player()
    p.jump()
    peak = 0.0
    for _ in range(100):
        p.update(0.01)
        peak = max(peak, p.y)
    assert config.BARRIER_HEIGHT < peak < config.OVERHEAD_BOTTOM + 1.0


def test_slide_returns_to_running():
    p = Player()
    assert p.slide()
    assert p.state is PlayerState.SLIDING and p.height == config.SLIDE_HEIGHT
    p.update(config.SLIDE_DURATION - 0.1)
    assert p.state is PlayerState.SLIDING
    p.update(0.2)
    assert p.state is PlayerState.RUNNING and p.height == config.PLAYER_HEIGHT


def test_slide_in_air_fast_falls_then_slides_on_landing():
    p = Player()
    p.jump()
    p.update(0.1)
    assert not p.slide()
    for _ in range(60):
        p.update(0.01)
    assert p.grounded and p.state is PlayerState.SLIDING
