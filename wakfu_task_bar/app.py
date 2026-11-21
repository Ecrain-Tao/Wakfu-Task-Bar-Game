"""Wakfu Task Bar Game — lightweight Tkinter prototype 0.1."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import queue
import sys
from PIL import Image, ImageTk
from pathlib import Path
from wakfu_task_bar.installer import installed_macos_app, stage_macos_update
from wakfu_task_bar.updater import VERSION, check_latest, download_asset
from wakfu_task_bar.engine import GameState, DUNGEONS, xp_needed, MAX_LEVEL

TICK_MS = 50
BG = "#15232e"
PANEL = "#223542"
FG = "#e8e4d6"
SPELL_NAMES = {"jabs": "Jabs", "uppercut": "Uppercut", "charge": "Charge",
               "super_iop_punch": "Super Iop Punch", "wrath": "Colère du Iop"}


class Game(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"Wakfu Task Bar Game — {VERSION}")
        self.geometry("860x480")
        self.minsize(480, 300)
        self.configure(bg=BG)
        self.state = GameState()
        self.state.load()
        self.last_saved = 0
        self.active_tab = "Combat"
        self.update_events = queue.Queue()
        self.latest_release = None
        self.update_busy = False
        self.combat_log = []
        self.floating_hits = []
        self.combat_clock = 0.0
        self.previous_room = None
        self.sprites = self.load_sprites()

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
        self.dungeon_panel = tk.Frame(self.menu_inner, bg=PANEL)
        self.auto_var = tk.BooleanVar(value=self.state.auto_progress)
        tk.Checkbutton(self.dungeon_panel, text="Progression automatique", variable=self.auto_var,
                       command=self.toggle_auto, bg=PANEL, fg=FG, selectcolor=BG,
                       activebackground=PANEL, activeforeground=FG).pack(anchor="w")
        for i, dungeon in enumerate(DUNGEONS):
            tk.Button(self.dungeon_panel, text=dungeon["name"],
                      command=lambda index=i: self.choose_dungeon(index)).pack(anchor="w", pady=2)
        self.spell_panel = tk.Frame(self.menu_inner, bg=PANEL)
        self.spell_vars = {}
        self.spell_priority = list(self.state.priority)
        self.spell_list = tk.Listbox(self.spell_panel, height=4, exportselection=False)
        for spell in self.spell_priority:
            self.spell_list.insert("end", SPELL_NAMES.get(spell, spell))
        self.spell_list.pack(fill="x", pady=3)
        controls = tk.Frame(self.spell_panel, bg=PANEL)
        controls.pack(fill="x")
        tk.Button(controls, text="Monter", command=lambda: self.move_spell(-1)).pack(side="left")
        tk.Button(controls, text="Descendre", command=lambda: self.move_spell(1)).pack(side="left")
        for spell in self.spell_priority:
            var = tk.BooleanVar(value=spell in self.state.equipped)
            self.spell_vars[spell] = var
            tk.Checkbutton(self.spell_panel, text=SPELL_NAMES.get(spell, spell),
                           variable=var, command=self.apply_spells,
                           bg=PANEL, fg=FG, selectcolor=BG,
                           activebackground=PANEL, activeforeground=FG).pack(anchor="w")
        self.update_panel = tk.Frame(self.menu_inner, bg=PANEL)
        self.update_channel = tk.StringVar(value="stable")
        channel_frame = tk.Frame(self.update_panel, bg=PANEL)
        channel_frame.pack(fill="x", pady=4)
        for value, label in (("stable", "Versions stables"), ("experimental", "Versions expérimentales (alpha/beta)")):
            tk.Radiobutton(channel_frame, text=label, value=value, variable=self.update_channel,
                           command=self.change_update_channel, bg=PANEL, fg=FG,
                           selectcolor=BG, activebackground=PANEL,
                           activeforeground=FG).pack(anchor="w")
        self.update_status = tk.Label(self.update_panel, text=f"Version installée : {VERSION}",
                                      bg=PANEL, fg=FG, justify="left", anchor="w", wraplength=600)
        self.update_status.pack(fill="x", pady=5)
        self.check_button = tk.Button(self.update_panel, text="Vérifier les mises à jour", command=self.check_updates)
        self.check_button.pack(anchor="w", pady=4)
        self.download_button = tk.Button(self.update_panel, text="Installer la mise à jour",
                                         command=self.download_update, state="disabled")
        self.download_button.pack(anchor="w", pady=4)
        self.progress = ttk.Progressbar(self.update_panel, maximum=100)
        self.progress.pack(fill="x", pady=4)
        self.update_note = tk.Label(self.update_panel,
                                    text="Sur macOS, mise à jour dans l’application actuelle après confirmation.",
                                    bg=PANEL, fg="#b4c4c8", anchor="w", justify="left", wraplength=600)
        self.update_note.pack(fill="x", pady=4)

        self.battle = tk.Canvas(self, bg="#172b35", highlightthickness=0)
        self.battle.place(relx=0, rely=0.4, y=-16, relwidth=1, relheight=0.6, height=-24)
        self.battle.bind("<Configure>", lambda _: self.draw())

        self.nav = tk.Frame(self, bg=BG)
        self.nav.place(relx=0, rely=1, y=-40, relwidth=1, height=40)
        for name in ("Combat", "Inventaire", "Aptitudes", "Sorts", "Donjons", "Réglages"):
            btn = tk.Button(self.nav, text=name, command=lambda n=name: self.select_tab(n),
                            bg="#ffffff", fg="#000000", activebackground="#e5e5e5",
                            activeforeground="#000000", relief="flat", padx=5, bd=0)
            btn.pack(side="left", fill="both", expand=True, padx=1, pady=2)
        self.select_tab("Combat")
        self.protocol("WM_DELETE_WINDOW", self.close_game)
        self.after(TICK_MS, self.tick)
        self.after(150, self.process_update_events)
        self.after(2500, self.check_updates)

    def _update_scroll(self, _):
        self.menu_canvas.configure(scrollregion=self.menu_canvas.bbox("all"))

    def _update_menu_width(self, event):
        self.menu_canvas.itemconfigure(self.menu_window, width=event.width)
        self.info.configure(wraplength=max(180, event.width - 20))

    def select_tab(self, name):
        self.active_tab = name
        self.heading.configure(text=name)
        if name == "Réglages":
            self.update_panel.pack(fill="x", pady=4)
        else:
            self.update_panel.pack_forget()
        if name == "Sorts":
            self.spell_panel.pack(fill="x", pady=4)
        else:
            self.spell_panel.pack_forget()
        if name == "Donjons":
            self.dungeon_panel.pack(fill="x", pady=4)
        else:
            self.dungeon_panel.pack_forget()
        self.refresh_menu()

    def refresh_menu(self):
        state = self.state
        d = state.dungeon
        content = {
            "Combat": (
                f"Niveau {state.level} | PV {state.hp}/{state.max_hp} | "
                f"XP {state.xp}/{xp_needed(state.level) if state.level < MAX_LEVEL else 'MAX'}\\n"
                f"Victoires : {state.kills} | Kamas : {state.kamas} | Coffres : {state.chests}\\n"
                f"Donjon : {d['name']} — Salle {state.room + 1}/{len(d['rooms']) + 1}\\n"
                f"{state.message}"
            ),
            "Inventaire": f"Coffres collectés : {state.chests}\\nÉquipement, sac, fusion et vente : à venir.",
            "Aptitudes": f"Niveau {state.level}\\nPoints d'aptitudes : à venir.",
            "Sorts": f"Iop — budget {state.pa} PA / {state.pw} PW. Les sorts sont automatiques, par ordre de priorité.",
            "Donjons": f"Donjon actuel : {d['name']}\\nDonjons validés : {len(state.wins)}/{len(DUNGEONS)}",
            "Réglages": "Vérifier et télécharger les mises à jour publiques.",
        }
        self.info.configure(text=content[self.active_tab].replace("\\n", "\n"))

    def apply_spells(self):
        equipped = [s for s in self.spell_priority if self.spell_vars[s].get()]
        self.state.configure_spells(equipped=equipped, priority=self.spell_priority)
        self.state.save()
        self.refresh_menu()

    def move_spell(self, direction):
        selection = self.spell_list.curselection()
        if not selection:
            return
        i = selection[0]
        j = i + direction
        if j < 0 or j >= len(self.spell_priority):
            return
        self.spell_priority[i], self.spell_priority[j] = self.spell_priority[j], self.spell_priority[i]
        self.spell_list.delete(0, "end")
        for spell in self.spell_priority:
            self.spell_list.insert("end", spell)
        self.spell_list.selection_set(j)
        self.apply_spells()

    def toggle_auto(self):
        self.state.auto_progress = self.auto_var.get()
        self.state.save()

    def choose_dungeon(self, index):
        self.state.select_dungeon(index)
        self.state.save()
        self.refresh_menu()

    def close_game(self):
        self.state.save()
        self.destroy()

    def change_update_channel(self):
        self.latest_release = None
        self.download_button.configure(state="disabled")
        self.update_status.configure(text=f"Canal sélectionné : {self.update_channel.get()}")
        self.check_updates()

    def check_updates(self):
        if self.update_busy:
            return
        self.update_busy = True
        self.check_button.configure(state="disabled")
        self.download_button.configure(state="disabled")
        self.update_status.configure(text="Recherche de la dernière version…")
        channel = self.update_channel.get()
        def worker():
            try:
                self.update_events.put(("checked", check_latest(channel)))
            except Exception as exc:
                self.update_events.put(("error", str(exc)))
        threading.Thread(target=worker, daemon=True).start()

    @staticmethod
    def load_sprites():
        """Load static PNGs and alpha frames; missing assets retain placeholders."""
        base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
        sprites = {}
        for key in ("iop_idle", "chacha_idle"):
            path = base / "assets" / "sprites" / (key + ".png")
            try:
                with Image.open(path) as original:
                    image = original.convert("RGBA")
                image.thumbnail((52, 72), Image.Resampling.LANCZOS)
                sprites[key] = [
                    ImageTk.PhotoImage(Image.blend(
                        Image.new("RGBA", image.size, (0, 0, 0, 0)),
                        image, opacity
                    )) for opacity in (1, .75, .5, .25)
                ]
            except (OSError, ValueError) as exc:
                print(f"Unable to load sprite {path}: {exc}", file=sys.stderr)
        bg_path = base / "assets" / "sprites" / "AP_mere_michou.png"
        try:
            with Image.open(bg_path) as original:
                sprites["background"] = original.convert("RGBA").copy()
        except (OSError, ValueError) as exc:
            print(f"Optional background unavailable {bg_path}: {exc}", file=sys.stderr)
        return sprites


    def download_update(self):
        if self.update_busy or not self.latest_release:
            return
        asset = self.latest_release.get("asset")
        if not asset:
            return
        app_path = installed_macos_app()
        if app_path:
            if not messagebox.askyesno(
                "Mettre à jour l'application",
                "Remplacer l'application actuelle et la relancer ? "
                "Une sauvegarde de l'ancienne version sera conservée."
            ):
                return
            folder = Path.home() / ".wakfu-task-bar-game" / "updates"
        else:
            folder_name = filedialog.askdirectory(
                title="Installation automatique indisponible : choisir le dossier de téléchargement"
            )
            if not folder_name:
                return
            folder = Path(folder_name)
        self.update_busy = True
        self.download_button.configure(state="disabled")
        self.check_button.configure(state="disabled")
        self.progress["value"] = 0
        self.update_status.configure(text="Téléchargement en cours…")
        def worker():
            try:
                path = download_asset(
                    asset, folder,
                    lambda done, total: self.update_events.put(("progress", (done, total)))
                )
                self.update_events.put(("install_ready" if app_path else "downloaded", str(path)))
            except Exception as exc:
                self.update_events.put(("error", str(exc)))
        threading.Thread(target=worker, daemon=True).start()

    def process_update_events(self):
        try:
            while True:
                kind, value = self.update_events.get_nowait()
                if kind == "progress":
                    done, total = value
                    if total:
                        self.progress["value"] = min(100, done * 100 / total)
                    self.update_status.configure(text=f"Téléchargement : {done // 1024} Ko")
                elif kind == "checked":
                    self.update_busy = False
                    self.latest_release = value
                    self.check_button.configure(state="normal")
                    if value["newer"] and value["asset"]:
                        self.update_status.configure(text=f"Nouvelle version disponible : {value['tag']}")
                        self.download_button.configure(state="normal")
                    elif value["newer"]:
                        self.update_status.configure(text=f"Version {value['tag']} sans fichier pour ce système.")
                    else:
                        self.update_status.configure(text=f"Vous avez la dernière version ({VERSION}).")
                elif kind == "install_ready":
                    self.update_busy = False
                    try:
                        stage_macos_update(Path(value))
                        self.state.save()
                        self.update_status.configure(text="Mise à jour préparée. Redémarrage…")
                        self.after(200, self.destroy)
                        return
                    except (OSError, RuntimeError, ValueError) as exc:
                        self.check_button.configure(state="normal")
                        self.download_button.configure(state="normal")
                        self.update_status.configure(text=f"Installation impossible : {exc}")
                elif kind == "downloaded":
                    self.update_busy = False
                    self.check_button.configure(state="normal")
                    self.download_button.configure(state="normal")
                    self.progress["value"] = 100
                    self.update_status.configure(text=f"Archive téléchargée : {value}")
                    self.update_note.configure(text="Décompressez l'archive et remplacez l'application après fermeture.")
                elif kind == "error":
                    self.update_busy = False
                    self.check_button.configure(state="normal")
                    self.update_status.configure(text=f"Mise à jour indisponible : {value}")
        except queue.Empty:
            pass
        self.after(150, self.process_update_events)

    def draw(self):
        from wakfu_task_bar.combat_v1 import COLORS, RECHARGE, COST, DURATION
        c = self.battle
        c.delete("all")
        w = max(1, c.winfo_width())
        h = max(1, c.winfo_height())
        ground = h - 26
        state = self.state
        hero = state.hero
        enemies = [m for m in state.battle.monsters if m.alive or m.fade > 0]
        all_x = [hero.x] + [m.x for m in enemies]
        extent = max(440, max(all_x, default=440) + 45)
        scale = min(1.0, max(.25, (w - 32) / extent))
        background = self.sprites.get("background")
        if background is not None:
            # Tkinter Canvas keeps no image references: retain the resized image.
            size = (w, h)
            if getattr(self, "_bg_size", None) != size:
                self._bg_size = size
                self._bg_photo = ImageTk.PhotoImage(background.resize(size, Image.Resampling.LANCZOS))
            c.create_image(0, 0, anchor="nw", image=self._bg_photo)
        else:
            c.create_rectangle(0, ground, w, h, fill="#29483b", outline="")
            c.create_line(0, ground, w, ground, fill="#54765d", width=2)

        def draw_fighter(fighter, color, y_offset=0, front=False):
            x = fighter.x * scale
            base = ground + y_offset
            if fighter.hp <= 0 and fighter.fade <= 0:
                return
            action = fighter.action
            duration = fighter.attack_animation if action == "monster_basic" else DURATION.get(action, 1)
            phase = fighter.action_elapsed / duration if action else 0
            lift = 13 if action == "super_iop_punch" and .2 <= phase <= .8 else 0
            stretch = 8 if action in ("jabs", "uppercut", "super_iop_punch") and phase > .35 else 0
            if front:
                c.create_oval(x-19,base-9,x+19,base+1,fill="#315c75",outline="#8ad5ff",width=2)
            sprite = self.sprites.get("iop_idle" if front else "chacha_idle")
            opacity = max(0, min(1, fighter.fade)) if not fighter.alive else 1
            if sprite:
                frame = min(3, int((1-opacity)*4))
                c.create_image(x, base-28-lift, image=sprite[frame])
            elif fighter.alive:
                c.create_oval(x-14,base-47-lift,x+14+stretch,base-8-lift,
                              fill=color, outline="#ffffff" if front else "#d4e5e3",
                              width=3 if front else 2)
            elif opacity > 0:
                # Shape fallback: stippled original color, never a grey corpse.
                c.create_oval(x-14,base-47-lift,x+14+stretch,base-8-lift,
                              fill=color, stipple="gray50" if opacity>.5 else "gray25",
                              outline="")
            if action == "charge":
                c.create_line(x-27,base-24,x-7,base-24,fill="#75c9f4",width=3)
            if fighter.alive:
                c.create_rectangle(x-21,base-58-lift,x+21,base-53-lift,fill="#4c252c",outline="")
                c.create_rectangle(x-21,base-58-lift,
                                   x-21+42*fighter.hp/max(1,fighter.max_hp),
                                   base-53-lift,fill="#67c68a",outline="")
            c.create_text(x,base-70-lift,text=fighter.name,fill="#8ddaff" if front else FG,
                          font=("Arial",9,"bold" if front else "normal"))
            return x,base

        # Overlapping monsters remain separate in a visual depth stack.
        # Back-to-front painter's order: monsters nearer the bottom are drawn LAST.
        # Stable sorting keeps visual depth consistent for the same monsters.
        ordered_enemies = sorted(enemies, key=lambda m: m.x, reverse=True)
        depth_by_id = {id(monster): i % 4 for i, monster in enumerate(ordered_enemies)}
        for monster in sorted(ordered_enemies, key=lambda m: depth_by_id[id(m)], reverse=True):
            draw_fighter(monster, "#d37b72", -depth_by_id[id(monster)]*28)
        if hero.action == "wrath":
            radius = 100 * scale
            x = hero.x * scale
            c.create_oval(x-radius,ground-30-radius,x+radius,ground-30+radius,
                          outline="#f46d4e",width=3)
        # Hero is always drawn last, and a little lower than enemies when overlapping.
        hero_offset = 0
        draw_fighter(hero,"#5ea5db",hero_offset,True)

        for hit in self.floating_hits:
            fighter = hit["fighter"]
            x = fighter.x*scale
            offset = hero_offset if fighter is hero else -min(
                next((i for i,m in enumerate(ordered_enemies) if m is fighter),0),3)*28
            y = ground+offset-94-(self.combat_clock-hit["time"])*22
            c.create_text(x,y,text=hit["text"],fill=hit["color"],
                          font=("Arial",12,"bold"))

        # Compact cooldown display in the upper-left; never covers character names.
        spell_names = SPELL_NAMES
        equipped = [s for s in hero.priority if s in hero.equipped]
        lines = [("ATTAQUES / RECHARGES", "#f9df99")]
        if hero.action == "jabs":
            lines.append(("Jabs — en cours", "#9bd7ff"))
        else:
            wait = max(0,(1-hero.basic_progress)*hero.basic_wait_seconds()) if hero.basic_started else 0
            lines.append((f"Jabs — {wait:.1f}s" if wait > 0 else "Jabs — prêt","#c9e1e9"))
        active = set(hero.active_spells())
        for spell in equipped:
            if spell not in active:
                status = "hors budget PA/PW"
            elif hero.action == spell:
                status = "en cours"
            elif spell == "uppercut":
                status = f"{min(4,hero.uppercut_count)}/4 attaques"
            elif hero.cooldowns.get(spell,0) > 0:
                status = f"{hero.cooldowns[spell]:.1f}s"
            else:
                status = "prêt"
            lines.append((f"{spell_names.get(spell,spell)} — {status}",
                          "#8be3aa" if status=="prêt" else "#c9e1e9"))
        panel_w = min(240,max(155,w*.3))
        panel_h = 12+len(lines)*17
        c.create_rectangle(7,7,panel_w,7+panel_h,fill="#20313d",outline="#395363")
        for i,(label,color) in enumerate(lines):
            c.create_text(15,19+i*17,anchor="w",text=label,fill=color,font=("Arial",9))

        # The log shows direction and spell, not repeated opaque damage numbers.
        if w >= 480:
            panel_x = max(panel_w+15,w-275)
            c.create_rectangle(panel_x,7,w-7,105,fill="#20313d",outline="#395363")
            c.create_text(panel_x+8,18,anchor="w",text="DERNIERS ÉVÉNEMENTS",
                          fill="#f9df99",font=("Arial",9,"bold"))
            for i,entry in enumerate(self.combat_log[-4:]):
                c.create_text(panel_x+8,37+i*17,anchor="w",text=entry["text"][:45],
                              fill=entry["color"],font=("Arial",9))
        if state.room_exit > 0:
            c.create_text(w/2,20,text="Salle terminée !",fill="#8ae7a8",
                          font=("Arial",14,"bold"))

    def tick(self):
        from wakfu_task_bar.combat_v1 import COLORS
        self.combat_clock += TICK_MS / 1000
        before_battle = self.state.battle
        self.state.tick(TICK_MS / 1000)
        # Room transitions may replace the battle; events from the previous room
        # must still be processed before the new room starts.
        for event in before_battle.events:
            if event.kind == "hit":
                source_is_player = any(f.name == event.source for f in before_battle.players)
                target_side = before_battle.monsters if source_is_player else before_battle.players
                target = next((f for f in target_side if f.name == event.target),None)
                color = COLORS.get(event.element,FG)
                direction = "Infligés" if source_is_player else "Reçus"
                label = f"{direction} : {event.amount} ({event.element})"
                self.combat_log.append({"text":label,"color":color})
                if target is not None:
                    self.floating_hits.append({"fighter":target,"text":f"-{event.amount}",
                                               "color":color,"time":self.combat_clock})
            elif event.kind == "death":
                self.combat_log.append({"text":f"{event.source} : K.O.","color":"#f4c1bc"})
        self.combat_log = self.combat_log[-4:]
        self.floating_hits = [hit for hit in self.floating_hits
                              if self.combat_clock-hit["time"] < 1.4
                              and (hit["fighter"] is self.state.hero
                                   or hit["fighter"] in self.state.battle.monsters)]
        self.last_saved += TICK_MS
        if self.last_saved >= 10000:
            self.last_saved = 0
            self.state.save()
        if self.active_tab in ("Combat","Donjons","Inventaire"):
            self.refresh_menu()
        self.draw()
        self.after(TICK_MS,self.tick)


def main():
    Game().mainloop()
