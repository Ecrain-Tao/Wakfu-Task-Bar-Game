# Publication v0.3.0-alpha — canal expérimental

Cette version est une **préversion de test**, pas une version stable. Le code se trouve sur `feature/combat-iop-v1`.

## Préparation réalisée
- `VERSION = "0.3.0-alpha"`.
- Dans Réglages, choix **Versions stables** / **Versions expérimentales (alpha/beta)**.
- Les versions expérimentales sont récupérées via la liste des GitHub Releases publiques, en ignorant les brouillons ; les versions stables via `releases/latest`.
- Le workflow **Publish game update** accepte désormais `v0.3.0-alpha`, contrôle la correspondance de version, exécute les tests, compile macOS/Windows et publie avec `--prerelease`, sans remplacer la dernière version stable.
- Les mises à jour restent **téléchargées puis installées manuellement**, pour éviter toute substitution risquée du programme en cours d'exécution.

## Publication (action manuelle requise)
1. Vérifier que le workflow **Combat V1 verification** est vert sur la branche.
2. Vérifier la présence du secret GitHub Actions `PUBLIC_RELEASES_TOKEN` avec accès en écriture au dépôt `Ecrain-Tao/Wakfu-Task-Bar-Game-Releases`.
3. Dans GitHub Actions du dépôt source, ouvrir **Publish game update** → **Run workflow**.
4. Choisir la branche `feature/combat-iop-v1` et saisir exactement `v0.3.0-alpha` dans `version`.
5. Attendre la réussite des jobs macOS, Windows et publish ; vérifier dans le dépôt Releases public la préversion et ses deux archives ZIP.

**Ne pas lancer le workflow depuis main** : la version intégrée dans main n'est pas 0.3.0-alpha et le contrôle de version doit alors refuser la publication.

## Première installation et mises à jour suivantes
L'application 0.2.x ne dispose pas du sélecteur expérimental. Pour cette première alpha, télécharger l'archive depuis la Release publique et remplacer manuellement l'application **après l'avoir fermée**. Les sauvegardes sont stockées dans le dossier utilisateur et non dans l'exécutable ; en conserver une copie avant de tester.

Une fois l'alpha lancée : **Réglages → Versions expérimentales → Vérifier les mises à jour**. Les préversions suivantes pourront être téléchargées dans cet onglet.

## Limites
La publication n'est pas automatique : elle nécessite un lancement manuel du workflow et le secret GitHub. Les tests CI ne garantissent pas l'absence de bugs d'interface ou de gameplay. Ne pas fusionner la PR de développement pour publier cette alpha.

## Choisir librement le numéro de la prochaine version
Dans **Run workflow**, saisir une version inédite, par exemple `v0.3.1-alpha`, `v0.3.2-alpha.1`, `v0.3.2-beta` ou `v0.4.0`. GitHub Actions inscrit cette version dans chaque exécutable, puis vérifie les deux archives ZIP avant publication. Plus besoin de modifier `VERSION` dans le code. Le format autorisé reste `vMAJEURE.MINEURE.CORRECTIF` avec éventuellement `-alpha`, `-beta`, `-rc` et un numéro après un point.
