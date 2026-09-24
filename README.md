# Enclos Backend - Documentation Complète

## Vue d'ensemble du projet

**Enclos Backend** est une API REST construite avec Django et Django REST Framework qui sert de backend à l'application de gestion d'élevage. Il gère l'authentification, les données du cheptel, l'intelligence artificielle pour la prédiction de maladies, et les communications en temps réel via WebSockets.

### Stack Technique

- **Django 6.1.1** : Framework web Python
- **Django REST Framework 3.18.1** : Toolkit pour construire des APIs REST
- **PostgreSQL** : Base de données relationnelle
- **Channels 4.3.1** : Support WebSockets pour communications en temps réel
- **Daphne 4.2.1** : Serveur ASGI pour WebSockets
- **scikit-learn 1.6.1** : Machine Learning pour les prédictions
- **SHAP 0.52.0** : Explicabilité des modèles IA
- **SimpleJWT 5.5.1** : Authentification JWT
- **PayDunya** : Intégration paiement mobile africain

### Architecture

L'application suit une architecture **API REST** avec :
- **Authentication JWT** : Tokens pour sécuriser les endpoints
- **Multi-tenancy** : Chaque utilisateur peut avoir plusieurs fermes
- **Real-time** : WebSockets pour les alertes en temps réel
- **ML Integration** : Prédictions IA avec Random Forest + SHAP
- **Event-driven** : Signals Django pour automatiser les traitements

---

## Arborescence du projet

```
backend/
├── accounts/              # Gestion des comptes utilisateurs
│   ├── admin.py          # Interface admin Django
│   ├── apps.py           # Configuration de l'application
│   ├── __init__.py       # Marqueur package Python
│   ├── migrations/       # Migrations de base de données
│   ├── models.py         # Modèles de données utilisateurs
│   ├── serializers.py    # Sérialiseurs API (JSON)
│   ├── tests.py          # Tests unitaires
│   ├── urls.py           # Routes URL de l'application
│   └── views.py          # Vues API (logique métier)
├── alertes/              # Système d'alertes en temps réel
│   ├── admin.py
│   ├── apps.py
│   ├── consumers.py      # Consumers WebSocket (réception messages)
│   ├── middleware.py     # Middleware d'auth WebSocket
│   ├── migrations/
│   ├── models.py         # Modèle Alerte
│   ├── routing.py        # Routing WebSocket
│   ├── serializers.py
│   ├── signals.py        # Signals pour broadcast alertes
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── alimentation/         # Gestion de l'alimentation
│   ├── admin.py
│   ├── apps.py
│   ├── __init__.py
│   ├── migrations/
│   ├── models.py         # Modèles Alimentation, TypeAliment, Frequence
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── common_validation.py  # Validation commune des formulaires
├── Dockerfile            # Configuration Docker
├── enclos/               # Configuration du projet Django
│   ├── asgi.py          # Configuration ASGI (WebSockets)
│   ├── __init__.py
│   ├── settings.py      # Configuration globale Django
│   ├── urls.py          # Routes URL principales
│   └── wsgi.py          # Configuration WSGI (HTTP classique)
├── fermes/               # Gestion des fermes
│   ├── admin.py
│   ├── apps.py
│   ├── __init__.py
│   ├── migrations/
│   ├── models.py         # Modèle Ferme
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── gestation/            # Gestion des gestations
│   ├── admin.py
│   ├── apps.py
│   ├── __init__.py
│   ├── migrations/
│   ├── models.py         # Modèle Gestation
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── historique/           # Historique des événements
│   ├── admin.py
│   ├── apps.py
│   ├── __init__.py
│   ├── migrations/
│   ├── models.py         # Modèle HistoriqueEvenement
│   ├── serializers.py
│   ├── signals.py       # Signals pour historisation automatique
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── ia_prediction/        # Module Intelligence Artificielle
│   ├── admin.py
│   ├── apps.py
│   ├── __init__.py
│   ├── migrations/
│   ├── models.py         # Modèle PredictionResultat
│   ├── predictor.py      # Moteur de prédiction IA 
│   ├── serializers.py
│   ├── signals.py        # Signals pour déclenchement auto IA
│   ├── tests.py
│   ├── urls.py
│   └── views.py          # API de prédiction
├── manage.py             # Script gestion Django
├── moncheptel/           # Gestion du cheptel (animaux)
│   ├── admin.py
│   ├── apps.py
│   ├── __init__.py
│   ├── migrations/
│   ├── models.py         # Modèles Animal, Race
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── plans/                # Plans d'abonnement
│   ├── admin.py
│   ├── apps.py
│   ├── __init__.py
│   ├── migrations/
│   ├── models.py         # Modèle Plan
│   ├── serializers.py
│   ├── urls.py
│   └── views.py
├── README.md             # Ce fichier
├── requirements.txt      # Dépendances Python
├── sante/                # Suivi de santé
│   ├── admin.py
│   ├── apps.py
│   ├── __init__.py
│   ├── migrations/
│   ├── models.py         # Modèle SuiviSante
│   ├── serializers.py
│   ├── signals.py       # Signals pour synchronisation état santé
│   ├── sync.py          # Script de synchronisation
│   ├── tests.py
│   ├── urls.py
│   └── views.py
└── subscriptions/        # Gestion des abonnements
    ├── admin.py
    ├── apps.py
    ├── __init__.py
    ├── migrations/
    ├── models.py         # Modèle Subscription
    ├── serializers.py
    ├── tests.py
    ├── urls.py
    └── views.py
```

---

## Rôle détaillé de chaque fichier

### Fichiers de configuration du projet

#### `manage.py`
**Script de gestion Django** - Point d'entrée pour toutes les commandes Django :
```bash
python manage.py runserver          # Lance le serveur de développement
python manage.py migrate            # Applique les migrations de base de données
python manage.py createsuperuser   # Crée un utilisateur admin
python manage.py collectstatic      # Collecte les fichiers statiques
python manage.py shell              # Lance un shell Python interactif
```

#### `requirements.txt`
**Dépendances Python** - Liste toutes les bibliothèques nécessaires :
- **Django & DRF** : Framework web et API REST
- **PostgreSQL driver** : `psycopg2-binary` pour la base de données
- **JWT Auth** : `djangorestframework_simplejwt` pour l'authentification
- **Channels** : `channels`, `daphne` pour les WebSockets
- **ML** : `scikit-learn`, `shap`, `joblib`, `numpy`, `pandas` pour l'IA
- **Validation** : `drf-spectacular` pour la documentation API (Swagger)
- **Serving** : `gunicorn`, `whitenoise` pour la production

#### `enclos/settings.py`
**Configuration globale Django** - Définit tous les paramètres de l'application :

**Sections principales :**
- **SECRET_KEY** : Clé de chiffrement pour les sessions (à garder secrète en production)
- **DEBUG** : Mode développement (True) ou production (False)
- **ALLOWED_HOSTS** : Domaines autorisés à servir l'application
- **INSTALLED_APPS** : Liste des applications Django installées
- **MIDDLEWARE** : Pipeline de traitement des requêtes HTTP
- **DATABASES** : Configuration de la connexion PostgreSQL
- **AUTH_USER_MODEL** : Modèle utilisateur personnalisé
- **REST_FRAMEWORK** : Configuration de DRF (authentification, permissions)
- **SIMPLE_JWT** : Configuration des tokens JWT (durée, rotation)
- **CORS** : Configuration pour autoriser les requêtes cross-origin
- **CHANNEL_LAYERS** : Configuration du backend pour WebSockets (InMemoryChannelLayer)
- **N8N_WEBHOOK_URL** : URL du webhook n8n pour l'explication LLM

#### `enclos/urls.py`
**Routing principal** - Définit les routes URL de niveau supérieur :
```python
urlpatterns = [
    path('admin/', admin.site.urls),              # Interface admin Django
    path('api/auth/', include('accounts.urls')),  # Authentification
    path('api/', include('moncheptel.urls')),     # Gestion animaux
    path('api/', include('alimentation.urls')),   # Alimentation
    path('api/', include('sante.urls')),         # Suivi santé
    path('api/', include('gestation.urls')),      # Gestation
    path('api/', include('alertes.urls')),       # Alertes
    path('api/ia/', include('ia_prediction.urls')), # IA
    path('api/schema/', SpectacularAPIView.as_view()), # Schéma OpenAPI
    path('api/docs/', SpectacularSwaggerView.as_view()), # Documentation Swagger
]
```

#### `enclos/asgi.py`
**Configuration ASGI** - Interface ASGI pour supporter HTTP et WebSockets :
```python
application = ProtocolTypeRouter({
    'http': django_application,        # Requêtes HTTP classiques
    'websocket': JWTAuthMiddleware(URLRouter(websocket_urlpatterns)),  # WebSockets
})
```
- **ASGI** : Asynchronous Server Gateway Interface - Standard pour les applications async
- **ProtocolTypeRouter** : Route les requêtes selon le protocole (http/websocket)
- **JWTAuthMiddleware** : Authentifie les connexions WebSocket via JWT

#### `enclos/wsgi.py`
**Configuration WSGI** - Interface WSGI pour les serveurs HTTP synchrones (Gunicorn) :
- Utilisé uniquement pour le déploiement production avec serveurs synchrones
- Remplacé par ASGI (Daphne) pour le support WebSockets

#### `Dockerfile`
**Configuration Docker** - Instructions pour construire l'image Docker du backend :
- Base image Python
- Installation des dépendances
- Copie du code
- Exposition du port 8000
- Commande de démarrage (Daphne pour ASGI)

---

## Applications Django détaillées

### 1. `accounts/` - Gestion des comptes utilisateurs

**Rôle** : Gère l'authentification et les utilisateurs

#### `models.py`
Contient les modèles liés aux utilisateurs :
- Extension du modèle User Django standard
- Profils utilisateurs avec informations supplémentaires

#### `views.py`
Endpoints d'authentification :
- **POST /api/auth/token/** : Login - Génère les tokens JWT
- **POST /api/auth/token/refresh/** : Rafraîchissement du token
- **POST /api/auth/users/register/** : Inscription d'un nouvel utilisateur
- **GET /api/auth/users/me/** : Profil de l'utilisateur connecté

#### `serializers.py`
Sérialiseurs pour convertir les modèles Django en JSON :
- `UserSerializer` : Conversion User ↔ JSON
- `RegisterSerializer` : Validation des données d'inscription

---

### 2. `fermes/` - Gestion des fermes

**Rôle** : Gère les fermes des éleveurs (multi-tenancy)

#### `models.py`
```python
class Ferme(models.Model):
    proprietaire = models.ForeignKey(User, on_delete=models.CASCADE)
    nom = models.CharField(max_length=120)
    localisation = models.CharField(max_length=150)
    superficie = models.DecimalField(...)
    coordonneesGPS = models.CharField(...)
    description = models.TextField()
```

#### `views.py`
Endpoints :
- **GET /api/fermes/** : Liste des fermes de l'utilisateur
- **POST /api/fermes/** : Création d'une nouvelle ferme
- **GET /api/fermes/{id}/** : Détails d'une ferme
- **PUT /api/fermes/{id}/** : Modification d'une ferme

---

### 3. `moncheptel/` - Gestion du cheptel (animaux)

**Rôle** : Gère les animaux de chaque ferme

#### `models.py`

**Modèle Race** :
```python
class Race(models.Model):
    espece = models.CharField(choices=[('bovin', 'Bovin'), ('ovin', 'Ovin'), ...])
    nom = models.CharField(max_length=120)
    description = models.TextField()
```

**Modèle Animal** :
```python
class Animal(models.Model):
    ferme = models.ForeignKey(Ferme, on_delete=models.CASCADE)
    nom = models.CharField(max_length=120, blank=True)
    numero_identification = models.CharField(max_length=20, unique=True)  # Auto-généré
    espece = models.CharField(choices=ESPECE_CHOICES)
    race = models.ForeignKey(Race, on_delete=models.SET_NULL, null=True)
    sexe = models.CharField(choices=[('male', 'Mâle'), ('femelle', 'Femelle')])
    date_naissance = models.DateField()
    poids_naissance = models.DecimalField(...)
    couleur = models.CharField(...)
    etat_sante = models.CharField(choices=[('sain', 'Sain'), ('malade', 'Malade'), ...])
    presence = models.CharField(choices=[('present', 'Présent'), ('vendu', 'Vendu'), ...])
    observations = models.TextField()
```

**Génération automatique du numéro d'identification** :
- Préfixe selon l'espèce (B pour Bovin, O pour Ovin, C pour Caprin, P pour Porcin)
- Numéro séquentiel unique par ferme
- Exemple : `B-001`, `O-042`, `C-015`

#### `views.py`
Endpoints :
- **GET /api/animaux/** : Liste des animaux de la ferme active
- **POST /api/animaux/** : Création d'un animal
- **GET /api/animaux/{id}/** : Détails d'un animal
- **PUT /api/animaux/{id}/** : Modification d'un animal
- **DELETE /api/animaux/{id}/** : Suppression d'un animal

#### `serializers.py`
- `AnimalSerializer` : Conversion Animal ↔ JSON avec relations
- `RaceSerializer` : Conversion Race ↔ JSON

---

### 4. `alimentation/` - Gestion de l'alimentation

**Rôle** : Enregistre les alimentations des animaux

#### `models.py`

**TypeAliment** : Types d'aliments créés par l'utilisateur (Foin, Granulés, Ensilage...)
**FrequenceAlimentation** : Fréquences (Quotidienne, Biquotidienne, Hebdomadaire...)
**Alimentation** :
```python
class Alimentation(models.Model):
    ferme = models.ForeignKey(Ferme, on_delete=models.CASCADE)
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    type_aliment = models.ForeignKey(TypeAliment, on_delete=models.SET_NULL)
    frequence = models.ForeignKey(FrequenceAlimentation, on_delete=models.SET_NULL)
    quantite_kg = models.DecimalField(...)
    date_alimentation = models.DateField()
    note = models.TextField()
```

#### `views.py`
Endpoints :
- **GET /api/alimentations/** : Liste des alimentations
- **POST /api/alimentations/** : Création d'une alimentation
- **GET /api/alimentations/{id}/** : Détails
- **PUT /api/alimentations/{id}/** : Modification
- **DELETE /api/alimentations/{id}/** : Suppression

---

### 5. `sante/` - Suivi de santé

**Rôle** : Enregistre les suivis de santé des animaux

#### `models.py`
```python
class SuiviSante(models.Model):
    ferme = models.ForeignKey(Ferme, on_delete=models.CASCADE)
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    date_debut = models.DateField()
    date_prochaine_consultation = models.DateField()
    date_fin = models.DateField()  # Date de guérison
    statut = models.CharField()  # 'Malade', 'En traitement', 'Guéri', 'Sous surveillance'
    poids_kg = models.DecimalField(...)  # Poids actuel mesuré
    temperature_celsius = models.DecimalField(...)  # Température
    frequence_cardiaque = models.PositiveIntegerField()  # BPM
    note = models.TextField()
```

#### `signals.py`
Synchronise automatiquement l'état de santé de l'animal avec les suivis :
- Quand un suivi "Malade" est créé → `animal.etat_sante = 'malade'`
- Quand un suivi se termine → `animal.etat_sante = 'sain'`

#### `sync.py`
Script de synchronisation manuelle pour corriger les états de santé

---

### 6. `gestation/` - Gestion des gestations

**Rôle** : Suit les gestations des femelles

#### `models.py`
```python
class Gestation(models.Model):
    ferme = models.ForeignKey(Ferme, on_delete=models.CASCADE)
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    statut = models.CharField(choices=[('En cours', 'En cours'), ('Imminente', 'Imminente'), ('Terminée', 'Terminée')])
    date_debut = models.DateField()  # Date de saillie
    date_prevue = models.DateField()  # Date prévue de mise bas
    date_mise_bas_reelle = models.DateField()
    nombre_naissances = models.PositiveIntegerField()
    pere = models.ForeignKey(Animal, on_delete=models.SET_NULL, related_name='peres')
    note = models.TextField()
```

---

### 7. `historique/` - Historique des événements

**Rôle** : Enregistre tous les événements du cheptel

#### `models.py`
```python
class HistoriqueEvenement(models.Model):
    ferme = models.ForeignKey(Ferme, on_delete=models.CASCADE)
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, null=True)
    type_evenement = models.CharField()  # 'alimentation', 'sante', 'gestation', 'IA', etc.
    titre = models.CharField()
    description = models.TextField()
    date_evenement = models.DateTimeField()
    source_ia = models.BooleanField()  # True si généré par l'IA
```

#### `signals.py`
Historise automatiquement les événements :
- Création alimentation → Entrée historique
- Création suivi santé → Entrée historique
- Prédiction IA → Entrée historique

---

### 8. `alertes/` - Système d'alertes en temps réel 

**Rôle** : Gère les alertes et les notifie en temps réel via WebSockets

#### `models.py`
```python
class Alerte(models.Model):
    ferme = models.ForeignKey(Ferme, on_delete=models.CASCADE)
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, null=True)
    type_alerte = models.CharField()  # 'Info', 'Avertissement', 'Critique'
    message = models.TextField()
    statut = models.CharField()  # 'lue', 'non_lue'
    date_creation = models.DateTimeField(auto_now_add=True)
```

#### `consumers.py` - Consumer WebSocket
**Rôle** : Gère les connexions WebSocket pour les alertes en temps réel

```python
class AlerteConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Vérifie l'authentification JWT
        user = self.scope.get('user')
        ferme_id = self.scope['url_route']['kwargs']['ferme_id']
        
        # Vérifie que l'utilisateur possède la ferme
        if not await self.owns_ferme(ferme_id, user.id):
            await self.close(code=4003)  # Refusé
            return
        
        # Ajoute le client au groupe de la ferme
        self.group_name = f'alertes_ferme_{ferme_id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
    
    async def disconnect(self, close_code):
        # Retire le client du groupe
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
    
    async def alerte_created(self, event):
        # Envoie l'alerte au client WebSocket
        await self.send(text_data=json.dumps(event['alerte']))
```

**Fonctionnement :**
1. Le frontend se connecte à `ws://backend/ws/alertes/{ferme_id}/`
2. Le middleware JWT authentifie la connexion via le token
3. Le consumer vérifie que l'utilisateur possède la ferme
4. Le client est ajouté au groupe `alertes_ferme_{ferme_id}`
5. Quand une alerte est créée, elle est broadcastée à tous les clients du groupe

#### `routing.py` - Routing WebSocket
```python
websocket_urlpatterns = [
    re_path(r'^ws/alertes/(?P<ferme_id>\d+)/$', AlerteConsumer.as_asgi()),
]
```
Définit les URL WebSocket : `/ws/alertes/{ferme_id}/`

#### `middleware.py` - Middleware d'authentification WebSocket
**Rôle** : Authentifie les connexions WebSocket via JWT
- Extrait le token depuis les paramètres URL ou les headers
- Valide le token et injecte l'utilisateur dans le scope
- Similaire au middleware HTTP mais adapté pour WebSockets

#### `signals.py` - Broadcast automatique des alertes
```python
@receiver(post_save, sender=Alerte)
def broadcast_new_alerte(sender, instance, created, **kwargs):
    if not created:
        return
    
    # Envoie l'alerte à tous les clients connectés de la ferme
    async_to_sync(get_channel_layer().group_send)(
        f'alertes_ferme_{instance.ferme_id}',
        {'type': 'alerte.created', 'alerte': AlerteSerializer(instance).data},
    )
```

**Fonctionnement :**
1. Quand une alerte est créée en base de données
2. Le signal `post_save` est déclenché
3. L'alerte est sérialisée en JSON
4. Elle est envoyée au channel layer
5. Tous les clients WebSocket du groupe reçoivent l'alerte en temps réel

---

### 9. `ia_prediction/` - Intelligence Artificielle

**Rôle** : Prédit les maladies animales using Machine Learning et fournit des explications

#### Architecture de l'IA

```
Données animal → Feature Engineering → Modèle Random Forest → Prédiction
                                                          ↓
                                                    Calcul SHAP
                                                          ↓
                                                Envoi n8n → LLM
                                                          ↓
                                            Explication générée + Alertes
```

#### `models.py` - Stockage des prédictions
```python
class PredictionResultat(models.Model):
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    declencheur = models.CharField(choices=[
        ('alimentation', 'Alimentation'),
        ('sante', 'Suivi santé'),
        ('gestation', 'Gestation'),
        ('manuel', 'Manuel'),
    ])
    est_malade = models.BooleanField()  # Résultat de la prédiction
    probabilite = models.FloatField()  # Probabilité de maladie (0-1)
    shap_values = models.JSONField()  # Valeurs SHAP pour explicabilité
    features_used = models.JSONField()  # Features utilisées pour la prédiction
    comparaison_historique = models.JSONField()  # Comparaison avec l'historique
    explication_llm = models.TextField()  # Explication générée par n8n/LLM
    envoye_n8n = models.BooleanField()  # Si envoyé avec succès à n8n
    date_prediction = models.DateTimeField(auto_now_add=True)
```

#### `predictor.py` - Moteur de prédiction IA 

**Fichier central de l'IA** - Contient toute la logique de prédiction

##### Architecture du fichier

```python
1. Imports et configuration
2. Chargement du modèle (cache en mémoire)
3. Définition des 112 features du modèle
4. Fonctions de feature engineering
5. Fonction de prédiction principale
6. Fonctions d'alerte
7. Fonction d'envoi à n8n
8. Fonction principale run_prediction()
```

##### 1. Chargement du modèle avec cache

```python
MODEL_PATH = Path(__file__).resolve().parent.parent.parent / 'models' / 'model_soutenance_simplon.joblib'
_model = None
_model_lock = threading.Lock()

def get_model():
    global _model
    if _model is None:
        with _model_lock:  # Thread-safe pour éviter les chargements multiples
            if _model is None:
                import joblib
                _model = joblib.load(MODEL_PATH)  # Charge le modèle Random Forest
                logger.info('Modèle IA chargé depuis %s', MODEL_PATH)
    return _model
```

**Pourquoi le cache ?** Le modèle Random Forest est volumineux (~50MB). Le charger à chaque prédiction serait inefficace. On le charge une seule fois et on le garde en mémoire.

##### 2. Les 112 features du modèle

```python
FEATURES = [
    # Features numériques (4)
    'age_mois', 'poids_kg', 'temperature_celsius', 'frequence_cardiaque',
    'quantite_aliment_kg', 'frequence_alimentation',
    
    # Espèce (one-hot encoding - 3 features, bovin est la référence)
    'espece_caprin', 'espece_ovin', 'espece_porcin',
    
    # Race (one-hot encoding - 81 features)
    'race_Africander', 'race_Alpine', 'race_Angora', ...,
    
    # Sexe (1 feature)
    'sexe_male',
    
    # Type d'aliment (one-hot encoding - 8 features)
    'aliment_type_Crop_Residues', 'aliment_type_Dry_Fodder', ...,
    
    # Stade de gestation (3 features)
    'gestation_stade_2e trimestre', 'gestation_stade_3e trimestre', 'gestation_stade_inconnu',
    
    # Source de données (2 features - toujours 0 pour données internes)
    'source_donnee_Kaggle - Animal Disease Prediction Using Symptoms',
    'source_donnee_Kaggle - Global Cattle Disease Detection...',
]
```

**One-hot encoding** : Technique pour représenter des variables catégorielles comme des nombres binaires. Par exemple, si l'espèce est "caprin" :
- `espece_caprin = 1`
- `espece_ovin = 0`
- `espece_porcin = 0`

##### 3. Fonctions de feature engineering

###### `_age_en_mois(date_naissance)`
```python
def _age_en_mois(date_naissance):
    """Calcule l'âge en mois depuis la date de naissance."""
    if not date_naissance:
        return 24  # Valeur par défaut neutre
    today = date.today()
    return max(1, (today.year - date_naissance.year) * 12 + (today.month - date_naissance.month))
```
Convertit la date de naissance en âge en mois pour le modèle.

###### `_race_feature(race_nom)`
```python
def _race_feature(race_nom):
    """Retourne le nom de la feature race correspondante ou None."""
    if not race_nom:
        return None
    key_with_space = f'race_{race_nom}'
    key_underscore = f'race_{race_nom.replace(" ", "_")}'
    if key_with_space in FEATURES:
        return key_with_space
    if key_underscore in FEATURES:
        return key_underscore
    return None
```
Mappe le nom de la race vers la feature correspondante dans le modèle (gère les espaces et underscores).

###### `_aliment_feature(type_aliment_nom)`
```python
def _aliment_feature(type_aliment_nom):
    """Retourne la feature aliment correspondante."""
    mapping = {
        'hay': 'aliment_type_Hay',
        'foin': 'aliment_type_Hay',
        'silage': 'aliment_type_Silage',
        'ensilage': 'aliment_type_Silage',
        'pasture': 'aliment_type_Pasture_Grass',
        'paturage': 'aliment_type_Pasture_Grass',
        ...
    }
    lower = type_aliment_nom.lower()
    for key, feature in mapping.items():
        if key in lower:
            return feature
    return 'aliment_type_inconnu'
```
Mappe le type d'aliment vers la feature correspondante avec gestion des synonymes.

###### `_gestation_stade(animal)`
```python
def _gestation_stade(animal):
    """Détermine le stade de gestation actif de l'animal."""
    gest = Gestation.objects.filter(animal=animal).exclude(
        statut__in=('Terminée', 'terminee', 'terminée')
    ).order_by('-date_debut').first()
    if not gest:
        return None
    jours = (date.today() - gest.date_debut).days if gest.date_debut else 0
    if jours < 90:
        return 'gestation_stade_2e trimestre'
    elif jours < 180:
        return 'gestation_stade_3e trimestre'
    else:
        return 'gestation_stade_inconnu'
```
Détermine le stade de gestation basé sur le nombre de jours depuis la saillie.

###### `_derniere_alimentation(animal)`
```python
def _derniere_alimentation(animal):
    return Alimentation.objects.filter(animal=animal).select_related(
        'type_aliment', 'frequence'
    ).order_by('-date_alimentation', '-id').first()
```
Récupère la dernière alimentation enregistrée pour l'animal.

###### `_mesures_sante(animal)`
```python
def _mesures_sante(animal):
    return list(SuiviSante.objects.filter(animal=animal).exclude(
        poids_kg__isnull=True,
        temperature_celsius__isnull=True,
        frequence_cardiaque__isnull=True,
    ).order_by('-date_debut', '-id'))
```
Récupère l'historique des mesures de santé avec les valeurs mesurées.

###### `_comparaison_historique(mesures)`
```python
def _comparaison_historique(mesures):
    """Compare la dernière mesure aux précédentes."""
    if len(mesures) < 2:
        return {'disponible': False, 'raison': 'Historique insuffisant'}
    actuelle, historiques = mesures[0], mesures[1:]
    resultat = {'disponible': True, 'mesures': {}}
    for champ in ('poids_kg', 'temperature_celsius', 'frequence_cardiaque'):
        valeur = getattr(actuelle, champ)
        valeurs = [float(getattr(m, champ)) for m in historiques if getattr(m, champ) is not None]
        if valeur is None or not valeurs:
            continue
        moyenne = sum(valeurs) / len(valeurs)
        ecart = float(valeur) - moyenne
        resultat['mesures'][champ] = {
            'actuelle': float(valeur),
            'moyenne_historique': round(moyenne, 2),
            'ecart': round(ecart, 2),
            'ecart_pct': round((ecart / moyenne) * 100, 2) if moyenne else None,
        }
    return resultat
```
Compare les dernières mesures de santé avec l'historique pour détecter les anomalies.

##### 4. `build_features()` - Construction du vecteur de features

```python
def build_features(animal, alimentation=None, suivi_sante=None):
    """
    Construit le DataFrame de features pour une prédiction.
    Retourne un DataFrame pandas avec les 112 colonnes dans l'ordre exact.
    """
    # Initialisation : toutes les features à 0
    row = {f: 0 for f in FEATURES}
    
    # Features numériques
    row['age_mois'] = _age_en_mois(animal.date_naissance)
    
    # Récupération des mesures de santé
    if suivi_sante is None:
        mesures_existantes = _mesures_sante(animal)
        suivi_sante = mesures_existantes[0] if mesures_existantes else None
    
    # Valeurs de santé avec valeurs de repli
    row['poids_kg'] = float(suivi_sante.poids_kg) if suivi_sante and suivi_sante.poids_kg is not None else float(animal.poids_naissance or 0)
    row['temperature_celsius'] = float(suivi_sante.temperature_celsius) if suivi_sante and suivi_sante.temperature_celsius is not None else 38.5
    row['frequence_cardiaque'] = float(suivi_sante.frequence_cardiaque) if suivi_sante and suivi_sante.frequence_cardiaque is not None else 70
    
    # Alimentation
    alimentation = alimentation or _derniere_alimentation(animal)
    if alimentation:
        row['quantite_aliment_kg'] = float(alimentation.quantite_kg or 0)
        # Conversion de la fréquence en nombre
        freq_nom = (alimentation.frequence.nom if alimentation.frequence else '').lower()
        if 'bi' in freq_nom or '2' in freq_nom:
            row['frequence_alimentation'] = 2
        elif 'tri' in freq_nom or '3' in freq_nom:
            row['frequence_alimentation'] = 3
        elif 'hebdo' in freq_nom:
            row['frequence_alimentation'] = 0.14
        else:
            row['frequence_alimentation'] = 1
    else:
        row['quantite_aliment_kg'] = 0
        row['frequence_alimentation'] = 0
    
    # Espèce (one-hot encoding)
    espece_lower = (animal.espece or '').lower()
    if espece_lower == 'caprin':
        row['espece_caprin'] = 1
    elif espece_lower == 'ovin':
        row['espece_ovin'] = 1
    elif espece_lower == 'porcin':
        row['espece_porcin'] = 1
    # bovin → toutes les features espèce = 0 (référence)
    
    # Race (one-hot encoding)
    race_nom = animal.race.nom if animal.race else ''
    race_feat = _race_feature(race_nom)
    if race_feat:
        row[race_feat] = 1
    
    # Sexe
    if (animal.sexe or '').lower() == 'male':
        row['sexe_male'] = 1
    
    # Type d'aliment
    if alimentation and alimentation.type_aliment:
        aliment_feat = _aliment_feature(alimentation.type_aliment.nom)
        row[aliment_feat] = 1
    else:
        row['aliment_type_inconnu'] = 1
    
    # Gestation
    stade = _gestation_stade(animal)
    if stade:
        row[stade] = 1
    
    # Source de données (toujours interne = 0)
    
    return pd.DataFrame([row], columns=FEATURES)
```

**Fonctionnement :**
1. Initialise toutes les features à 0
2. Remplit les features numériques avec les données de l'animal
3. Utilise les valeurs de repli si les données de santé sont manquantes
4. Active les features catégorielles correspondantes (one-hot encoding)
5. Retourne un DataFrame pandas avec exactement 112 colonnes

##### 5. `predict()` - Prédiction et calcul SHAP

```python
def predict(animal, alimentation=None, suivi_sante=None, declencheur='manuel'):
    """
    Lance la prédiction complète pour un animal.
    Retourne un dict avec :
      - est_malade (bool)
      - probabilite (float)
      - shap_values (dict feature → valeur)
      - features_used (dict)
    """
    import shap
    
    model = get_model()  # Charge le modèle (avec cache)
    mesures = _mesures_sante(animal)
    df = build_features(animal, alimentation, suivi_sante)  # Construit les features
    
    # Prédiction
    proba_array = model.predict_proba(df)[0]  # [P(sain), P(malade)]
    est_malade = bool(proba_array[1] >= 0.5)  # Seuil à 50%
    probabilite = float(proba_array[1])
    
    # Calcul SHAP (explicabilité)
    explainer = shap.TreeExplainer(model)
    shap_vals = explainer.shap_values(df)
    
    # Gestion des différentes versions de SHAP
    if isinstance(shap_vals, list):
        shap_class1 = shap_vals[1][0]  # Classe "malade"
    elif np.asarray(shap_vals).ndim == 3:
        shap_class1 = shap_vals[0, :, 1]
    else:
        shap_class1 = shap_vals[0]
    
    # Conversion en dictionnaire (features non nulles uniquement)
    shap_dict = {
        feat: round(float(val), 6)
        for feat, val in zip(FEATURES, shap_class1)
        if abs(val) > 1e-7
    }
    
    return {
        'est_malade': est_malade,
        'probabilite': probabilite,
        'shap_values': shap_dict,
        'features_used': df.iloc[0].to_dict(),
        'comparaison_historique': _comparaison_historique(mesures),
    }
```

**SHAP (SHapley Additive exPlanations)** : Méthode d'explicabilité qui attribue une contribution à chaque feature pour la prédiction.

**Exemple de sortie SHAP :**
```json
{
  "temperature_celsius": 0.15,      # Contribue positivement à "malade"
  "poids_kg": -0.08,                # Contribue négativement (réduit probabilité)
  "frequence_cardiaque": 0.12,      # Contribue positivement
  "espece_caprin": -0.02,          # Faible contribution négative
}
```

##### 6. Fonctions d'alerte

###### `_creer_alerte(animal, niveau, message)`
```python
def _creer_alerte(animal, niveau, message):
    from alertes.models import Alerte
    
    # Évite les doublons d'alertes non lues
    if Alerte.objects.filter(
        ferme=animal.ferme, animal=animal, message=message, statut='non_lue',
    ).exists():
        return None
    
    return Alerte.objects.create(
        ferme=animal.ferme, animal=animal,
        type_alerte=niveau, message=message,
    )
```
Crée une alerte en base de données avec protection contre les doublons.

###### `_alerte_depuis_n8n(animal, reponse_n8n)`
```python
def _alerte_depuis_n8n(animal, reponse_n8n):
    message = str(reponse_n8n.get('message_alerte') or reponse_n8n.get('alerte_message') or '').strip()
    if not _est_vrai(reponse_n8n.get('creer_alerte')) or not message:
        return None
    niveau = str(reponse_n8n.get('niveau_alerte') or 'Avertissement')
    return _creer_alerte(animal, niveau, message)
```
Crée une alerte basée sur la réponse de n8n/LLM.

###### `_alerte_variation_poids(animal)`
```python
def _alerte_variation_poids(animal):
    """Alerte si le poids vient d'être modifié directement sur la fiche animal."""
    variation = _variation_poids(animal)
    if not variation:
        return None
    avant_f, apres_f = variation
    delta = abs(apres_f - avant_f)
    delta_pct = (delta / avant_f * 100) if avant_f else 100
    
    # Seuil : 2kg ou 10%
    if delta < 2 and delta_pct < 10:
        return None
    
    nom = animal.nom or animal.numero_identification
    niveau = 'Avertissement' if delta_pct >= 20 or delta >= 5 else 'Info'
    message = f'Le poids de {nom} est passé de {avant_f:.2f} kg à {apres_f:.2f} kg.'
    return _creer_alerte(animal, niveau, message)
```
Détecte les variations significatives de poids lors de la modification de la fiche animal.

###### `_alerte_perte_poids_suivi(animal)`
```python
def _alerte_perte_poids_suivi(animal):
    """Détecte une perte de poids dans l'historique SuiviSante."""
    mesures = _mesures_sante(animal)
    if len(mesures) < 2:
        return None
    
    derniere = mesures[0]
    if derniere.poids_kg is None:
        return None
    
    poids_precedents = [float(m.poids_kg) for m in mesures[1:] if m.poids_kg is not None]
    if not poids_precedents:
        return None
    
    moyenne_avant = sum(poids_precedents) / len(poids_precedents)
    poids_actuel = float(derniere.poids_kg)
    delta = moyenne_avant - poids_actuel  # positif = perte
    
    if delta <= 0:
        return None  # pas de perte
    
    delta_pct = (delta / moyenne_avant * 100) if moyenne_avant else 100
    
    # Seuil : 2kg ou 5%
    if delta < 2 and delta_pct < 5:
        return None
    
    nom = animal.nom or animal.numero_identification
    niveau = 'Avertissement' if delta_pct >= 10 or delta >= 5 else 'Info'
    message = f'{nom} a perdu du poids récemment, surveillez son état.'
    return _creer_alerte(animal, niveau, message)
```
Détecte les pertes de poids dans l'historique des suivis de santé.

###### `_alerte_comportement(animal, suivi_sante=None)`
```python
def _alerte_comportement(animal, suivi_sante=None):
    """Crée une alerte si les observations contiennent des signaux préoccupants."""
    observations = (animal.observations or '').lower().strip()
    note_suivi = (getattr(suivi_sante, 'note', None) or '').lower().strip()
    texte = ' '.join(filter(None, [observations, note_suivi]))
    
    if not texte:
        return None
    
    # Mots-clés préoccupants
    _MOTS_CLES_ALERTE = [
        'moins réactif', 'apathique', 'faible', 'abattu',
        'ne mange pas', 'perte d\'appétit', 'diarrhée', 'fièvre',
        'boite', 'toux', 'tremble', 'déshydraté', 'abcès',
    ]
    
    for mot in _MOTS_CLES_ALERTE:
        if mot in texte:
            nom = animal.nom or animal.numero_identification
            source = animal.observations if mot in observations else suivi_sante.note
            message = f'{nom} présente un signe préoccupant : "{mot}". Note : {source}'
            return _creer_alerte(animal, 'Avertissement', message)
    return None
```
Détecte des mots-clés préoccupants dans les observations.

##### 7. `envoyer_n8n()` - Envoi au webhook n8n

```python
def envoyer_n8n(animal, resultat, n8n_url, declencheur='manuel', gestation=None):
    """
    Envoie le résultat + SHAP au webhook n8n pour justification LLM.
    Retourne (succès, réponse_n8n).
    """
    # Formatage des valeurs SHAP pour l'affichage
    shap_lines = '\n'.join(
        f'{feature}: {value:+.6f}'
        for feature, value in sorted(
            resultat['shap_values'].items(),
            key=lambda item: abs(item[1]),
            reverse=True
        )[:12]  # Top 12 features
    )
    
    # Construction du payload
    payload = {
        # Champs plats (compatibilité workflow existant)
        'animal_id': animal.id,
        'nom': animal.nom or animal.numero_identification,
        'espece': animal.espece or '',
        'etat_sante': animal.etat_sante or '',
        'poids_kg': resultat['features_used'].get('poids_kg'),
        'proba': resultat['probabilite'],
        'prediction_label': 'malade' if resultat['est_malade'] else 'sain',
        'observations': '\n'.join(filter(None, observations_parts)),
        'shap_lines': shap_lines,
        'historique_lines': json.dumps(resultat['comparaison_historique']),
        
        # Données structurées (évolution future)
        'animal': {
            'id': animal.id,
            'numero_identification': animal.numero_identification,
            'nom': animal.nom or '',
            'espece': animal.espece or '',
            'race': animal.race.nom if animal.race else '',
            'sexe': animal.sexe or '',
            'etat_sante': animal.etat_sante or '',
            'poids_kg': resultat['features_used'].get('poids_kg'),
            'age_mois': _age_en_mois(animal.date_naissance),
        },
        'prediction': {
            'est_malade': resultat['est_malade'],
            'probabilite': resultat['probabilite'],
            'declencheur': declencheur,
        },
        'shap_values': resultat['shap_values'],
        'features_used': {k: v for k, v in resultat['features_used'].items() if v != 0},
        'comparaison_historique': resultat['comparaison_historique'],
    }
    
    try:
        resp = requests.post(
            n8n_url,
            json=payload,
            timeout=15,
            headers={'Content-Type': 'application/json'},
        )
        resp.raise_for_status()
        logger.info('Résultat IA envoyé à n8n pour animal %s', animal.id)
        data = resp.json()
        return True, _normaliser_reponse_n8n(data)
    except requests.RequestException as exc:
        logger.warning('Échec envoi n8n pour animal %s : %s', animal.id, exc)
        return False, {}
```

**Workflow n8n :**
1. Le backend envoie les données + SHAP au webhook n8n
2. n8n formate les données pour un LLM (GPT, Claude, etc.)
3. Le LLM génère une explication en langage naturel
4. n8n renvoie l'explication + éventuellement une alerte à créer
5. Le backend persiste l'explication et crée l'alerte si demandé

##### 8. `run_prediction()` - Fonction principale

```python
def run_prediction(animal, alimentation=None, suivi_sante=None, gestation=None, declencheur='manuel'):
    """
    Fonction principale — prédit, envoie à n8n, persiste le résultat.
    Appelée depuis les signals ou l'API.
    Retourne l'instance PredictionResultat créée.
    """
    from django.conf import settings
    from ia_prediction.models import PredictionResultat
    
    n8n_url = getattr(settings, 'N8N_WEBHOOK_URL', '')
    
    try:
        # Étape 1 : Prédiction
        resultat = predict(animal, alimentation, suivi_sante, declencheur)
        
        # Ajout des données de suivi santé pour n8n
        if suivi_sante:
            resultat['suivi_sante'] = {
                'id': suivi_sante.id,
                'statut': suivi_sante.statut,
                'note': suivi_sante.note or '',
                'date_debut': suivi_sante.date_debut.isoformat() if suivi_sante.date_debut else None,
                'poids_kg': float(suivi_sante.poids_kg) if suivi_sante.poids_kg is not None else None,
                'temperature_celsius': float(suivi_sante.temperature_celsius) if suivi_sante.temperature_celsius is not None else None,
                'frequence_cardiaque': suivi_sante.frequence_cardiaque,
            }
    except Exception as exc:
        logger.error('Erreur prédiction IA pour animal %s : %s', animal.id, exc, exc_info=True)
        return None
    
    # Étape 2 : Envoi à n8n
    envoye = False
    reponse_n8n = {}
    if n8n_url:
        envoye, reponse_n8n = envoyer_n8n(animal, resultat, n8n_url, declencheur, gestation)
    
    # Étape 3 : Extraction de l'explication LLM
    explication = str(
        reponse_n8n.get('explication_llm')
        or reponse_n8n.get('explication')
        or reponse_n8n.get('conseil')
        or ''
    )
    
    # Étape 4 : Persistance en base
    pr = PredictionResultat.objects.create(
        animal=animal,
        declencheur=declencheur,
        est_malade=resultat['est_malade'],
        probabilite=resultat['probabilite'],
        shap_values=resultat['shap_values'],
        features_used={k: v for k, v in resultat['features_used'].items() if v != 0},
        comparaison_historique=resultat['comparaison_historique'],
        envoye_n8n=envoye,
        explication_llm=explication,
    )
    
    # Étape 5 : Création des alertes
    _alerte_depuis_n8n(animal, reponse_n8n)  # Alerte demandée par n8n
    _alerte_variation_poids(animal)  # Variation poids fiche
    _alerte_perte_poids_suivi(animal)  # Perte poids historique
    _alerte_comportement(animal, suivi_sante)  # Observations suspectes
    
    # Étape 6 : Historisation
    _historiser_prediction(animal, pr, explication)
    
    logger.info(
        'Prédiction animal %s : %s (%.0f%%) — décl. %s',
        animal.id,
        'MALADE' if pr.est_malade else 'SAIN',
        pr.probabilite * 100,
        declencheur,
    )
    return pr
```

**Flux complet :**
1. Construit les features depuis les données de l'animal
2. Lance la prédiction Random Forest
3. Calcule les valeurs SHAP
4. Envoie à n8n pour explication LLM
5. Persiste le résultat en base
6. Crée les alertes appropriées
7. Historise l'événement

#### `signals.py` - Déclenchement automatique des prédictions

```python
def _run_async(animal, alimentation=None, suivi_sante=None, gestation=None, declencheur='alimentation'):
    """Exécute l'analyse après validation effective de l'enregistrement."""
    def task():
        try:
            from ia_prediction.predictor import run_prediction
            run_prediction(
                animal, alimentation=alimentation, suivi_sante=suivi_sante,
                gestation=gestation, declencheur=declencheur,
            )
        except Exception as exc:
            logger.error('Signal IA — erreur prédiction animal %s : %s', animal.id, exc, exc_info=True)
    
    # Exécute après commit transactionnel
    transaction.on_commit(task)

# Signal : création alimentation
@receiver(post_save, sender='alimentation.Alimentation')
def on_alimentation_created(sender, instance, created, **kwargs):
    _run_async(instance.animal, alimentation=instance, declencheur='alimentation')

# Signal : création suivi santé
@receiver(post_save, sender='sante.SuiviSante')
def on_sante_created(sender, instance, created, **kwargs):
    _run_async(instance.animal, suivi_sante=instance, declencheur='sante')

# Signal : modification animal
@receiver(post_save, sender='moncheptel.Animal')
def on_animal_updated(sender, instance, created, **kwargs):
    if created:
        return
    _run_async(instance, declencheur='manuel')

# Signal : création/modification gestation
@receiver(post_save, sender='gestation.Gestation')
def on_gestation_saved(sender, instance, **kwargs):
    _run_async(instance.animal, gestation=instance, declencheur='gestation')
```

**Fonctionnement :**
- Les signals Django écoutent les événements de base de données
- Quand une alimentation, un suivi santé, ou une gestation est créé/modifié
- La prédiction IA est lancée automatiquement
- L'exécution est différée après le commit transactionnel pour garantir la cohérence

#### `views.py` - API de prédiction

```python
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def predire(request):
    """
    Déclenche une prédiction IA pour un animal.
    Corps JSON attendu :
      {
        "animal_id": <int>,
        "alimentation_id": <int|null>,
        "declencheur": "manuel"
      }
    """
    animal_id = request.data.get('animal_id')
    alimentation_id = request.data.get('alimentation_id')
    declencheur = request.data.get('declencheur', 'manuel')
    
    if not animal_id:
        return Response({'detail': 'animal_id est obligatoire.'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Vérifie que l'animal appartient à la ferme de l'utilisateur
    try:
        animal = Animal.objects.get(id=animal_id, ferme__proprietaire=request.user)
    except Animal.DoesNotExist:
        return Response({'detail': 'Animal introuvable.'}, status=status.HTTP_404_NOT_FOUND)
    
    # Lancement de la prédiction dans un thread (timeout 30s)
    result_container = {}
    
    def run():
        pr = run_prediction(animal, alimentation, declencheur)
        result_container['pr'] = pr
    
    t = threading.Thread(target=run)
    t.start()
    t.join(timeout=30)
    
    pr = result_container.get('pr')
    if not pr:
        return Response(
            {'detail': 'La prédiction a échoué ou a dépassé le délai.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    
    return Response(PredictionResultatSerializer(pr).data, status=status.HTTP_201_CREATED)
```

**Endpoints :**
- **POST /api/ia/predire/** : Déclenche une prédiction manuelle
- **GET /api/ia/predictions/** : Liste des prédictions de la ferme
- **GET /api/ia/predictions/{id}/** : Détail d'une prédiction
- **GET /api/ia/predictions/?animal={id}** : Prédictions d'un animal

---

### 10. `plans/` - Plans d'abonnement

**Rôle** : Définit les plans d'abonnement disponibles

#### `models.py`
```python
class Plan(models.Model):
    nom = models.CharField(max_length=120)
    description = models.TextField()
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    duree_mois = models.PositiveIntegerField()
    nb_fermes_max = models.PositiveIntegerField()
    nb_animaux_max = models.PositiveIntegerField()
    acces_ia = models.BooleanField()
    acces_support = models.BooleanField()
    acces_analyses = models.BooleanField()
```

---

### 11. `subscriptions/` - Abonnements utilisateurs

**Rôle** : Gère les abonnements actifs des utilisateurs

#### `models.py`
```python
class Subscription(models.Model):
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    date_debut = models.DateField()
    date_fin = models.DateField()
    statut = models.CharField(choices=[('actif', 'Actif'), ('expiré', 'Expiré'), ...])
    moyen_paiement = models.CharField()
```

#### Intégration PayDunya
- **POST /api/subscriptions/paydunya/** : Crée un checkout Paydunya
- **POST /api/subscriptions/paydunya/callback/** : Callback après paiement

---

## Concepts Django expliqués

### Models (Modèles)

Les **models** sont la couche d'accès aux données de Django. Ils définissent la structure de la base de données sous forme de classes Python.

```python
from django.db import models

class Animal(models.Model):
    nom = models.CharField(max_length=120)
    espece = models.CharField(max_length=20)
    date_naissance = models.DateField()
    
    class Meta:
        verbose_name = 'Animal'
        verbose_name_plural = 'Animaux'
        ordering = ['-date_naissance']
    
    def __str__(self):
        return f'{self.nom} ({self.espece})'
```

**Types de champs courants :**
- `CharField` : Texte court
- `TextField` : Texte long
- `IntegerField` : Entier
- `DecimalField` : Nombre décimal (pour argent, mesures)
- `DateField` / `DateTimeField` : Date/Heure
- `BooleanField` : Booléen
- `ForeignKey` : Relation vers un autre modèle
- `ManyToManyField` : Relation plusieurs-à-plusieurs

**Migrations** : Django génère automatiquement les fichiers de migration pour synchroniser les models avec la base de données.

### Views (Vues)

Les **views** contiennent la logique métier et traitent les requêtes HTTP.

```python
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Animal
from .serializers import AnimalSerializer

@api_view(['GET'])
def liste_animaux(request):
    animaux = Animal.objects.filter(ferme__proprietaire=request.user)
    serializer = AnimalSerializer(animaux, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def creer_animal(request):
    serializer = AnimalSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)
```

**Types de vues :**
- **Function-based views** : Fonctions simples
- **Class-based views** : Classes avec méthodes HTTP (get, post, put, delete)
- **ViewSets** : Classes REST Framework avec CRUD automatique

### Serializers

Les **serializers** convertissent les modèles Django en JSON et vice versa.

```python
from rest_framework import serializers
from .models import Animal

class AnimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Animal
        fields = '__all__'  # ou ['id', 'nom', 'espece']
        read_only_fields = ['numero_identification']
    
    def validate_poids_naissance(self, value):
        if value <= 0:
            raise serializers.ValidationError("Le poids doit être positif")
        return value
```

**Fonctions :**
- Sérialisation : Model → JSON (pour les réponses API)
- Désérialisation : JSON → Model (pour les requêtes API)
- Validation : Vérifie les données avant sauvegarde

### URLs Routing

Le **routing** connecte les URLs aux vues.

```python
from django.urls import path
from . import views

urlpatterns = [
    path('animaux/', views.liste_animaux, name='liste-animaux'),
    path('animaux/<int:id>/', views.detail_animal, name='detail-animal'),
    path('animaux/creer/', views.creer_animal, name='creer-animal'),
]
```

**Patterns de routage :**
- `<int:id>` : Capture un entier (ex: /animaux/42/)
- `<str:slug>` : Capture une chaîne (ex: /animaux/mon-animal/)
- `<uuid:id>` : Capture un UUID

### Signals (Signaux)

Les **signals** permettent de déclencher des actions automatiquement quand des événements de base de données se produisent.

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Animal

@receiver(post_save, sender=Animal)
def apres_creation_animal(sender, instance, created, **kwargs):
    if created:
        print(f"Nouvel animal créé : {instance.nom}")
```

**Signals courants :**
- `pre_save` : Avant sauvegarde
- `post_save` : Après sauvegarde
- `pre_delete` : Avant suppression
- `post_delete` : Après suppression

**Utilisation dans le projet :**
- `alertes/signals.py` : Broadcast alertes en temps réel
- `ia_prediction/signals.py` : Déclenchement auto IA
- `historique/signals.py` : Historisation automatique
- `sante/signals.py` : Synchronisation état santé

### Middleware

Le **middleware** est un pipeline de traitement des requêtes HTTP.

```python
class SimpleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Code exécuté avant la vue
        response = self.get_response(request)
        # Code exécuté après la vue
        return response
```

**Middleware dans le projet :**
- `CorsMiddleware` : Gère les requêtes cross-origin
- `JWTAuthMiddleware` : Authentifie les WebSockets

### Channels & WebSockets

**Channels** ajoute le support WebSockets à Django pour les communications en temps réel.

**Architecture :**
```
Client WebSocket → ASGI Server → Channel Layer → Consumer → Logique
                                            ↓
                                      Broadcast au groupe
```

**Channel Layer** : Backend de stockage des messages (InMemory, Redis, etc.)
- Stocke les messages pour les WebSockets
- Gère les groupes de clients
- Peut être InMemory (dev) ou Redis (prod)

**Consumer** : Équivalent d'une vue pour WebSockets
```python
class AlerteConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        # Traitement du message
    
    async def disconnect(self, close_code):
        # Nettoyage
```

**Routing WebSocket** :
```python
websocket_urlpatterns = [
    re_path(r'^ws/alertes/(?P<ferme_id>\d+)/$', AlerteConsumer.as_asgi()),
]
```

### Authentication JWT

**JWT (JSON Web Token)** : Méthode d'authentification stateless.

**Flux JWT :**
1. Client envoie username/password → POST /api/auth/token/
2. Serveur génère `access_token` et `refresh_token`
3. Client stocke les tokens
4. Client envoie `access_token` dans le header `Authorization: Bearer <token>`
5. Serveur valide le token et autorise l'accès
6. Quand `access_token` expire, client utilise `refresh_token` pour en obtenir un nouveau

**Configuration :**
```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
```

### Permissions

Les **permissions** contrôlent l'accès aux endpoints.

```python
from rest_framework import permissions

class IsFermeProprietaire(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.ferme.proprietaire == request.user
```

**Permissions courantes :**
- `IsAuthenticated` : Utilisateur connecté requis
- `IsAdminUser` : Administrateur requis
- `IsFermeProprietaire` : Propriétaire de la ferme requis

---

## Commands Django utiles

### Gestion du projet
```bash
python manage.py runserver              # Lance le serveur de développement
python manage.py shell                  # Shell Python interactif
python manage.py check                  # Vérifie les erreurs de projet
```

### Base de données
```bash
python manage.py makemigrations         # Crée les fichiers de migration
python manage.py migrate                # Applique les migrations
python manage.py showmigrations         # Affiche l'état des migrations
python manage.py sqlmigrate app 0001    # Affiche le SQL d'une migration
```

### Utilisateurs
```bash
python manage.py createsuperuser         # Crée un superutilisateur
python manage.py changepassword <user>   # Change le mot de passe
```

### Assets statiques
```bash
python manage.py collectstatic          # Collecte les fichiers statiques
python manage.py findstatic              # Trouve les fichiers statiques
```

### Tests
```bash
python manage.py test                    # Lance tous les tests
python manage.py test app                # Lance les tests d'une app
python manage.py test app.tests.TestClass  # Lance une classe de tests
```

---

## Déploiement

### Configuration production

1. **Variables d'environnement** :
```bash
DEBUG=False
SECRET_KEY=<clé_secrète>
ALLOWED_HOSTS=domaine.com,www.domaine.com
DB_HOST=postgres
DB_NAME=enclos_db
DB_USER=postgres
DB_PASSWORD=<mot_de_passe>
N8N_WEBHOOK_URL=https://n8n.example.com/webhook/...
```

2. **Base de données PostgreSQL** :
```bash
docker run -d --name postgres \
  -e POSTGRES_DB=enclos_db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -v enclos_pgdata:/var/lib/postgresql/data \
  postgres:16-alpine
```

3. **Serveur ASGI (Daphne)** :
```bash
daphne -b 0.0.0.0 -p 8000 enclos.asgi:application
```

4. **Serveur Web (Nginx)** :
```nginx
server {
    listen 80;
    server_name domaine.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

### Docker Compose

Le projet inclut une configuration Docker Compose complète :
- **Service db** : PostgreSQL
- **Service backend** : Django + Daphne
- **Service frontend** : React + Nginx

```bash
docker-compose up -d
```

---

## Bonnes pratiques Django

### 1. Utiliser les migrations
- Ne jamais modifier la base de données manuellement
- Toujours créer des migrations pour les changements de models
- Revoir les migrations avant de les appliquer en production

### 2. Sécurité
- Ne jamais commit la SECRET_KEY
- Utiliser `decouple` pour les variables d'environnement
- Valider toutes les entrées utilisateur
- Utiliser les permissions DRF

### 3. Performance
- Utiliser `select_related` et `prefetch_related` pour les requêtes
- Indexer les champs fréquemment filtrés
- Utiliser le cache pour les données lourdes (comme le modèle IA)

### 4. Organisation du code
- Une fonction par vue si possible
- Extraire la logique complexe dans des services
- Utiliser les signals pour la logique transversale
- Nommer les models, views, serializers de manière descriptive

### 5. Tests
- Écrire des tests pour la logique critique
- Tester les permissions
- Tester les validators
- Utiliser des factories pour les données de test

---

## Ressources pour approfondir

- [Documentation Django](https://docs.djangoproject.com/)
- [Documentation Django REST Framework](https://www.django-rest-framework.org/)
- [Documentation Channels](https://channels.readthedocs.io/)
- [Documentation scikit-learn](https://scikit-learn.org/)
- [Documentation SHAP](https://shap.readthedocs.io/)
- [JWT Authentication](https://django-rest-framework-simplejwt.readthedocs.io/)

---

##  Glossaire technique

- **ASGI** : Asynchronous Server Gateway Interface - Standard pour applications async
- **WSGI** : Web Server Gateway Interface - Standard pour applications sync
- **JWT** : JSON Web Token - Token d'authentification stateless
- **Middleware** : Couche de traitement des requêtes HTTP
- **Serializer** : Convertisseur Model ↔ JSON
- **Signal** : Événement déclenché par des actions de base de données
- **Migration** : Fichier de modification de la structure de base de données
- **ViewSet** : Vue DRF avec CRUD automatique
- **Consumer** : Vue pour WebSockets
- **Channel Layer** : Backend de stockage des messages WebSocket
- **SHAP** : Méthode d'explicabilité des modèles IA
- **One-hot encoding** : Représentation binaire de variables catégorielles
- **Feature engineering** : Transformation des données brutes en features pour l'IA
- **Random Forest** : Algorithme de Machine Learning (ensemble d'arbres de décision)

---

**Dernière mise à jour :** Septembre 2026
**Version :** 1.0.0
