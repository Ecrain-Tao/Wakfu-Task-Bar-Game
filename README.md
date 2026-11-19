# Wakfu Task Bar Game

Prototype **0.1 léger** d'un idle RPG 2D, développé en Python avec **Tkinter (bibliothèque standard)**.

## Fonctionnalités

- Fenêtre redimensionnable, menus en haut (~40 %), combat toujours visible en bas (~60 %), navigation en bas.
- Déplacement et attaque automatiques du héros contre un Bouftou de démonstration.
- Compteurs temporaires de victoires, XP et kamas (non sauvegardés).
- Onglets réservés aux systèmes futurs : inventaire, aptitudes, sorts et donjons.

Les graphismes et les valeurs sont provisoires. Aucun système complet de donjon ou d'équipement n'est encore intégré.

## Exécuter en Python

Installer Python 3.12 avec prise en charge Tkinter, puis :

```bash
python main.py
```

Aucune dépendance Python externe nécessaire.

## Télécharger une application

Le workflow GitHub Actions compile des applications **macOS Intel** (utilisables sur Apple Silicon via Rosetta 2) et **Windows** à l'aide de PyInstaller en mode `--onefile`. Dans l'onglet **Actions**, ouvrir le dernier workflow **Build desktop apps** réussi et télécharger son **Artifact**.

Le binaire macOS n'est ni signé ni notarisé. Un avertissement Gatekeeper peut apparaître.

## Fichiers

- `main.py` : point d'entrée.
- `wakfu_task_bar/app.py` : interface et boucle de combat Tkinter.
- `.github/workflows/build.yml` : builds automatiques.
