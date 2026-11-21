"""Combat V1: deterministic event-timed Iop and monster actions.

All times are seconds. No Tk dependency; suitable for unit tests.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from math import floor
import random

ELEMENTS = ("fire", "water", "earth", "air")
COLORS = {"fire":"#ef5350","water":"#42a5f5","earth":"#66bb6a","air":"#f48fb1","light":"#ffee58","stasis":"#ab47bc"}
RANGE = {"jabs":40,"uppercut":40,"charge":200,"super_iop_punch":60,"wrath":100}
COST = {"uppercut":(0,1),"charge":(1,0),"super_iop_punch":(4,0),"wrath":(4,1)}
DURATION = {"jabs":.8,"uppercut":.6,"charge":.6,"super_iop_punch":1.0,"wrath":1.5}
RECHARGE = {"charge":10.0,"super_iop_punch":12.0,"wrath":20.0}
DEFAULT_PRIORITY = ["wrath","super_iop_punch","uppercut","charge"]

def half_up(value):
    return max(0, int(Decimal(str(max(0, value))).quantize(Decimal("1"), rounding=ROUND_HALF_UP)))

def resist_percent(raw):
    return floor((1 - 0.8 ** (raw / 100)) * 100 + 1e-9)

@dataclass
class Stats:
    mastery: dict = field(default_factory=lambda:{e:0 for e in ELEMENTS})
    melee: float = 0
    distance: float = 0
    critical_mastery: float = 0
    berserk: float = 0
    heal_mastery: float = 0
    inflicted: float = 0
    healing_done: float = 0
    healing_received: float = 0
    critical_chance: float = 0
    parry_chance: float = 0
    attack_speed: float = 0
    resist: dict = field(default_factory=lambda:{e:0 for e in ELEMENTS})
    fixed_damage: float = 0
    barrier: float = 0
    barrier_charges: int = 0
    incurable: float = 0

def element_pair(element, caster, target):
    if element == "light":
        chosen = max(ELEMENTS, key=lambda e: caster.stats.mastery.get(e,0))
        return chosen, chosen
    if element == "stasis":
        best = max(ELEMENTS, key=lambda e: caster.stats.mastery.get(e,0))
        weak = min(ELEMENTS, key=lambda e: resist_percent(target.stats.resist.get(e,0)))
        return best, weak
    return element, element

def calculate_damage(lines, caster, target, category, critical=False, parried=False):
    """One impact; multiple elemental lines share fixed damage/barrier/parry/rounding."""
    amount = 0.0
    for element, base in lines:
        mastery_element, resist_element = element_pair(element, caster, target)
        mastery = caster.stats.mastery.get(mastery_element,0)
        mastery += caster.stats.melee if category == "melee" else caster.stats.distance
        if caster.hp < caster.max_hp / 2:
            mastery += caster.stats.berserk
        if critical:
            mastery += caster.stats.critical_mastery
        resistance = resist_percent(target.stats.resist.get(resist_element,0))
        amount += base * (1 + mastery/100) * (1.25 if critical else 1) * (1 + caster.stats.inflicted/100) * (1 - resistance/100)
    amount += caster.stats.fixed_damage
    if target.stats.barrier_charges > 0:
        amount -= target.stats.barrier
        target.stats.barrier_charges -= 1
    if parried:
        amount *= .8
    return half_up(amount)

def calculate_heal(base, caster, target, critical=False):
    mastery = caster.stats.heal_mastery
    if caster.hp < caster.max_hp / 2:
        mastery += caster.stats.berserk
    if critical:
        mastery += caster.stats.critical_mastery
    amount = base * (1 + mastery/100) * (1.25 if critical else 1)
    amount *= 1 + (caster.stats.healing_done + target.stats.healing_received)/100
    amount *= 1 - target.stats.incurable/100
    return min(target.max_hp-target.hp, half_up(amount))

@dataclass
class Fighter:
    name: str
    x: float
    hp: int
    max_hp: int
    damage: int = 3
    side: int = 1
    speed: float = 95
    reach: float = 40
    attack_animation: float = .8
    attack_wait: float = 1.5
    stats: Stats = field(default_factory=Stats)
    radius: float = 0
    priority: list = field(default_factory=lambda:list(DEFAULT_PRIORITY))
    equipped: list = field(default_factory=lambda:list(DEFAULT_PRIORITY))
    pa: int = 6
    pw: int = 2
    basic_progress: float = 1.0
    basic_started: bool = False
    action: str = ""
    action_elapsed: float = 0
    action_target: object = None
    locked_targets: list = field(default_factory=list)
    critical: bool = False
    impact_index: int = 0
    cooldowns: dict = field(default_factory=dict)
    uppercut_count: int = 0
    controls: list = field(default_factory=list)
    interrupted_recovery: float = 0
    fade: float = 0
    kills: int = 0
    alive: bool = True
    last_attack_speed: float = 0
    charge_start: float = 0
    charge_destination: float = 0
    charge_intercepted: bool = False
    charge_last_target: object = None
    bonus_crit: float = 0

    def is_blocked(self, kind):
        return any(kind in c for c in self.controls)

    def active_spells(self):
        remaining_pa, remaining_pw = self.pa, self.pw
        result = []
        for spell in self.equipped:
            if spell not in COST:
                continue
            a, w = COST[spell]
            if a <= remaining_pa and w <= remaining_pw:
                result.append(spell)
                remaining_pa -= a
                remaining_pw -= w
        return result

    def basic_wait_seconds(self):
        speed = max(-50, min(200, self.stats.attack_speed))
        return self.attack_wait / (1 + speed/100)

    def update_loadout(self, spells=None, priority=None, pa=None, pw=None):
        before = set(self.active_spells())
        if spells is not None:
            self.equipped = list(dict.fromkeys(spells))
        if priority is not None:
            self.priority = list(dict.fromkeys(priority))
        if pa is not None:
            self.pa = pa
        if pw is not None:
            self.pw = pw
        after = set(self.active_spells())
        for spell in before ^ after:
            self.cooldowns[spell] = RECHARGE.get(spell,0) if spell != "uppercut" else 0
            if spell == "uppercut":
                self.uppercut_count = 0

@dataclass
class Event:
    kind: str
    source: str
    target: str = ""
    amount: int = 0
    element: str = ""
    spell: str = ""

class Battle:
    def __init__(self, players, monsters, seed=1):
        self.players = players
        self.monsters = monsters
        self.rng = random.Random(seed)
        self.time = 0.0
        self.events = []
        self.finished = False
        self.winner = None
        self.monster_kills = 0

    def opponents(self, actor):
        return self.monsters if actor.side == 1 else self.players

    def distance(self, a, b):
        return max(0, abs(a.x-b.x)-b.radius)

    def target(self, actor, reach=None):
        candidates = [f for f in self.opponents(actor) if f.alive and (reach is None or self.distance(actor,f) <= reach + 1e-7)]
        if not candidates:
            return None
        near = min(self.distance(actor,f) for f in candidates)
        ties = [f for f in candidates if abs(self.distance(actor,f)-near) < 1e-7]
        most_hp = max(f.hp for f in ties)
        ties = [f for f in ties if f.hp == most_hp]
        return self.rng.choice(ties)

    def emit(self, kind, actor, target=None, amount=0, element="", spell=""):
        self.events.append(Event(kind,actor.name,target.name if target else "",amount,element,spell))

    def kill(self, actor, victim):
        victim.hp = 0
        victim.alive = False
        victim.fade = 1.0
        victim.action = ""
        victim.locked_targets.clear()
        victim.action_target = None
        actor.kills += 1
        if victim.side == 2:
            self.monster_kills += 1
        self.emit("death",victim)
        if not any(f.alive for f in self.opponents(actor)):
            self.finished = True
            self.winner = actor.side
            for f in self.players+self.monsters:
                if f.alive and f.action and f.action != "charge":
                    f.action_elapsed = min(f.action_elapsed, DURATION.get(f.action,f.attack_animation))
    
    def hit(self, actor, target, lines, category, spell):
        if not target or not target.alive:
            return False
        parried = self.rng.random()*100 < target.stats.parry_chance
        amount = calculate_damage(lines,actor,target,category,actor.critical,parried)
        actual = min(target.hp,amount)
        target.hp -= actual
        self.emit("hit",actor,target,actual,lines[0][0],spell)
        if target.hp <= 0:
            self.kill(actor,target)
            return True
        return False

    def start(self, actor, action, target):
        actor.action = action
        actor.action_elapsed = 0.0
        actor.action_target = target
        actor.impact_index = 0
        actor.critical = self.rng.random()*100 < actor.stats.critical_chance
        actor.locked_targets = []
        if action == "wrath":
            actor.locked_targets = [m for m in self.opponents(actor) if m.alive and self.distance(actor,m) <= 100]
        if action == "charge":
            actor.charge_start = actor.x
            actor.charge_destination = target.x
            actor.charge_last_target = target
            actor.charge_intercepted = False
        actor.bonus_crit = 0
        if action == "jabs" and actor.side == 1:
            actor.uppercut_count += 1
        if action == "charge":
            actor.uppercut_count += 1
        if action in ("jabs", "monster_basic"):
            actor.basic_progress = 0.0
            actor.basic_started = False
        self.emit("start",actor,target,spell=action)

    def castable(self, actor, spell):
        if spell not in actor.active_spells() or actor.cooldowns.get(spell,0)>0:
            return False
        if spell == "uppercut" and actor.uppercut_count < 4:
            return False
        return self.target(actor,RANGE[spell]) is not None

    def choose(self, actor):
        if actor.side == 1 and not actor.is_blocked("spell"):
            for spell in actor.priority:
                if self.castable(actor,spell):
                    self.start(actor,spell,self.target(actor,RANGE[spell]))
                    if spell == "uppercut":
                        actor.uppercut_count = 0
                    return
        if not actor.is_blocked("basic") and (not actor.basic_started or actor.basic_progress >= 1):
            target = self.target(actor,actor.reach)
            if target:
                self.start(actor,"jabs" if actor.side==1 else "monster_basic",target)
                return
        if not actor.is_blocked("move"):
            target = self.target(actor)
            if target and self.distance(actor,target) > actor.reach:
                step = min(actor.speed * self.step, self.distance(actor,target)-actor.reach)
                # Opponents block movement; allies do not.
                new_x = actor.x + step*(1 if target.x>actor.x else -1)
                for blocker in self.opponents(actor):
                    if not blocker.alive:
                        continue
                    old_delta = blocker.x-actor.x
                    new_delta = blocker.x-new_x
                    if old_delta*new_delta <= 0 or abs(new_delta)<blocker.radius:
                        new_x = blocker.x - (blocker.radius if old_delta>=0 else -blocker.radius)
                actor.x = new_x

    def impact(self, actor, moment):
        action = actor.action
        target = actor.action_target
        if action == "jabs":
            # Four distinct impacts; redirect after death to any living enemy in reach.
            element = ELEMENTS[actor.impact_index]
            if not target or not target.alive:
                target = self.target(actor,40)
            if target and target.alive:
                self.hit(actor,target,[(element,1)],"melee",action)
        elif action == "uppercut":
            if target and target.alive:
                self.hit(actor,target,[("light",5)],"melee",action)
        elif action == "super_iop_punch":
            if target and target.alive:
                if self.hit(actor,target,[("fire",8)],"melee",action):
                    actor.bonus_crit = 1
        elif action == "wrath":
            if actor.impact_index == 0:
                actor.bonus_crit = 0
                for m in list(actor.locked_targets):
                    if m.alive and self.hit(actor,m,[("fire",6)],"melee",action):
                        actor.bonus_crit = 1
            elif actor.bonus_crit:
                for m in list(actor.locked_targets):
                    if m.alive:
                        self.hit(actor,m,[("fire",1)],"melee",action)
        elif action == "charge":
            if target and target.alive and self.distance(actor,target)<=1e-6:
                self.hit(actor,target,[("earth",3)],"distance",action)
        elif action == "monster_basic":
            if target and target.alive:
                self.hit(actor,target,[("earth",actor.damage)],"melee",action)

    def finish(self, actor):
        action = actor.action
        actor.action = ""
        actor.action_target = None
        actor.locked_targets = []
        if action == "super_iop_punch":
            actor.cooldowns[action] = 9 if actor.bonus_crit else 12
        elif action in RECHARGE:
            actor.cooldowns[action] = RECHARGE[action]
        if action in ("jabs","monster_basic"):
            actor.basic_progress = 0
            actor.basic_started = True
        self.emit("finish",actor,spell=action)

    def advance_action(self, actor, dt):
        action = actor.action
        if not action:
            return
        duration = actor.attack_animation if action=="monster_basic" else DURATION[action]
        if self.finished:
            actor.action_elapsed = min(duration, actor.action_elapsed + 3*dt)
            if actor.action_elapsed >= duration - 1e-8:
                self.finish(actor)
            return
        old = actor.action_elapsed
        new = min(duration,old+dt)
        if action == "charge":
            target = actor.charge_last_target
            if target and target.alive:
                actor.charge_destination = target.x
            destination = actor.charge_destination
            direction = 1 if destination >= actor.charge_start else -1
            if not actor.charge_intercepted:
                proposed = actor.charge_start + (destination-actor.charge_start) * (new/duration)
                # Crossing an enemy hitbox stops the dash for the rest of the animation.
                blockers = [f for f in self.opponents(actor) if f.alive
                            and (f.x-actor.x)*direction >= -1e-7
                            and (f.x-proposed)*direction <= f.radius+1e-7]
                if blockers:
                    victim = min(blockers,key=lambda f:abs(f.x-actor.x))
                    actor.x = victim.x-direction*victim.radius
                    actor.action_target = victim
                    actor.charge_intercepted = True
                else:
                    actor.x = proposed
                    actor.action_target = target
        if action == "jabs":
            moments = (.2,.4,.6,.8)
        elif action == "uppercut":
            moments = (.6,)
        elif action == "charge":
            moments = (.6,)
        elif action == "super_iop_punch":
            moments = (.8,)
        elif action == "wrath":
            moments = (.7,.9)
        else:
            moments = (duration,)
        # A consumed-impact cursor prevents repeated hits at floating-point boundaries.
        while actor.impact_index < len(moments):
            index = actor.impact_index
            moment = moments[index]
            if moment > new + 1e-8 or not actor.alive or not actor.action:
                break
            actor.impact_index += 1
            self.impact(actor,moment)
        actor.action_elapsed = new
        if new >= duration-1e-8 and actor.alive and actor.action:
            self.finish(actor)

    def tick(self, dt):
        if dt <= 0:
            return []
        self.events = []
        # Small substeps preserve ordered impact times and collision checks.
        remaining = dt
        while remaining > 1e-9:
            step = min(.01,remaining)
            remaining -= step
            self.step = step
            self.time += step
            fighters = self.players+self.monsters
            for f in fighters:
                if not f.alive:
                    f.fade = max(0,f.fade-step)
                    continue
                if f.basic_started:
                    f.basic_progress = min(1,f.basic_progress+step/f.basic_wait_seconds())
                for name in list(f.cooldowns):
                    f.cooldowns[name] = max(0,f.cooldowns[name]-step)
                if f.interrupted_recovery>0 and not f.is_blocked("spell"):
                    f.interrupted_recovery=max(0,f.interrupted_recovery-step)
                if f.action and (f.is_blocked("spell") if f.action not in ("jabs","monster_basic") else f.is_blocked("basic")):
                    f.action=""
                    f.action_target=None
                    f.interrupted_recovery=max(f.interrupted_recovery,.3)
            for f in fighters:
                if f.alive and f.action:
                    self.advance_action(f,step)
            if not self.finished:
                for f in fighters:
                    if f.alive and not f.action and f.interrupted_recovery<=0:
                        self.choose(f)
        return self.events
