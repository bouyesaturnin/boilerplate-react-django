# CLAUDE.md — Règles du projet boilerplate-react-django

## Stack technique

- **Backend** : Python 3.11, Django 5.2, DRF, Simple JWT, django-cors-headers
- **Frontend** : React 19, Vite 8, Tailwind CSS 4, React Router, Axios, Lucide React
- **Base de données** : SQLite (dev), PostgreSQL (prod)
- **Linter frontend** : oxlint

---

## Structure du projet

```
boilerplate-react-django/
├── .gitignore
├── .venv/                      Environnement virtuel Python (ne pas versionner)
├── backend/
│   ├── accounts/               Auth : modèle User personnalisé, serializers, vues, tests
│   ├── core/                   Endpoint de santé et utilitaires communs
│   ├── config/                 Settings, URLs, WSGI/ASGI
│   ├── .env                    Variables d'environnement (ne pas versionner)
│   ├── .env.example            Template des variables d'environnement
│   ├── Procfile                Déploiement Gunicorn
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── api/                Client Axios et appels API
    │   ├── components/ui/      Composants réutilisables du design system
    │   ├── features/auth/      AuthContext (login, register, logout)
    │   ├── hooks/              Hooks React personnalisés (useAuth)
    │   ├── layouts/            Layouts de page (MainLayout)
    │   ├── pages/              Pages de l'application
    │   └── routes/             AppRouter, ProtectedRoute
    └── .env.example
```

---

## Règles de développement

### Sécurité
- Ne jamais mettre de secrets dans le code source
- Ne jamais versionner `.env` (ni ses variantes), `.venv/`, `node_modules/`, `db.sqlite3`
- `DEBUG=True` uniquement en développement
- `CORS_ALLOWED_ORIGINS` doit être restrictif en production
- Valider toutes les entrées côté serveur
- Ne jamais retourner d'informations sensibles dans les erreurs API
- Ne jamais journaliser de mot de passe, token JWT, cookie ou secret
- Ne jamais faire confiance à un en-tête de proxy (`X-Forwarded-For`, `X-Forwarded-Proto`) sans configuration
  explicite : `DRF_NUM_PROXIES=0` et `TRUST_PROXY_SSL_HEADER=False` par défaut
- Capturer des exceptions précises (ex. `TokenError`) : une panne serveur ne doit pas devenir une erreur 400
- Inscription : les validateurs `AUTH_PASSWORD_VALIDATORS` s'appliquent via `RegisterSerializer.validate`
- Limitation de débit (`ScopedRateThrottle`) : scopes `auth_login` 10/min, `auth_register` 5/h,
  `auth_refresh` 30/min ; tout nouvel endpoint public sensible doit recevoir un scope

### Variables d'environnement (backend/.env, voir `.env.example`)
| Variable | Défaut | Rôle |
|---|---|---|
| `SECRET_KEY` | — (obligatoire) | Signe aussi les JWT ; une clé distincte par environnement |
| `DEBUG` | `False` | `True` uniquement en développement |
| `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS` | voir `.env.example` | Listes séparées par des virgules, éléments vides ignorés |
| `TRUST_PROXY_SSL_HEADER` | `False` | `True` seulement derrière un proxy de confiance |
| `DRF_NUM_PROXIES` | `0` | Proxys de confiance pour l'IP client ; à mesurer avant de changer |
| `SECURE_HSTS_PRELOAD` | `False` | Activation explicite seulement |
| `DJANGO_ADMIN_PATH` | `admin` | Lettres, chiffres, `-`, `_` ; ni `api` ni `static` |
| `DATABASE_URL` | vide (SQLite) | PostgreSQL en production |

### Backend Django
- `AUTH_USER_MODEL = "accounts.User"` — ne jamais modifier après la première migration
- Toutes les nouvelles routes API sous `/api/v1/`
- `/api/health/` conservé pour la compatibilité
- Permissions DRF explicites sur chaque vue
- Utiliser `get_user_model()` plutôt qu'importer `User` directement

### Frontend React
- Tailwind CSS 4 uniquement — ne pas créer de `tailwind.config.js` (syntaxe CSS3)
- `@import "tailwindcss"` dans `index.css` suffit
- Tous les appels API passent par `src/api/client.js` (jamais d'`axios` direct)
- Routes protégées via `ProtectedRoute` dans `AppRouter.jsx`
- Utiliser les composants du design system (`Button`, `Input`, `Alert`…) plutôt que des classes Tailwind ad hoc

### Base de données
- Ne jamais supprimer les migrations
- Ne jamais modifier `AUTH_USER_MODEL` après la première migration
- Ne jamais lancer de reset de migrations sans accord explicite

---

## Fichiers à ne pas modifier sans justification

Ces fichiers sont stables et fonctionnels. Les modifier sans raison précise risque de casser l'authentification, les tests ou la configuration.

| Fichier | Raison |
|---------|--------|
| `accounts/migrations/0001_initial.py` | Migration initiale du modèle User — ne jamais supprimer |
| `config/settings.py` | Configuration centrale — modifier via `.env` autant que possible |
| `src/api/client.js` | Gère le refresh token et la queue des requêtes — logique fragile, couverte par `client.test.js` |
| `src/features/auth/AuthContext.jsx` | État global d'authentification — toute modification impacte toute l'app |
| `src/features/auth/session.js` | Fin de session (déconnexion + nettoyage local même en cas d'erreur) |
| `backend/Procfile` | `collectstatic` avant Gunicorn : sans lui, l'admin renvoie une 500 en production |
| `src/routes/ProtectedRoute.jsx` | Garde de sécurité des routes privées |

---

## Commandes de développement

### Backend (depuis la racine du projet)

```powershell
.venv\Scripts\activate
cd backend
python manage.py runserver        # Lancer le serveur (port 8000)
python manage.py check            # Vérifier la configuration
python manage.py migrate          # Appliquer les migrations
python manage.py makemigrations   # Créer de nouvelles migrations
python manage.py createsuperuser  # Créer un administrateur (email comme identifiant)
python manage.py test             # Lancer tous les tests backend
python manage.py makemigrations --check --dry-run  # Vérifier qu'aucune migration n'est en attente
```

### Frontend (depuis le dossier frontend/)

```powershell
npm run dev      # Serveur de développement (port 5173)
npm test         # Tests du client API et de la session (node:test, sans dépendance)
npm run build    # Build de production
npm run lint     # Vérification du code (oxlint)
npm run preview  # Prévisualiser le build de production
```

### Vérification complète avant un commit

```powershell
cd backend ; python manage.py check ; python manage.py makemigrations --check --dry-run ; python manage.py test
cd ..\frontend ; npm test ; npm run lint ; npm run build
cd .. ; git diff --check ; git add -A --dry-run   # contrôler qu'aucun fichier sensible n'est proposé
```

---

## Endpoints API

| Méthode | URL | Accès | Description |
|---------|-----|-------|-------------|
| GET | `/api/health/` | Public | Santé de l'API (compatibilité) |
| GET | `/api/v1/health/` | Public | Santé de l'API |
| POST | `/api/v1/auth/register/` | Public | Inscription |
| POST | `/api/v1/auth/login/` | Public | Connexion (retourne JWT) |
| POST | `/api/v1/auth/token/refresh/` | Public | Rafraîchir le token |
| POST | `/api/v1/auth/logout/` | Authentifié | Déconnexion + blacklist |
| GET | `/api/v1/auth/me/` | Authentifié | Lire le profil utilisateur |
| PATCH | `/api/v1/auth/me/` | Authentifié | Modifier le profil |

---

## Ajouter une fonctionnalité

Exemple : ajouter une feature `projects` avec une API et une page React.

### 1. Créer l'app Django

```powershell
cd backend
python manage.py startapp projects
```

Enregistrer dans `config/settings.py` :
```python
INSTALLED_APPS = [
    ...
    "projects",
]
```

### 2. Créer le modèle

```python
# backend/projects/models.py
from django.db import models
from django.conf import settings

class Project(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
```

```powershell
python manage.py makemigrations projects
python manage.py migrate
```

### 3. Écrire le serializer

```python
# backend/projects/serializers.py
from rest_framework import serializers
from .models import Project

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ("id", "name", "created_at")
        read_only_fields = ("id", "created_at")
```

### 4. Écrire la vue

```python
# backend/projects/views.py
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Project
from .serializers import ProjectSerializer

class ProjectListCreateView(generics.ListCreateAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Project.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
```

### 5. Câbler l'URL

```python
# backend/projects/urls.py
from django.urls import path
from .views import ProjectListCreateView

urlpatterns = [
    path("", ProjectListCreateView.as_view(), name="project-list"),
]
```

```python
# backend/config/urls.py — ajouter :
path("api/v1/projects/", include("projects.urls")),
```

### 6. Écrire les tests

```python
# backend/projects/tests.py
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()

class ProjectTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@test.com", username="user", password="pass1234"
        )
        login = self.client.post("/api/v1/auth/login/", {
            "email": "user@test.com", "password": "pass1234"
        })
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login.data['access']}"
        )

    def test_create_project(self):
        r = self.client.post("/api/v1/projects/", {"name": "Mon projet"})
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_list_projects(self):
        r = self.client.get("/api/v1/projects/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_unauthenticated_denied(self):
        self.client.credentials()
        r = self.client.get("/api/v1/projects/")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)
```

```powershell
python manage.py test projects
```

### 7. Connecter à React

```javascript
// frontend/src/api/projects.js
import client from './client'

export const projectsApi = {
  list: () => client.get('/projects/'),
  create: (data) => client.post('/projects/', data),
}
```

### 8. Créer la page React

```jsx
// frontend/src/pages/ProjectsPage.jsx
import { useEffect, useState } from 'react'
import { projectsApi } from '../api/projects'
import { Card, CardBody } from '../components/ui/Card'
import Spinner from '../components/ui/Spinner'
import Alert from '../components/ui/Alert'

export default function ProjectsPage() {
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    projectsApi.list()
      .then(({ data }) => setProjects(data.results ?? data))
      .catch(() => setError('Impossible de charger les projets.'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Spinner />
  if (error) return <Alert variant="error">{error}</Alert>

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-gray-900">Projets</h1>
      {projects.map((p) => (
        <Card key={p.id}>
          <CardBody>{p.name}</CardBody>
        </Card>
      ))}
    </div>
  )
}
```

### 9. Ajouter la route dans AppRouter

```jsx
// Ajouter dans les routes protégées de src/routes/AppRouter.jsx :
import ProjectsPage from '../pages/ProjectsPage'

<Route path="projects" element={<ProjectsPage />} />
```

### 10. Vérifier lint et build

```powershell
cd frontend && npm run lint && npm run build
cd backend && python manage.py check
```

---

## Checklist avant un commit

- [ ] `python manage.py check` → 0 issue
- [ ] `python manage.py test` → tous les tests passent
- [ ] `npm run lint` → 0 erreur
- [ ] `npm run build` → build propre
- [ ] Aucun secret dans les fichiers modifiés
- [ ] Aucune migration supprimée ou modifiée
