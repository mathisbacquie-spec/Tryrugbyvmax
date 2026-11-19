# RUGBY AUCTION ONLINE — 2 joueurs

Jeu accessible dans un navigateur sur deux téléphones, sans installation. Contient une base de 500 joueurs, 12 tirages (6 avants, 6 trois-quarts), 20 € par participant, maximum 6 joueurs par équipe, enchères de 1 € et chrono serveur de 15 secondes.

## Publier gratuitement avec Render

1. Crée un dépôt GitHub et place les **5 fichiers** de ce dossier à sa racine (`index.html`, `server.py`, `players.json`, `requirements.txt`, `render.yaml`). Ne téléverse pas le ZIP tel quel.
2. Connecte-toi sur https://dashboard.render.com/ et choisis **New > Blueprint**.
3. Connecte ton dépôt GitHub et valide la création du service décrit par `render.yaml` (vérifie que le plan affiché est bien **Free** avant validation).
4. Attends le déploiement. Render fournit une adresse HTTPS du type `https://rugby-auction-online-xxxx.onrender.com`.
5. Ouvre cette adresse sur deux téléphones : **Créer un salon** sur le premier, puis **Rejoindre** avec le code sur le second. Le joueur 1 lance la partie.

Les offres gratuites et leurs quotas peuvent changer ; vérifie les conditions Render au moment de la publication. Le service gratuit peut se mettre en veille après une période d'inactivité : le premier chargement peut prendre du temps.

## Rejouer une partie

À la fin des 12 enchères, le **joueur 1** peut cliquer sur **🔄 Rejouer une partie**. Une nouvelle sélection aléatoire de 6 avants et 6 trois-quarts est créée, les deux budgets reviennent à 20 €, les équipes sont vidées et le chrono reprend. Les deux joueurs restent dans le **même salon** et n’ont pas besoin de ressaisir le code. Les deux joueurs doivent être connectés pour relancer.

## Limites à connaître

- C'est une première version jouable, **pas encore hébergée** : le déploiement sur ton compte Render reste à faire.
- Salons en mémoire : perdus lors d'un redémarrage ou d'une mise en veille ; si le joueur 1 se déconnecte, le salon ferme.
- Deux joueurs maximum par salon, pas de reconnexion en cours de partie ni de comptes.
- Un seul processus serveur doit être utilisé (ce que prévoit la configuration fournie).
- Les fiches joueurs sont une base de jeu et certains clubs / nationalités peuvent nécessiter des corrections.

## Test en local

```bash
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8000
```

Ouvre http://localhost:8000 sur l'ordinateur.

## Pseudos des joueurs
Chaque joueur choisit un pseudo (20 caractères maximum) avant de créer ou rejoindre un salon. Les pseudos sont synchronisés sur les deux appareils et restent affichés lors des parties rejouées. Ils ne sont pas enregistrés dans une base de données.
