# Wakfu Task Bar Game

Prototype **0.1** d'un idle RPG 2D à fenêtre redimensionnable, en Python et PySide6.

## Fonctionnalités de la version 0.1

- Combat automatique de démonstration : déplacement vers un Bouftou, attaques et réapparition.
- Compteurs de victoires, XP et kamas (valeurs provisoires, **non sauvegardées**).
- Menus en haut (40 %) et combat visible en bas (60 %), onglets toujours en bas.
- Onglets de navigation préparés pour les prochaines versions.
- Interface adaptée aux fenêtres redimensionnées.

Les graphismes sont **provisoires** et les mécaniques d'inventaire, de donjon, de fusion et de sorts ne sont pas encore implémentées.

## Lancer depuis les sources

Installer Python 3.12, puis :

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell : .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
python main.py
```

## Builds GitHub Actions

Le workflow `build.yml` crée des archives pour macOS (Apple Silicon) et Windows. Aller dans **Actions → Build desktop apps → Run workflow** ou pousser un commit sur `main`. Télécharger ensuite les **Artifacts** du run.

Les exécutables macOS ne sont pas signés/notarisés : Gatekeeper peut demander une autorisation lors du premier lancement.

## Structure

- `main.py` : point d'entrée
- `wakfu_task_bar/app.py` : interface et boucle de combat
- `.github/workflows/build.yml` : compilation automatisée
