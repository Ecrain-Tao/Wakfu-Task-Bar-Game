"""Run with python -m unittest discover -s tests."""
import unittest
from unittest.mock import patch

from wakfu_task_bar.engine import DUNGEONS, GameState, xp_needed
from wakfu_task_bar.updater import version_parts


class EngineTests(unittest.TestCase):
    def test_dungeon_starts_with_simultaneous_enemies(self):
        state = GameState()
        self.assertEqual(len(state.monsters), DUNGEONS[0]["rooms"][0])

    def test_dungeon_locked(self):
        state = GameState()
        self.assertFalse(state.select_dungeon(1))
        self.assertEqual(state.dungeon_index, 0)

    def test_death_restores_hp_and_first_room(self):
        state = GameState()
        state.room = 2
        state.hp = 0
        state.respawn_timer = 0.01
        state.tick(0.1)
        self.assertEqual(state.room, 0)
        self.assertEqual(state.hp, state.max_hp)

    def test_level_up(self):
        state = GameState()
        state.grant_xp(xp_needed(1))
        self.assertEqual(state.level, 2)

    def test_save_data(self):
        state = GameState()
        self.assertEqual(state.to_dict()["dungeon_index"], 0)

    def test_versions(self):
        self.assertLess(version_parts("v0.2.0"), version_parts("v0.3.0"))
        self.assertLess(version_parts("v0.2.0-beta"), version_parts("v0.2.0"))
        with self.assertRaises(ValueError):
            version_parts("v0.2.0-unknown")


if __name__ == "__main__":
    unittest.main()
