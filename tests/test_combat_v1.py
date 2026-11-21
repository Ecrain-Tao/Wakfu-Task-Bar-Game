"""Regression tests for combat rules. Run: python -m unittest discover -s tests."""
import unittest
from wakfu_task_bar.combat_v1 import (
    Battle, Fighter, Stats, calculate_damage, calculate_heal, resist_percent,
)

class CombatV1Tests(unittest.TestCase):
    def test_resistance_conversion(self):
        self.assertEqual(resist_percent(0), 0)
        self.assertEqual(resist_percent(100), 19)

    def test_half_up_and_multielement(self):
        p = Fighter("Iop", 0, 100, 100)
        m = Fighter("Monster", 10, 100, 100, side=2)
        self.assertEqual(calculate_damage([("fire",1),("water",1)],p,m,"melee"),2)

    def test_light_highest_mastery(self):
        p = Fighter("Iop", 0, 100, 100)
        m = Fighter("Monster", 10, 100, 100, side=2)
        p.stats.mastery["fire"]=100
        self.assertEqual(calculate_damage([("light",5)],p,m,"melee"),10)

    def test_healing_caps_hp(self):
        p=Fighter("Iop",0,95,100)
        self.assertEqual(calculate_heal(20,p,p),5)

    def test_jabs_impacts(self):
        p=Fighter("Iop",0,100,100)
        p.equipped=[]
        m=Fighter("Monster",20,100,100,side=2)
        m.speed=0
        m.attack_animation=10
        b=Battle([p],[m])
        b.tick(.21)
        self.assertEqual(m.hp,99)
        b.tick(.6)
        self.assertEqual(m.hp,96)

    def test_target_dies_mid_monster_animation(self):
        p=Fighter("Iop",0,1,1)
        m=Fighter("Monster",20,100,100,side=2)
        b=Battle([p],[m])
        b.start(m,"monster_basic",p)
        p.alive=False
        p.hp=0
        b.tick(.6)
        self.assertEqual(p.hp,0)
        self.assertEqual(m.action,"")

    def test_killed_attacker_cancels_future_impacts(self):
        p=Fighter("Iop",0,100,100)
        m=Fighter("Monster",20,100,100,side=2)
        b=Battle([p],[m])
        b.start(m,"monster_basic",p)
        m.alive=False
        m.hp=0
        b.tick(1)
        self.assertEqual(p.hp,100)

    def test_loadout_budget(self):
        p=Fighter("Iop",0,100,100)
        self.assertEqual(p.active_spells(),["wrath","uppercut","charge"])
        p.update_loadout(pa=1,pw=1)
        self.assertEqual(p.active_spells(),["uppercut","charge"])

if __name__ == "__main__":
    unittest.main()
