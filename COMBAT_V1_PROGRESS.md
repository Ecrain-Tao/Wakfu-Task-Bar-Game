# Combat Iop V1 — état d'intégration

Branche de travail : `feature/combat-iop-v1`. Ne pas fusionner avant vérification.

## Intégré dans cette branche
- Module autonome `combat_v1.py` avec acteurs, actions horodatées, impacts élémentaires, dégâts, soins, critiques, parade, barrière et résistances.
- Jabs : quatre impacts Feu/Eau/Terre/Air ; Uppercut : Lumière ; Charge : Terre ; Super Iop Punch : Feu ; Colère : zone Feu et impact bonus conditionnel.
- Budget PA/PW d'équipement et priorités de sorts ; commandes dans l'onglet Sorts.
- Monstres : poursuite, attaque de base animée, cible verrouillée pendant l'attaque ; dégâts déjà subis conservés.
- Raccordement au moteur de donjons et à la sauvegarde ; transition visuelle sommaire ; poses procédurales provisoires.
- Premiers tests unitaires.

## À finaliser avant essais utilisateur
- Contrôles de mouvement et d'actions avec durée, récupération d'interruption spécifique à chaque sort.
- Rechargement d'Uppercut après *quatre attaques lancées* et conditions alternatives générales (coups, dégâts reçus/infligés, morts).
- Simulation des projectiles pour les attaques à distance.
- Gestion rigoureuse des actions simultanées, priorité au joueur et accélération ×3 de la dernière animation.
- Géométrie des hitboxes et collisions robustes, notamment plusieurs combattants simultanés.
- Gestion complète de plusieurs héros, morts persistantes, écran de sortie et réapparition.
- Effets visuels définitifs, feedback des dégâts colorés et animations d'impact.
- Vérification de la compatibilité des anciennes sauvegardes et des tests sur macOS/Windows.

## Exécution locale
```bash
python -m unittest discover -s tests
python main.py
```

**Important :** cette branche reste un prototype de développement. Les tests n'ont pas encore été exécutés dans un environnement Python avec les fichiers complets du dépôt.
