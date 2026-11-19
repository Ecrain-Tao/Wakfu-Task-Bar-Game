"""Deterministic room-based idle RPG combat and local save data."""
from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from pathlib import Path

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
        self.spawn_room()

    @property
    def max_hp(self):
        return 100 + (self.level - 1) * 10

    @property
    def dungeon(self):
        return DUNGEONS[self.dungeon_index]

    def spawn_room(self):
        self.player_x = 60.0
        self.attack_timer = 0.0
        self.monsters = []
        boss = self.room >= len(self.dungeon["rooms"])
        count = 1 if boss else self.dungeon["rooms"][self.room]
        hp = self.dungeon["hp"] * (3 if boss else 1)
        for i in range(count):
            self.monsters.append(Monster(
                ("Chef " if boss else "") + self.dungeon["enemy"],
                hp, hp, 260.0 + i * 66.0,
                self.dungeon["damage"] * (2 if boss else 1),
            ))

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
        if not self.monsters:
            return
        living = [m for m in self.monsters if m.hp > 0]
        if not living:
            return
        target = min(living, key=lambda m: abs(m.x - self.player_x))
        if target.x - self.player_x > 54:
            self.player_x += min(95 * dt, target.x - self.player_x - 54)
        else:
            self.attack_timer += dt
            if self.attack_timer >= 0.8:
                self.attack_timer = 0
                target.hp = max(0, target.hp - (10 + self.level * 2))
                if target.hp == 0:
                    self.kills += 1
                    self.kamas += self.dungeon["kamas"]
                    self.grant_xp(self.dungeon["xp"])
                    if self.kills % 7 == 0:
                        self.chests += 1
                        self.message = "Coffre obtenu !"
        for monster in living:
            if monster.hp <= 0:
                continue
            if monster.x - self.player_x > 45:
                monster.x -= min(48 * dt, monster.x - self.player_x - 45)
            else:
                monster.attack_timer += dt
                if monster.attack_timer >= 1.4:
                    monster.attack_timer = 0
                    self.hp = max(0, self.hp - monster.damage)
                    if self.hp == 0:
                        self.message = "Défaite : retour à la première salle"
                        self.respawn_timer = 1.0
                        return
        if all(m.hp <= 0 for m in self.monsters):
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
                self.spawn_room()

    def to_dict(self):
        return {
            "level": self.level, "xp": self.xp, "kamas": self.kamas,
            "kills": self.kills, "chests": self.chests,
            "wins": sorted(self.wins), "dungeon_index": self.dungeon_index,
            "auto_progress": self.auto_progress,
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
            self.hp = self.max_hp
            self.room = 0
            self.spawn_room()
        except (ValueError, TypeError, OSError, KeyError):
            self.message = "Sauvegarde illisible : nouvelle partie temporaire."
