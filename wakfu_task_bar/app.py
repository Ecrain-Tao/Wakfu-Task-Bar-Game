"""Wakfu Task Bar Game — lightweight Tkinter prototype 0.1."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

TICK_MS = 50
BG = "#15232e"
PANEL = "#223542"
FG = "#e8e4d6"


class Game(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Wakfu Task Bar Game — Prototype 0.1")
        self.geometry("860x480")
        self.minsize(480, 300)
        self.configure(bg=BG)
        self.kills = self.xp = self.kamas = 0
        self.player_x = 70.0
        self.enemy_x = 350.0
        self.player_hp = 100
        self.enemy_hp = 45
        self.attack_elapsed = 0
        self.respawn_ticks = 0
        self.flash_ticks = 0
        self.active_tab = "Combat"

        self.top = tk.Frame(self, bg=PANEL, highlightbackground="#47606c", highlightthickness=1)
        self.top.place(relx=0, rely=0, relwidth=1, relheight=0.4, height=-16)
        self.heading = tk.Label(self.top, text="Combat", bg=PANEL, fg=FG,
                                font=("Arial", 13, "bold"), anchor="w")
        self.heading.pack(fill="x", padx=12, pady=(8, 3))
        self.menu_canvas = tk.Canvas(self.top, bg=PANEL, highlightthickness=0)
        self.menu_scroll = ttk.Scrollbar(self.top, orient="vertical", command=self.menu_canvas.yview)
        self.menu_canvas.configure(yscrollcommand=self.menu_scroll.set)
        self.menu_scroll.pack(side="right", fill="y")
        self.menu_canvas.pack(side="left", fill="both", expand=True, padx=10)
        self.menu_inner = tk.Frame(self.menu_canvas, bg=PANEL)
        self.menu_window = self.menu_canvas.create_window((0, 0), window=self.menu_inner, anchor="nw")
        self.menu_inner.bind("<Configure>", self._update_scroll)
        self.menu_canvas.bind("<Configure>", self._update_menu_width)
        self.info = tk.Label(self.menu_inner, bg=PANEL, fg=FG, anchor="nw",
                             justify="left", wraplength=700, font=("Arial", 11))
        self.info.pack(anchor="nw", fill="x", pady=4)

        self.battle = tk.Canvas(self, bg="#172b35", highlightthickness=0)
        self.battle.place(relx=0, rely=0.4, y=-16, relwidth=1, relheight=0.6, height=-24)
        self.battle.bind("<Configure>", lambda _: self.draw())

        self.nav = tk.Frame(self, bg=BG)
        self.nav.place(relx=0, rely=1, y=-40, relwidth=1, height=40)
        for name in ("Combat", "Inventaire", "Aptitudes", "Sorts", "Donjons"):
            btn = tk.Button(self.nav, text=name, command=lambda n=name: self.select_tab(n),
                            bg="#253c49", fg=FG, activebackground="#416377",
                            activeforeground=FG, relief="flat", padx=5, bd=0)
            btn.pack(side="left", fill="both", expand=True, padx=1, pady=2)
        self.select_tab("Combat")
        self.after(TICK_MS, self.tick)

    def _update_scroll(self, _):
        self.menu_canvas.configure(scrollregion=self.menu_canvas.bbox("all"))

    def _update_menu_width(self, event):
        self.menu_canvas.itemconfigure(self.menu_window, width=event.width)
        self.info.configure(wraplength=max(180, event.width - 20))

    def select_tab(self, name):
        self.active_tab = name
        self.heading.configure(text=name)
        self.refresh_menu()

    def refresh_menu(self):
        content = {
            "Combat": f"Combat automatique en cours.\\n\\nVictoires : {self.kills}  |  XP : {self.xp}  |  Kamas : {self.kamas}\\n\\nLe héros avance vers le Bouftou, attaque, puis recommence.",
            "Inventaire": "À venir : Équipement | Sac | Coffres | Fusion / Vente.\\n\\n14 emplacements d'équipement prévus.",
            "Aptitudes": "À venir : Intelligence et Force, répartition et réinitialisation des points.",
            "Sorts": "À venir : attaque de base, sort 1, sort 2 et priorités.",
            "Donjons": "À venir : donjons d'Astrub, progression automatique et Boss Ultimes.",
        }
        self.info.configure(text=content[self.active_tab].replace("\\n", "\n"))

    def draw(self):
        c = self.battle
        c.delete("all")
        w = max(1, c.winfo_width())
        h = max(1, c.winfo_height())
        ground = h - 30
        c.create_rectangle(0, ground, w, h, fill="#29483b", outline="")
        c.create_line(0, ground, w, ground, fill="#54765d", width=2)
        scale = min(1.0, max(0.35, w / 520))
        for x, hp, max_hp, color, name in (
            (self.player_x * scale, self.player_hp, 100, "#5ea5db", "Héros"),
            (self.enemy_x * scale, self.enemy_hp, 45, "#d37b72", "Bouftou"),
        ):
            c.create_oval(x - 17, ground - 54, x + 17, ground - 8,
                          fill=color, outline="#d4e5e3", width=2)
            c.create_rectangle(x - 24, ground - 67, x + 24, ground - 61,
                               fill="#4c252c", outline="")
            c.create_rectangle(x - 24, ground - 67, x - 24 + 48 * max(0, hp) / max_hp,
                               ground - 61, fill="#67c68a", outline="")
            c.create_text(x, ground - 81, text=name, fill=FG, font=("Arial", 10))
        if self.flash_ticks:
            c.create_line(self.player_x * scale + 20, ground - 38,
                          self.enemy_x * scale - 18, ground - 38,
                          fill="#f7d47b", width=3)

    def tick(self):
        if self.respawn_ticks:
            self.respawn_ticks -= 1
            if self.respawn_ticks == 0:
                self.enemy_hp = 45
                self.enemy_x = 350
                self.player_x = 70
                self.player_hp = 100
        else:
            self.flash_ticks = max(0, self.flash_ticks - 1)
            distance = self.enemy_x - self.player_x
            if distance > 62:
                self.player_x += min(2.5, distance - 62)
            else:
                self.attack_elapsed += TICK_MS
                if self.attack_elapsed >= 850:
                    self.attack_elapsed = 0
                    self.flash_ticks = 3
                    self.enemy_hp = max(0, self.enemy_hp - 9)
                    if self.enemy_hp == 0:
                        self.kills += 1
                        self.xp += 10
                        self.kamas += 3
                        self.respawn_ticks = 12
                        if self.active_tab == "Combat":
                            self.refresh_menu()
        self.draw()
        self.after(TICK_MS, self.tick)


def main():
    Game().mainloop()
