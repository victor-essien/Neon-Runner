from game import config
from game.systems.difficulty import DifficultyManager
from game.systems.scoring import HighScoreStore, Scoring


def test_distance_and_coins_add_score():
    s = Scoring()
    s.add_distance(100)
    s.add_coin()
    assert s.score == 100 * config.SCORE_PER_METER + config.COIN_SCORE


def test_high_score_persists(tmp_path):
    store = HighScoreStore(tmp_path / "hs.json")
    s = Scoring(store)
    s.add_distance(50)
    assert s.finalize() is True
    assert Scoring(store).high_score == s.score
    s2 = Scoring(store)
    assert s2.finalize() is False            # score 0 does not beat the record


def test_corrupt_high_score_file_is_ignored(tmp_path):
    path = tmp_path / "hs.json"
    path.write_text("not json")
    assert HighScoreStore(path).load() == 0


def test_speed_increases_gradually_and_is_capped():
    d = DifficultyManager()
    speeds = []
    for _ in range(400):
        d.update(1.0)
        speeds.append(d.speed)
    assert speeds == sorted(speeds)
    assert speeds[0] == config.INITIAL_SPEED
    assert max(speeds) <= config.MAX_SPEED
    assert d.gap_seconds >= config.MIN_GAP_SECONDS
