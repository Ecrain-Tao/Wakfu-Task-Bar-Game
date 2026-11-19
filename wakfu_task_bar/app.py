"""Resizable PySide6 idle-combat prototype."""
from __future__ import annotations

import math
import sys

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QBrush, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication, QFrame, QGraphicsScene, QGraphicsView, QHBoxLayout,
    QLabel, QMainWindow, QProgressBar, QPushButton, QScrollArea,
    QSizePolicy, QTabWidget, QVBoxLayout, QWidget,
)

TICK_MS = 50


class CombatScene(QGraphicsView):
    """Draw the small 2D auto-battle without external art assets."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene_data = QGraphicsScene(self)
        self.setScene(self.scene_data)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QColor("#172b35"))
        self.player_x = 70.0
        self.enemy_x = 350.0
        self.player_hp = 100
        self.enemy_hp = 45
        self.attack_flash = 0
        self.enemy_flash = 0
        self.setMinimumHeight(140)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.render_scene()

    def render_scene(self):
        s = self.scene_data
        s.clear()
        w = max(420, self.viewport().width())
        h = max(140, self.viewport().height())
        s.setSceneRect(0, 0, w, h)
        ground = h - 36
        s.addRect(0, ground, w, 36, QPen(Qt.PenStyle.NoPen), QBrush(QColor("#29483b")))
        s.addLine(0, ground, w, ground, QPen(QColor("#54765d"), 2))
        scale = min(1.0, w / 520)
        px = self.player_x * scale
        ex = self.enemy_x * scale
        for x, hp, fill, flash in [
            (px, self.player_hp, "#5ea5db", self.attack_flash),
            (ex, self.enemy_hp, "#d37b72", self.enemy_flash),
        ]:
            color = QColor("#ffffff") if flash else QColor(fill)
            s.addEllipse(x - 17, ground - 54, 34, 46, QPen(QColor("#d4e5e3"), 2), QBrush(color))
            s.addRect(x - 24, ground - 67, 48, 6, QPen(Qt.PenStyle.NoPen), QBrush(QColor("#4c252c")))
            s.addRect(x - 24, ground - 67, 48 * max(0, hp) / (100 if x == px else 45), 6,
                      QPen(Qt.PenStyle.NoPen), QBrush(QColor("#67c68a")))
        if self.attack_flash:
            s.addLine(px + 20, ground - 38, ex - 18, ground - 38, QPen(QColor("#f7d47b"), 3))
        s.addText("Héros").setPos(px - 17, ground - 91)
        s.addText("Bouftou").setPos(ex - 25, ground - 91)


class GameWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wakfu Task Bar Game — Prototype 0.1")
        self.resize(860, 480)
        self.setMinimumSize(520, 320)
        self.kamas = 0
        self.xp = 0
        self.kills = 0
        self.time_since_attack = 0
        self.respawn_delay = 0
        self.combat = CombatScene()
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(5)
        self.menu_frame = QFrame()
        self.menu_frame.setObjectName("menuFrame")
        menu_layout = QVBoxLayout(self.menu_frame)
        menu_layout.setContentsMargins(10, 8, 10, 8)
        self.menu_title = QLabel("Combat — aperçu")
        self.menu_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        menu_layout.addWidget(self.menu_title)
        self.menu_scroll = QScrollArea()
        self.menu_scroll.setWidgetResizable(True)
        self.menu_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.menu_content = QLabel()
        self.menu_content.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.menu_content.setWordWrap(True)
        self.menu_scroll.setWidget(self.menu_content)
        menu_layout.addWidget(self.menu_scroll)
        layout.addWidget(self.menu_frame)
        layout.addWidget(self.combat)
        self.nav = QTabWidget()
        self.nav.setTabPosition(QTabWidget.TabPosition.South)
        self.nav.setDocumentMode(True)
        for name in ("Combat", "Inventaire", "Aptitudes", "Sorts", "Donjons"):
            self.nav.addTab(QWidget(), name)
        self.nav.currentChanged.connect(self.refresh_menu)
        self.nav.setFixedHeight(36)
        layout.addWidget(self.nav)
        self.setStyleSheet("""
            QWidget { background: #15232e; color: #e8e4d6; font-family: Arial; }
            QFrame#menuFrame { background: #223542; border: 1px solid #47606c; border-radius: 7px; }
            QScrollArea, QScrollArea > QWidget > QWidget { background: #223542; }
            QTabBar::tab { background: #253c49; padding: 7px 10px; border: 1px solid #47606c; }
            QTabBar::tab:selected { background: #416377; }
        """)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(TICK_MS)
        self.refresh_menu()
        self.update_layout_heights()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_layout_heights()

    def update_layout_heights(self):
        available = max(180, self.centralWidget().height() - 36 - 21)
        self.menu_frame.setFixedHeight(round(available * 0.4))
        self.combat.setMinimumHeight(max(120, round(available * 0.6)))

    def refresh_menu(self, *_):
        name = self.nav.tabText(self.nav.currentIndex())
        self.menu_title.setText(name)
        contents = {
            "Combat": f"Prototype 0.1 — combat automatique en cours.\n\nVictoires : {self.kills}   |   XP : {self.xp}   |   Kamas : {self.kamas}\n\nLe héros avance vers le monstre, attaque automatiquement, puis recommence.",
            "Inventaire": "À venir : Équipement | Sac | Coffres | Fusion / Vente.\n\n14 emplacements d'équipement prévus.",
            "Aptitudes": "À venir : Intelligence et Force, points à répartir et réinitialisation.",
            "Sorts": "À venir : attaque de base, sort 1, sort 2 et priorités.",
            "Donjons": "À venir : donjons d'Astrub, progression automatique et Boss Ultimes.",
        }
        self.menu_content.setText(contents[name])

    def tick(self):
        c = self.combat
        if self.respawn_delay:
            self.respawn_delay -= 1
            if self.respawn_delay == 0:
                c.enemy_hp = 45
                c.enemy_x = 350
                c.player_x = 70
                c.player_hp = 100
            c.render_scene()
            return
        if c.attack_flash:
            c.attack_flash -= 1
        if c.enemy_flash:
            c.enemy_flash -= 1
        distance = c.enemy_x - c.player_x
        if distance > 62:
            c.player_x += min(2.5, distance - 62)
        else:
            self.time_since_attack += TICK_MS
            if self.time_since_attack >= 850:
                self.time_since_attack = 0
                c.attack_flash = 3
                c.enemy_flash = 2
                c.enemy_hp = max(0, c.enemy_hp - 9)
                if c.enemy_hp == 0:
                    self.kills += 1
                    self.xp += 10
                    self.kamas += 3
                    self.respawn_delay = 12
                    self.refresh_menu()
        c.render_scene()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Wakfu Task Bar Game")
    window = GameWindow()
    window.show()
    sys.exit(app.exec())
