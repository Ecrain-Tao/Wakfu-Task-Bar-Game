# Mère Michou — sprites et mises à jour

## Images à ajouter

Dans le dépôt **Ecrain-Tao/Wakfu-Task-Bar-Game**, branche `main`, ajouter :

- `assets/sprites/iop_idle.png` : Iop immobile
- `assets/sprites/chacha_idle.png` : Chacha immobile

Les PNG transparents sont conseillés. Le jeu charge ces fichiers automatiquement et conserve les formes provisoires tant que les images sont absentes. Le moteur de combat reste indépendant des images. Les deux images seront incluses dans les prochaines compilations macOS et Windows.

## Donjon de test

Le seul donjon est désormais **Mère Michou**, avec des **Chachas**. Les anciens donjons ont été retirés de la sélection. Les sauvegardes conservent le niveau, l'XP, les kamas et l'équipement ; un ancien index de donjon est ramené au donjon unique.

## Mise à jour de l'application

Sur **macOS**, lorsque l'application est lancée depuis un bundle `.app` installé dans un dossier modifiable :

1. Ouvrir Réglages et sélectionner le canal expérimental si nécessaire.
2. Vérifier les mises à jour et cliquer sur **Installer la mise à jour**.
3. Confirmer le remplacement de l'application existante.
4. Le jeu télécharge l'archive, prépare un installateur externe, sauvegarde la partie, se ferme puis est remplacé et relancé.
5. Une copie de l'application précédente est conservée avec le suffixe `.previous` pour retour arrière.

L'installation est différée après fermeture pour ne pas remplacer un programme en cours d'exécution. Si l'application n'est pas lancée depuis un `.app` ou si le dossier n'est pas modifiable, l'application propose le téléchargement manuel. Sur **Windows**, l'installation reste manuelle pour le moment.

**Important :** les versions précédentes ne disposent pas de cette fonctionnalité : il faut installer une fois une version contenant ce nouveau système. L'installation automatique n'a pas encore été vérifiée sur un Mac réel ; tester avec une copie de l'application avant d'utiliser la version principale.
