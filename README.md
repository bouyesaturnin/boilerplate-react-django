# Boilerplate React + Django

Base de départ pour applications SaaS et projets métier.

**Stack :** React 19 · Vite 8 · Tailwind CSS 4 · Django 5.2 · DRF · Simple JWT

---

## Prérequis

- Python 3.11+
- Node.js 20+
- npm 10+
- Git

---

## Installation (développement)

Toutes les commandes s'exécutent **depuis la racine du projet** sauf indication contraire.

### 1. Cloner le projet

```powershell
git clone <url-du-repo>
cd boilerplate-react-django
```

### 2. Environnement virtuel Python

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 3. Backend Django

```powershell
# Installer les dépendances
pip install -r backend/requirements.txt

# Configurer les variables d'environnement
copy backend\.env.example backend\.env
# Ouvrir backend\.env et remplacer SECRET_KEY par une vraie clé (voir commande ci-dessous)
```

Générer une `SECRET_KEY` :
```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

```powershell
# Appliquer les migrations
cd backend
python manage.py migrate

# (Optionnel) Créer un superutilisateur pour l'interface admin
python manage.py createsuperuser
```

> **Note :** ce projet utilise l'**email** comme identifiant (pas le username).
> Django demandera dans cet ordre : `Email address` → `Username` → `Password`.

```powershell
# Revenir à la racine
cd ..
```

### 4. Frontend React

```powershell
cd frontend
npm install
cd ..
```

---

## Lancement en développement

Ouvrir **deux terminaux** depuis la racine du projet.

```powershell
# Terminal 1 — Backend Django (port 8000)
.venv\Scripts\activate
cd backend
python manage.py runserver
```

```powershell
# Terminal 2 — Frontend React (port 5173)
cd frontend
npm run dev
```

Application disponible sur `http://localhost:5173`
API disponible sur `http://localhost:8000`

---

## Vérifications et tests

```powershell
# Vérifier la configuration Django
cd backend && python manage.py check

# Vérifier qu'aucune migration n'est en attente
cd backend && python manage.py makemigrations --check --dry-run

# Lancer les tests backend (authentification, autorisations, limitation de débit, réglages)
cd backend && python manage.py test

# Lancer les tests frontend (client API, renouvellement JWT, déconnexion) — node:test, sans dépendance
cd frontend && npm test

# Linter frontend
cd frontend && npm run lint

# Build de production frontend
cd frontend && npm run build
```

Les tests de réglages lancent de courts processus Django avec des variables fictives : ils ne lisent ni ne modifient `backend/.env`.

---

## Protections de sécurité incluses

| Protection | Détail |
|---|---|
| Mots de passe | Validateurs Django appliqués à l'inscription : longueur, mots de passe courants, uniquement numériques, trop proches de l'email ou du nom d'utilisateur |
| Limitation de débit | Par IP : connexion 10/min, inscription 5/h, renouvellement du token 30/min (réponse 429). Compteurs en mémoire, propres à chaque worker : ce n'est pas une protection contre une attaque distribuée |
| IP client | `X-Forwarded-For` ignoré par défaut (`DRF_NUM_PROXIES=0`) : un client ne peut pas falsifier son IP pour contourner les limites |
| JWT | Access token 15 min, refresh token 7 jours, rotation et blacklist de l'ancien refresh token |
| Déconnexion | Le frontend envoie le refresh token courant, même après une rotation ; l'état local est nettoyé même si le serveur échoue. Une panne serveur n'est pas masquée en « token invalide » |
| Client API | Un seul renouvellement pour des requêtes concurrentes, pas de boucle, pas de renouvellement sur les endpoints d'authentification |
| HTTPS (`DEBUG=False`) | Redirection HTTPS, HSTS 1 an (preload désactivé par défaut), cookies sécurisés. En-tête de proxy pris en compte seulement si `TRUST_PROXY_SSL_HEADER=True` |
| Admin | Chemin configurable (`DJANGO_ADMIN_PATH`) ; il ne remplace pas l'authentification de l'admin |
| Journaux | Avertissements et erreurs Django vers la console, sans en-têtes, corps de requête ni tokens |

Limite connue : un access token reste valide jusqu'à son expiration (15 min) après la déconnexion ; les tokens sont stockés dans `localStorage`.

---

## Endpoints API

| Méthode | URL | Accès | Description |
|---------|-----|-------|-------------|
| GET | `/api/v1/health/` | Public | Santé de l'API |
| POST | `/api/v1/auth/register/` | Public | Inscription |
| POST | `/api/v1/auth/login/` | Public | Connexion — retourne access + refresh token |
| POST | `/api/v1/auth/token/refresh/` | Public | Rafraîchir le token d'accès |
| POST | `/api/v1/auth/logout/` | Authentifié | Déconnexion + blacklist du refresh token |
| GET | `/api/v1/auth/me/` | Authentifié | Lire le profil utilisateur |
| PATCH | `/api/v1/auth/me/` | Authentifié | Modifier le profil (first_name, last_name, username) |

---

## Pages React

| URL | Accès | Description |
|-----|-------|-------------|
| `/` | Public | Page d'accueil |
| `/login` | Public | Connexion |
| `/register` | Public | Inscription |
| `/dashboard` | Authentifié | Tableau de bord (profil utilisateur) |

---

## Démarrer un nouveau projet depuis ce boilerplate

Cette procédure permet de créer un nouveau projet indépendant, sans récupérer les secrets, la base de données ou les données de l'ancien projet.

### 1. Copier le code source

```powershell
# Copier le dossier sous un nouveau nom
xcopy /E /I boilerplate-react-django mon-nouveau-projet
cd mon-nouveau-projet
```

Ou via Git (recommandé) :
```powershell
git clone <url-du-repo> mon-nouveau-projet
cd mon-nouveau-projet
# Supprimer le lien avec le dépôt d'origine
Remove-Item -Recurse -Force .git
git init
```

### 2. Supprimer les données de l'ancien projet

```powershell
# Supprimer la base de données (ne contient que des données de dev)
Remove-Item backend\db.sqlite3 -ErrorAction SilentlyContinue

# Supprimer les secrets (ne jamais copier un .env d'un projet à l'autre)
Remove-Item backend\.env -ErrorAction SilentlyContinue
```

### 3. Créer un nouvel environnement virtuel

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt
```

### 4. Configurer les secrets du nouveau projet

```powershell
copy backend\.env.example backend\.env
```

Ouvrir `backend\.env` et générer une nouvelle `SECRET_KEY` :
```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Coller la clé générée dans `backend\.env`.

### 5. Initialiser la base de données

```powershell
cd backend
python manage.py migrate
python manage.py createsuperuser
cd ..
```

### 6. Installer les dépendances frontend

```powershell
cd frontend
npm install
cd ..
```

### 7. Adapter le nom du projet (optionnel)

| Fichier | Champ à modifier |
|---------|-----------------|
| `frontend/index.html` | `<title>` |
| `frontend/package.json` | `"name"` |
| `README.md` | Titre et description |
| `CLAUDE.md` | Titre |

### 8. Lancer le projet

```powershell
# Terminal 1
.venv\Scripts\activate && cd backend && python manage.py runserver

# Terminal 2
cd frontend && npm run dev
```

---

## Déploiement en production

### Variables d'environnement (`backend/.env`)

```env
SECRET_KEY=<générer avec la commande ci-dessus, une clé distincte par environnement>
DEBUG=False
ALLOWED_HOSTS=mondomaine.com,www.mondomaine.com
CORS_ALLOWED_ORIGINS=https://mondomaine.com
DATABASE_URL=postgresql://user:password@host:5432/dbname
# Selon l'hébergement (voir backend/.env.example) :
# CSRF_TRUSTED_ORIGINS=https://mondomaine.com
# TRUST_PROXY_SSL_HEADER=True     # uniquement derrière un proxy de confiance
# DRF_NUM_PROXIES=0               # à mesurer sur l'hébergeur avant de changer
# DJANGO_ADMIN_PATH=gestion-a-personnaliser
```

### Préparer le backend

```bash
# Activer l'environnement virtuel
source .venv/bin/activate  # Linux/Mac
# ou : .venv\Scripts\activate  # Windows

pip install -r backend/requirements.txt
# Pour PostgreSQL : décommenter psycopg2 dans requirements.txt puis :
# pip install psycopg2==2.9.10

cd backend
python manage.py migrate
python manage.py collectstatic --noinput
```

### Lancer avec Gunicorn

```bash
cd backend
gunicorn config.wsgi --workers 2 --bind 0.0.0.0:8000
```

### Builder le frontend

```bash
cd frontend
npm install
npm run build
# Fichiers de sortie dans frontend/dist/
```

### Architecture recommandée

```
Internet → Nginx
              ├── /        → frontend/dist/   (React, fichiers statiques)
              └── /api/    → Gunicorn:8000    (Django)
```

**Configuration Nginx minimale :**

```nginx
server {
    listen 80;
    server_name mondomaine.com;

    location / {
        root /chemin/vers/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Derrière ce Nginx (et lui seul), activer `TRUST_PROXY_SSL_HEADER=True` ; pour la limitation de débit par IP,
vérifier l'en-tête `X-Forwarded-For` réellement reçu avant de régler `DRF_NUM_PROXIES`.

### Plateformes cloud (Railway, Render, Heroku)

Le fichier `backend/Procfile` est préconfiguré :
```
web: python manage.py collectstatic --noinput && gunicorn config.wsgi --workers 2 --bind 0.0.0.0:$PORT
```

- `collectstatic` est lancé au démarrage, dans le conteneur qui sert l'application : avec `DEBUG=False`,
  l'admin renvoie une erreur 500 si le manifeste des fichiers statiques est absent.
- Les migrations (`python manage.py migrate --noinput`) se lancent dans la commande de pré-déploiement
  de la plateforme, pas dans le `Procfile`.
- Ces réglages sont vérifiés par des tests locaux ; un déploiement réel reste à valider sur la plateforme.

---

## Design system — composants disponibles

```jsx
import Button from './components/ui/Button'
import Input from './components/ui/Input'
import Alert from './components/ui/Alert'
import Badge from './components/ui/Badge'
import { Card, CardHeader, CardBody, CardFooter } from './components/ui/Card'
import Spinner from './components/ui/Spinner'

<Button variant="primary" loading={true}>Envoyer</Button>
<Button variant="secondary">Annuler</Button>
<Button variant="destructive">Supprimer</Button>
<Button variant="ghost" size="sm">Voir</Button>

<Input label="Email" error="Email invalide" helper="Format: nom@domaine.com" />

<Alert variant="success" dismissible>Opération réussie.</Alert>
<Alert variant="error">Une erreur est survenue.</Alert>
<Alert variant="warning">Attention.</Alert>
<Alert variant="info">Information.</Alert>

<Badge variant="success">Actif</Badge>
<Badge variant="warning">En attente</Badge>
<Badge variant="error">Erreur</Badge>

<Card>
  <CardHeader><h2>Titre</h2></CardHeader>
  <CardBody>Contenu</CardBody>
  <CardFooter>Actions</CardFooter>
</Card>

<Spinner size="md" />
```

---

## Structure du projet

```
boilerplate-react-django/
├── .gitignore
├── .venv/                      Environnement virtuel Python (non versionné)
├── CLAUDE.md                   Règles du projet pour Claude Code
├── README.md
│
├── backend/
│   ├── .env                    Secrets locaux (non versionné)
│   ├── .env.example            Template des variables d'environnement
│   ├── Procfile                Déploiement Gunicorn
│   ├── requirements.txt
│   ├── manage.py
│   ├── accounts/               Auth : modèle User, serializers, vues, tests
│   │   └── migrations/
│   ├── core/                   Health check
│   └── config/                 Settings, URLs, WSGI
│
└── frontend/
    ├── .env.example
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── api/                Client Axios + fonctions auth
        ├── components/ui/      Design system (Button, Input, Alert, Badge, Card, Spinner)
        ├── features/auth/      AuthContext (login, register, logout)
        ├── hooks/              useAuth
        ├── layouts/            MainLayout
        ├── pages/              Home, Login, Register, Dashboard, 404
        └── routes/             AppRouter, ProtectedRoute
```
