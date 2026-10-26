"""Central configuration for NEON RUNNER.

Every tunable number lives here so gameplay, rendering and hardware settings
can be changed in one place.
"""
from __future__ import annotations

from pathlib import Path

# --- Paths -------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
HIGH_SCORE_FILE = PROJECT_ROOT / "highscore.json"
LOG_FILE = PROJECT_ROOT / "neon_runner.log"

# --- Window ------------------------------------------------------------------
TITLE = "NEON RUNNER"
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
MAX_FRAME_DT = 0.05          # clamp dt so a stall never teleports the world
DEBUG = False

# --- Serial ------------------------------------------------------------------
SERIAL_BAUDRATE = 115200
SERIAL_PORT = None            # None = auto-detect, or e.g. "COM5" / "/dev/ttyUSB0"
SERIAL_RECONNECT_S = 2.0

# --- Lanes & player (world units are metres) ---------------------------------
LANE_COUNT = 3
START_LANE = 1
LANE_CHANGE_DURATION = 0.18
JUMP_FORCE = 9.0              # m/s  -> apex ~1.56 m
GRAVITY = -26.0               # m/s^2
FAST_FALL_SPEED = 16.0        # DOWN while airborne
JUMP_BUFFER_S = 0.10          # early JUMP press is remembered this long
PLAYER_HEIGHT = 1.8
SLIDE_HEIGHT = 0.7
SLIDE_DURATION = 0.65
PLAYER_HALF_DEPTH = 0.4

# --- Collision ---------------------------------------------------------------
LANE_HIT_WIDTH = 0.5          # lane-units: |player_lane - obstacle_lane| below this = same lane
VERTICAL_FORGIVENESS = 0.05
COIN_PICKUP_DEPTH = 0.9
COIN_PICKUP_LANE = 0.6
COIN_HEIGHT = 0.8

# --- Obstacles ---------------------------------------------------------------
BARRIER_HEIGHT = 0.8
BARRIER_DEPTH = 0.7
OVERHEAD_BOTTOM = 1.1
OVERHEAD_TOP = 2.2
TRAIN_HEIGHT = 3.2
TRAIN_MIN_LENGTH = 7.0
TRAIN_MAX_LENGTH = 11.0

# --- Speed & difficulty ------------------------------------------------------
INITIAL_SPEED = 16.0          # m/s at multiplier 1.0
MAX_SPEED = 34.0
# (seconds, speed multiplier) - linearly interpolated, flat after the last point
DIFFICULTY_CURVE = ((0, 1.0), (30, 1.0), (60, 1.2), (90, 1.4), (120, 1.6), (180, 1.9), (300, 2.1))
BASE_GAP_SECONDS = 1.5        # reaction time between patterns (shrinks over time)
MIN_GAP_SECONDS = 0.85
GAP_DECAY_PER_SECOND = 0.0045
TIER_TIMES = (25.0, 60.0)     # patterns unlock at these times

# --- Spawning ----------------------------------------------------------------
SPAWN_Z = 110.0
SPAWN_START_Z = 45.0
DESPAWN_Z = -12.0

# --- Scoring -----------------------------------------------------------------
SCORE_PER_METER = 10
COIN_SCORE = 50

# --- Perspective camera ------------------------------------------------------
HORIZON_Y = 240
GROUND_Y = 640                # screen y of the player's feet
LANE_WIDTH_PX = 230.0
PX_PER_M = 95.0
FOCAL = 14.0
EYE_HEIGHT = (GROUND_Y - HORIZON_Y) / PX_PER_M

# --- Flow --------------------------------------------------------------------
COUNTDOWN_STEP_S = 0.8
GAME_OVER_INPUT_DELAY_S = 1.0
BOOT_SCREEN_S = 3.0

# --- Palette -----------------------------------------------------------------
CYAN = (30, 235, 255)
MAGENTA = (255, 60, 200)
YELLOW = (255, 214, 64)
ORANGE = (255, 130, 50)
RED = (255, 70, 90)
GREEN = (80, 255, 150)
WHITE = (240, 240, 255)
DIM = (130, 130, 175)
FOG_COLOR = (44, 18, 80)
