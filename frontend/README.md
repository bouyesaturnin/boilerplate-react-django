# Frontend — Boilerplate React + Django

Application React construite avec Vite et Tailwind CSS 4.

---

## Stack

- **React 19** — bibliothèque UI
- **Vite 8** — bundler et serveur de développement
- **Tailwind CSS 4** — styles via `@import "tailwindcss"` dans `index.css`
- **React Router 7** — navigation et routes protégées
- **Axios** — client HTTP avec gestion automatique du refresh JWT
- **Lucide React** — icônes
- **oxlint** — linter

---

## Commandes

```powershell
# Depuis le dossier frontend/
npm install       # Installer les dépendances
npm run dev       # Serveur de développement → http://localhost:5173
npm run build     # Build de production → frontend/dist/
npm run lint      # Vérification du code
npm run preview   # Prévisualiser le build de production
```

---

## Arborescence `src/`

```
src/
├── api/
│   ├── client.js           Client Axios central — injecte le JWT, gère le refresh auto
│   └── auth.js             Fonctions : login, register, logout, me, refreshToken
│
├── components/ui/          Design system — composants réutilisables
│   ├── Alert.jsx           Alertes : success | error | warning | info
│   ├── Badge.jsx           Badges de statut
│   ├── Button.jsx          Boutons : primary | secondary | destructive | ghost
│   ├── Card.jsx            Conteneur : Card, CardHeader, CardBody, CardFooter
│   ├── Input.jsx           Champ de formulaire avec label, erreur et helper
│   ├── Navbar.jsx          Navigation principale
│   └── Spinner.jsx         Indicateur de chargement
│
├── features/auth/
│   └── AuthContext.jsx     Contexte global : isAuthenticated, login, register, logout
│
├── hooks/
│   └── useAuth.js          Hook : accès au contexte auth depuis n'importe quel composant
│
├── layouts/
│   └── MainLayout.jsx      Layout principal — Navbar + <Outlet />
│
├── pages/
│   ├── HomePage.jsx        Page d'accueil publique
│   ├── LoginPage.jsx       Formulaire de connexion
│   ├── RegisterPage.jsx    Formulaire d'inscription
│   ├── DashboardPage.jsx   Tableau de bord (route protégée)
│   └── NotFoundPage.jsx    Page 404
│
└── routes/
    ├── AppRouter.jsx       Définition de toutes les routes
    └── ProtectedRoute.jsx  Redirige vers /login si non authentifié
```

---

## Proxy API

Vite redirige automatiquement les requêtes `/api/*` vers `http://localhost:8000` en développement.
Aucune variable d'environnement n'est nécessaire — le proxy est configuré dans `vite.config.js`.

En production, Nginx (ou équivalent) assure ce rôle de proxy.

---

## Design system

### Button

```jsx
import Button from './components/ui/Button'

<Button variant="primary">Envoyer</Button>
<Button variant="secondary">Annuler</Button>
<Button variant="destructive">Supprimer</Button>
<Button variant="ghost" size="sm">Voir</Button>
<Button loading={true}>Chargement…</Button>
<Button disabled>Désactivé</Button>
```

Variants : `primary` | `secondary` | `destructive` | `ghost`
Tailles : `sm` | `md` (défaut) | `lg`

### Input

```jsx
import Input from './components/ui/Input'

<Input id="email" name="email" type="email" label="Email" />
<Input label="Mot de passe" type="password" error="Mot de passe incorrect" />
<Input label="Username" helper="Lettres et chiffres uniquement" />
```

### Alert

```jsx
import Alert from './components/ui/Alert'

<Alert variant="success">Compte créé avec succès.</Alert>
<Alert variant="error">Identifiants incorrects.</Alert>
<Alert variant="warning" dismissible>Session expirée.</Alert>
<Alert variant="info" title="Information">Mise à jour disponible.</Alert>
```

### Badge

```jsx
import Badge from './components/ui/Badge'

<Badge variant="success">Actif</Badge>
<Badge variant="warning">En attente</Badge>
<Badge variant="error">Erreur</Badge>
<Badge variant="primary">Nouveau</Badge>
```

### Card

```jsx
import { Card, CardHeader, CardBody, CardFooter } from './components/ui/Card'

<Card>
  <CardHeader><h2>Titre</h2></CardHeader>
  <CardBody>Contenu principal</CardBody>
  <CardFooter>Actions</CardFooter>
</Card>
```

### Spinner

```jsx
import Spinner from './components/ui/Spinner'

<Spinner size="sm" />
<Spinner size="md" />   {/* défaut */}
<Spinner size="lg" />
```

---

## Authentification

L'état d'authentification est géré par `AuthContext`. Utiliser le hook `useAuth` dans n'importe quel composant :

```jsx
import { useAuth } from '../features/auth/AuthContext'
// ou
import { useAuth } from '../hooks/useAuth'

function MonComposant() {
  const { isAuthenticated, user, login, logout } = useAuth()
  ...
}
```

Le client Axios (`src/api/client.js`) gère automatiquement :
- L'injection du token JWT dans chaque requête
- Le refresh automatique du token expiré (sans déconnecter l'utilisateur)
- La mise en file d'attente des requêtes simultanées pendant le refresh
- La redirection vers `/login` si le refresh échoue

---

## Ajouter une page

1. Créer `src/pages/MaPage.jsx`
2. Ajouter la route dans `src/routes/AppRouter.jsx`
3. Si la page est protégée, la placer à l'intérieur du bloc `<Route element={<ProtectedRoute />}>`

```jsx
// AppRouter.jsx — exemple
import MaPage from '../pages/MaPage'

// Route publique
<Route path="ma-page" element={<MaPage />} />

// Route protégée
<Route element={<ProtectedRoute />}>
  <Route path="ma-page-privee" element={<MaPage />} />
</Route>
```

## Ajouter un appel API

Créer un fichier dans `src/api/` :

```javascript
// src/api/projets.js
import client from './client'

export const projetsApi = {
  list: () => client.get('/projets/'),
  create: (data) => client.post('/projets/', data),
  delete: (id) => client.delete(`/projets/${id}/`),
}
```

Utiliser dans un composant :

```jsx
import { projetsApi } from '../api/projets'

const { data } = await projetsApi.list()
```

---

## Couleur primaire (rebranding)

La couleur `primary` est définie dans `src/index.css` via `@theme`. Pour changer la couleur de tout le projet, modifier les valeurs OKLCH dans ce bloc :

```css
@theme {
  --color-primary-600: oklch(51% 0.222 264.1);  /* ← couleur principale */
  ...
}
```
