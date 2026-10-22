# Enclos — Backend

API d'Enclos construite avec Django et Django REST Framework. Elle gère les comptes, les fermes, les données du cheptel, les abonnements, les alertes et les fonctionnalités d'intelligence artificielle.

## Technologies

- Python 3.12 dans l'image Docker
- Django 6.1 et Django REST Framework
- PostgreSQL 16
- JWT avec SimpleJWT
- Django Channels et Daphne pour les connexions WebSocket
- scikit-learn, pandas, NumPy, SHAP et joblib pour le modèle prédictif
- PayDunya pour le traitement des paiements

## Fonctionnalités de la V2

- Authentification et gestion des comptes.
- Gestion des fermes et séparation des données par ferme active.
- Gestion des animaux, des races et génération des QR codes de fiche.
- Suivi de l'alimentation, avec types d'aliments et fréquences.
- Suivi de santé et mesures, ordonnances, rappels et extraction d'informations d'ordonnance.
- Suivi des gestations et des événements associés.
- Historique des événements du cheptel.
- Alertes et notifications en temps réel via WebSocket.
- Rappels d'ordonnance vérifiés périodiquement par la commande Django `rappels_ordonnances`.
- Prédiction de risque à partir des données de l'animal et pré-diagnostic assisté à partir d'une image et d'observations.
- Plans, abonnements et intégration PayDunya.

Les réponses générées par l'IA sont des pistes d'aide à l'analyse et ne constituent pas un diagnostic vétérinaire.

## Structure

```text
backend/
├── accounts/       # Comptes et authentification
├── alertes/        # Alertes, rappels et WebSocket
├── alimentation/   # Rations, types d'aliments et fréquences
├── enclos/         # Paramètres, routes et configuration ASGI
├── fermes/         # Fermes
├── gestation/      # Gestations
├── historique/     # Historique des événements
├── ia_prediction/  # Prédictions et pré-diagnostic IA
├── moncheptel/     # Animaux et races
├── plans/          # Plans d'abonnement
├── sante/          # Suivi santé, ordonnances et rappels
├── subscriptions/  # Abonnements et paiements PayDunya
├── manage.py
├── requirements.txt
└── Dockerfile
```

Chaque application Django regroupe ses modèles, vues, sérialiseurs, routes, migrations et tests lorsque cela s'applique.

## Prérequis et configuration

- Python 3.12 recommandé pour reproduire l'environnement Docker.
- PostgreSQL accessible.
- Un fichier `backend/.env` avec la configuration propre à l'environnement.

Les principales variables attendues sont :

```env
SECRET_KEY=
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=5432
CORS_ALLOWED_ORIGINS=http://localhost:5173
PAYDUNYA_MASTER_KEY=
PAYDUNYA_PRIVATE_KEY=
PAYDUNYA_TOKEN=
PAYDUNYA_MODE=test
N8N_WEBHOOK_URL=
OPENROUTER_API_KEY=
OPENROUTER_VISION_MODEL=
GEMINI_API_KEY=
GEMINI_VISION_MODEL=
```

Ajoutez dans cet environnement les paramètres PayDunya et IA nécessaires à vos intégrations. Les clés, jetons et mots de passe sont des secrets : utilisez vos propres valeurs, ne les partagez pas et ne les ajoutez pas au dépôt. `DEBUG=True` et le mode de paiement `test` sont destinés au développement, pas à la production.

## Lancement local

Depuis `backend/`, créer et activer un environnement virtuel, puis installer les dépendances :

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Configurer le fichier `.env` de `backend/` et démarrer PostgreSQL, puis exécuter :

```bash
python manage.py migrate
python manage.py runserver
```

L'API est alors disponible par défaut sur `http://127.0.0.1:8000`. La documentation interactive OpenAPI est disponible à `http://127.0.0.1:8000/api/docs/` et l'administration Django à `http://127.0.0.1:8000/admin/`.

Commandes de développement :

```bash
python manage.py check
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py test
```

## Routes principales de l'API

Les routes des ressources sont regroupées sous `/api/` :

| Domaine | Préfixe |
| --- | --- |
| Authentification | `/api/auth/` |
| Plans et abonnements | `/api/plans/`, `/api/subscriptions/` |
| Fermes | `/api/fermes/` |
| Animaux et races | `/api/animaux/`, `/api/races/` |
| Alimentation | `/api/alimentations/`, `/api/type-aliments/`, `/api/frequences/` |
| Santé et ordonnances | `/api/sante/`, `/api/ordonnances/` |
| Gestations | `/api/gestations/` |
| Historique | `/api/historiques/` |
| Alertes | `/api/alertes/` |
| IA | `/api/ia/predire/`, `/api/ia/pre-diagnostic/` |
| Schéma et documentation | `/api/schema/`, `/api/docs/` |

La plupart des routes sont protégées par JWT. Les requêtes associées à une ferme transmettent également l'identifiant de la ferme active via l'en-tête `X-Ferme-Id`. Consultez la documentation Swagger pour les méthodes et paramètres de chaque endpoint.

## IA et alertes

Le backend comprend un modèle prédictif chargé par le module `ia_prediction` et des endpoints dédiés à la prédiction et au pré-diagnostic. Les analyses peuvent s'appuyer sur les données de santé, d'alimentation et de suivi de l'animal. Les alertes produites sont conservées et peuvent être envoyées au frontend en temps réel par WebSocket.

Le pré-diagnostic par image et les justifications LLM dépendent des fournisseurs et variables externes configurés dans `backend/.env`. L'image Docker du backend télécharge également le modèle prédictif pendant le build ; l'accès Internet est donc requis à cette étape. En Compose, le dossier racine `models/` est monté dans le conteneur sous `/models`.

## Docker et Docker Compose

Le fichier `docker-compose.yml` à la racine du dépôt démarre quatre services :

- `db` : PostgreSQL 16 avec le volume persistant `enclos_pgdata`.
- `backend` : API Django sur le port hôte `8000`. Le conteneur lit `backend/.env`, monte le code source et applique les migrations avant de démarrer le serveur.
- `reminders` : worker Django qui attend que l'API soit prête, puis vérifie les prises échues toutes les 30 secondes et crée les alertes correspondantes.
- `frontend` : bundle React servi par Nginx sur le port hôte `5173`.

Depuis la racine du dépôt, vérifiez d'abord que `backend/.env` est configuré et que ses paramètres `DB_*` correspondent à ceux du service PostgreSQL. Puis lancez :

```bash
docker compose up --build
```

Accès locaux :

- Interface : `http://localhost:5173`
- API : `http://localhost:8000`
- Swagger : `http://localhost:8000/api/docs/`
- Administration Django : `http://localhost:8000/admin/`

Commandes utiles :

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f reminders
docker compose logs -f db
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py test
docker compose down
```

`docker compose down` arrête et supprime les conteneurs sans supprimer les données PostgreSQL. `docker compose down -v` supprime aussi le volume de la base et ses données : ne l'utilisez que si leur effacement est voulu.

Le conteneur PostgreSQL écoute sur le port `5432` du réseau Docker. Pour les connexions depuis la machine hôte, Compose publie le port `5433` par défaut afin de ne pas entrer en conflit avec un PostgreSQL local. Ce port peut être remplacé avec la variable `DB_FORWARD_PORT` ; le backend continue, dans tous les cas, à se connecter à `db:5432`.

Le frontend du Compose utilise par défaut une URL API locale adaptée à un navigateur sur la même machine. Pour un déploiement distant, il faut transmettre au build Vite une valeur `VITE_API_BASE_URL` correspondant à l'adresse accessible depuis le navigateur, puis reconstruire le bundle. Le Dockerfile et la configuration Compose actuels ne transmettent pas automatiquement cette variable au build.

Le worker crée des alertes dans l'application ; il ne déclenche pas de notification native du navigateur ou du téléphone. En dehors de Docker Compose, lancez-le dans un processus séparé depuis `backend/` :

```bash
python manage.py rappels_ordonnances --interval 30
```

Pour un test ponctuel :

```bash
python manage.py rappels_ordonnances --once
```

## Sécurité et déploiement

- Le fichier `backend/.env` contient des secrets d'environnement ; ne le versionnez pas et n'en copiez pas le contenu dans la documentation.
- Les paramètres de base de données de Compose sont configurés dans le fichier racine `docker-compose.yml` et doivent correspondre à `DB_*` dans `backend/.env`. Remplacez les identifiants de développement avant tout déploiement.
- Configurez `DEBUG=False`, une `SECRET_KEY` forte, les hôtes autorisés, CORS et les URL de retour PayDunya pour l'environnement de déploiement.
- Pour la production, utilisez un serveur ASGI approprié, HTTPS, des sauvegardes PostgreSQL et une couche Channels adaptée à plusieurs processus si nécessaire. Le `runserver` de Compose est prévu pour le développement.
