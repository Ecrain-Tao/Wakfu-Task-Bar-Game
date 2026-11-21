# Tester la branche Combat Iop V1

**Version expérimentale :** les règles de base sont jouables, mais la totalité du cahier des charges n'est pas encore réalisée. La branche principale et les Releases publiques restent inchangées.

## Télécharger une application de test
1. Ouvrir l'onglet **Actions** du dépôt privé.
2. Choisir **Build desktop apps**, puis le dernier run déclenché sur `feature/combat-iop-v1`.
3. Attendre la réussite des tests et de la compilation.
4. Dans **Artifacts**, télécharger `Wakfu-Task-Bar-Game-macOS-Intel` (Mac, Rosetta 2 sur Apple Silicon) ou `Wakfu-Task-Bar-Game-Windows` (Windows).
5. Décompresser l'archive et lancer l'application. Ce n'est **pas** une mise à jour publique et elle ne doit pas remplacer une installation existante.

Si aucun artifact n'est disponible, consulter les logs du workflow. Une archive n'est pas garantie tant que le run n'est pas vert.

## Test depuis les sources
Python 3.12 et `certifi` sont nécessaires :
```bash
python -m pip install certifi
python -m unittest discover -s tests -v
python main.py
```

## Scénarios de validation manuelle
- Ouvrir **Sorts**, désactiver **Colère** pour rendre **Super Iop Punch** équipable avec le budget actuel.
- Modifier la priorité d'un sort avec **Monter/Descendre** ; observer l'attaque automatique.
- Vérifier les quatre impacts colorés de **Jabs** et les animations provisoires de **Charge** et **Colère**.
- Vérifier les dégâts reçus des monstres, la transition entre salles et la conservation des PV.
- Vérifier le redémarrage salle 1 après la mort du Iop.
- Fermer et rouvrir l'application ; vérifier la conservation de l'équipement et des priorités.

## Limites connues
Les animations sont des placeholders Tkinter. Les contrôles complexes, les projectiles, les configurations multi-personnages, les règles complètes de recharge et certaines collisions avancées ne sont pas encore intégrés. Ne pas considérer cette version comme une V1 finale.

**Rapport de bug utile :** système (Mac/Windows), action effectuée, comportement observé, comportement attendu, et capture d'écran ou logs du workflow.
