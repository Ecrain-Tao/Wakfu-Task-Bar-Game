"""Deterministic room-based idle RPG combat and local save data."""
from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from .combat_v1 import Battle, Fighter, Stats, DEFAULT_PRIORITY

SAVE_DIR = Path.home() / ".wakfu-task-bar-game"
SAVE_FILE = SAVE_DIR / "save.json"

DUNGEONS = (
    {"name": "Prairie des Bouftous", "level": 1, "rooms": (2, 3, 2), "enemy": "Bouftou", "hp": 35, "damage": 3, "xp": 10, "kamas": 3},
    {"name": "Sous-bois des Tofus", "level": 4, "rooms": (3, 3, 4), "enemy": "Tofu", "hp": 27, "damage": 4, "xp": 12, "kamas": 4},
    {"name": "Égouts d'Astrub", "level": 8, "rooms": (3, 4, 4), "enemy": "Larve", "hp": 54, "damage": 5, "xp": 18, "kamas": 6},
)
MAX_LEVEL = 35


def xp_needed(level: int) -> int:
    return 50 + 25 * level


@dataclass
class Monster:
    name: str
    hp: int
    max_hp: int
    x: float
    damage: int
    attack_timer: float = 0.0


class GameState:
    def __init__(self):
        self.level = 1
        self.xp = 0
        self.kamas = 0
        self.kills = 0
        self.chests = 0
        self.wins = set()
        self.dungeon_index = 0
        self.room = 0
        self.auto_progress = True
        self.hp = self.max_hp
        self.player_x = 60.0
        self.monsters = []
        self.attack_timer = 0.0
        self.respawn_timer = 0.0
        self.message = ""
        self.priority = list(DEFAULT_PRIORITY)
        self.equipped = list(DEFAULT_PRIORITY)
        self.pa, self.pw = 6, 2
        self.battle = None
        self.room_exit = 0.0
        self.spawn_room()

    @property
    def max_hp(self):
        return 100 + (self.level - 1) * 10

    @property
    def dungeon(self):
        return DUNGEONS[self.dungeon_index]

    def spawn_room(self):
        old_hero = getattr(self, "hero", None)
        old_cooldowns = dict(old_hero.cooldowns) if old_hero and old_hero.alive else {}
        old_uppercut = old_hero.uppercut_count if old_hero and old_hero.alive else 0
        old_basic_progress = old_hero.basic_progress if old_hero and old_hero.alive else 1.0
        self.player_x = 60.0
        self.attack_timer = 0.0
        self.monsters = []
        boss = self.room >= len(self.dungeon["rooms"])
        count = 1 if boss else self.dungeon["rooms"][self.room]
        hp = self.dungeon["hp"] * (3 if boss else 1)
        self.hero = Fighter("Iop", 60.0, self.hp, self.max_hp, side=1, speed=95)
        self.hero.priority = list(self.priority)
        self.hero.equipped = list(self.equipped)
        self.hero.pa, self.hero.pw = self.pa, self.pw
        self.hero.cooldowns = old_cooldowns
        self.hero.uppercut_count = old_uppercut
        self.hero.basic_progress = old_basic_progress
        enemies = []
        for i in range(count):
            monster = Monster(
                ("Chef " if boss else "") + self.dungeon["enemy"],
                hp, hp, 260.0 + i * 66.0,
                self.dungeon["damage"] * (2 if boss else 1),
            )
            self.monsters.append(monster)
            enemies.append(Fighter(monster.name,monster.x,monster.hp,monster.max_hp,
                                   damage=monster.damage,side=2,speed=48,reach=45,
                                   attack_animation=.5,attack_wait=1.4,
                                   radius=20 if boss else 0))
        self.battle = Battle([self.hero], enemies)
        self.room_exit = 0.0
        self._sync_battle()

    def _sync_battle(self):
        self.player_x = self.hero.x
        self.hp = self.hero.hp
        for old, new in zip(self.monsters,self.battle.monsters):
            old.x,old.hp = new.x,new.hp

    def configure_spells(self, equipped=None, priority=None):
        if equipped is not None:
            self.equipped = list(equipped)
        if priority is not None:
            self.priority = list(priority)
        self.hero.update_loadout(spells=self.equipped,priority=self.priority)

    def select_dungeon(self, index: int):
        if not 0 <= index < len(DUNGEONS):
            return False
        if index > 0 and (index - 1) not in self.wins:
            self.message = "Donjon verrouillé : validez le précédent."
            return False
        self.dungeon_index = index
        self.room = 0
        self.hp = self.max_hp
        self.respawn_timer = 0
        self.hero.alive = False
        self.spawn_room()
        self.message = "Nouveau donjon : " + self.dungeon["name"]
        return True

    def grant_xp(self, amount: int):
        self.xp += amount
        while self.level < MAX_LEVEL and self.xp >= xp_needed(self.level):
            self.xp -= xp_needed(self.level)
            self.level += 1
            self.message = f"Niveau supérieur ! Niveau {self.level}"
        if self.level >= MAX_LEVEL:
            self.xp = 0

    def tick(self, dt: float):
        if self.respawn_timer > 0:
            self.respawn_timer -= dt
            if self.respawn_timer <= 0:
                self.hp = self.max_hp
                self.room = 0
                self.spawn_room()
            return
        if self.room_exit > 0:
            self.room_exit -= dt
            self.hero.x += 160 * dt
            self.player_x = self.hero.x
            for name in self.hero.cooldowns:
                self.hero.cooldowns[name] = max(0, self.hero.cooldowns[name]-dt)
            if self.room_exit <= 0:
                self._advance_room()
            return
        previous_kills = self.battle.monster_kills
        self.battle.tick(dt)
        self._sync_battle()
        gained = self.battle.monster_kills - previous_kills
        for _ in range(gained):
            self.kills += 1
            self.kamas += self.dungeon["kamas"]
            self.grant_xp(self.dungeon["xp"])
            if self.kills % 7 == 0:
                self.chests += 1
                self.message = "Coffre obtenu !"
        if self.battle.finished and self.battle.winner == 2:
            self.message = "Défaite : retour à la première salle"
            self.respawn_timer = 1.0
            return
        if self.battle.finished and self.battle.winner == 1:
            self.room_exit = 0.8

    def _advance_room(self):
        if self.room < len(self.dungeon["rooms"]):
            self.room += 1
            self.spawn_room()
        else:
            completed = self.dungeon_index
            self.wins.add(completed)
            self.message = "Donjon terminé : " + self.dungeon["name"]
            if self.auto_progress and completed + 1 < len(DUNGEONS):
                self.dungeon_index += 1
            self.room = 0
            self.hp = self.max_hp
            self.hero.alive = False
            self.spawn_room()

    def to_dict(self):
        return {
            "level": self.level, "xp": self.xp, "kamas": self.kamas,
            "kills": self.kills, "chests": self.chests,
            "wins": sorted(self.wins), "dungeon_index": self.dungeon_index,
            "auto_progress": self.auto_progress,
            "equipped": self.equipped, "priority": self.priority,
        }

    def save(self):
        SAVE_DIR.mkdir(parents=True, exist_ok=True)
        tmp = SAVE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        os.replace(tmp, SAVE_FILE)

    def load(self):
        if not SAVE_FILE.exists():
            return
        try:
            data = json.loads(SAVE_FILE.read_text(encoding="utf-8"))
            self.level = min(MAX_LEVEL, max(1, int(data.get("level", 1))))
            self.xp = max(0, int(data.get("xp", 0)))
            self.kamas = max(0, int(data.get("kamas", 0)))
            self.kills = max(0, int(data.get("kills", 0)))
            self.chests = max(0, int(data.get("chests", 0)))
            self.wins = {int(i) for i in data.get("wins", []) if 0 <= int(i) < len(DUNGEONS)}
            index = int(data.get("dungeon_index", 0))
            self.dungeon_index = index if 0 <= index < len(DUNGEONS) and (index == 0 or index - 1 in self.wins) else 0
            self.auto_progress = bool(data.get("auto_progress", True))
            self.equipped = [s for s in data.get("equipped", DEFAULT_PRIORITY) if s in DEFAULT_PRIORITY]
            self.priority = [s for s in data.get("priority", DEFAULT_PRIORITY) if s in DEFAULT_PRIORITY]
            self.hp = self.max_hp
            self.room = 0
            self.spawn_room()
        except (ValueError, TypeError, OSError, KeyError):
            self.message = "Sauvegarde illisible : nouvelle partie temporaire."
