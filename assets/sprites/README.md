# Sprites du donjon Mère Michou

Déposer ici deux images **PNG avec fond transparent** :

- `iop_idle.png` : Iop en position de repos.
- `chacha_idle.png` : Chacha en position de repos.

Chemins exacts : `assets/sprites/iop_idle.png` et `assets/sprites/chacha_idle.png`.

Le jeu charge ces images automatiquement au lancement. Elles sont réduites à environ 52 × 72 pixels maximum à l'écran, sans modifier les fichiers d'origine. En leur absence, les formes provisoires restent visibles. Une nouvelle compilation est nécessaire après leur ajout pour les inclure dans l'application distribuée.

## Fond de la carte

Ajouter `AP_mere_michou.png` dans ce même dossier : `assets/sprites/AP_mere_michou.png`.

Le jeu adapte le fond à la taille du canvas de combat. Un PNG ou JPG peut être décodé par Pillow, mais conserver l'extension `.png` pour correspondre au nom attendu. Si le fichier est absent, le fond actuel reste affiché.

## Animations idle

Les fichiers `iop_idle.png` et `chacha_idle.png` sont des images **statiques**. Pour un véritable idle animé, fournir une planche de sprites (spritesheet) avec des images cohérentes ou une séquence de PNG transparents ; l'animation pourra ensuite être jouée image par image.
