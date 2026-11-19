# Wakfu Task Bar Game

Prototype **0.2.0** en Python / Tkinter. Code privé, distributions prévues sur le dépôt public [Wakfu-Task-Bar-Game-Releases](https://github.com/Ecrain-Tao/Wakfu-Task-Bar-Game-Releases).

## Déjà implémenté

- Fenêtre redimensionnable ; menus en haut, combat toujours visible en bas.
- Combat automatique avec plusieurs monstres simultanés, poursuite, dégâts et barres de PV.
- Trois donjons de démonstration avec salles fixes, boss, validation et déverrouillage séquentiel.
- Progression automatique activable, sélection manuelle des donjons accessibles.
- Défaite : redémarrage du donjon, restauration des PV.
- XP, niveaux (jusqu'au niveau 35), kamas et compteur de coffres.
- Sauvegarde locale dans `~/.wakfu-task-bar-game/save.json` toutes les 10 secondes et à la fermeture.
- Onglet Réglages : vérifier les GitHub Releases publiques et télécharger la nouvelle archive.

**Encore à développer :** classes, équipements, inventaire fonctionnel, aptitudes, sorts, fusions, vente, Boss Ultimes, animations/graphismes définitifs et installation automatique des mises à jour. Les mécaniques actuelles sont une démonstration et ne reflètent pas encore tout le cahier des charges.

## Lancement local

Python 3.12 avec Tkinter :

```bash
python main.py
python -m unittest discover -s tests
```

## Compilation

GitHub Actions > **Build desktop apps** produit les exécutables macOS Intel (Rosetta 2 sur Apple Silicon) et Windows, ainsi que les ZIP de mise à jour.

## Publication publique des mises à jour

Le workflow **Publish game update** compile et publie uniquement les ZIP vers le dépôt public. Pour l'autoriser :

1. Créer un **fine-grained personal access token** GitHub limité au dépôt `Wakfu-Task-Bar-Game-Releases`, avec permission **Contents: Read and write**.
2. Dans le dépôt **privé**, ouvrir **Settings → Secrets and variables → Actions → New repository secret**.
3. Nommer le secret `PUBLIC_RELEASES_TOKEN` et coller la valeur du jeton. **Ne jamais le mettre dans un fichier ou un message.**
4. Lancer le workflow **Publish game update** manuellement avec `v0.2.0`, ou pousser un tag `v0.2.0`. Vérifier que la version correspond à `VERSION` dans `wakfu_task_bar/updater.py`.
5. Vérifier la Release publique contenant `Wakfu-Task-Bar-Game-Windows.zip` et `Wakfu-Task-Bar-Game-macOS-Intel.zip`.

Le bouton de téléchargement de l'application fonctionnera après publication d'une version **plus récente** que celle installée. L'installation demeure manuelle dans cette version ; ne pas écraser l'application pendant qu'elle tourne. Le binaire macOS n'est pas signé/notarisé.

**Sécurité :** aucune clé privée ni jeton n'est intégré dans l'application. Les téléchargements proviennent exclusivement du dépôt public prévu. La vérification cryptographique des archives et le remplacement automatique restent à implémenter avant une distribution grand public.
