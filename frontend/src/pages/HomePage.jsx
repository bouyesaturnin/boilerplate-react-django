import { Link } from 'react-router-dom'
import Button from '../components/ui/Button'
import Badge from '../components/ui/Badge'

export default function HomePage() {
  return (
    <div className="py-20 text-center">
      <Badge variant="primary" className="mb-4">Boilerplate v1.0</Badge>

      <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl">
        React + Django
      </h1>
      <p className="mx-auto mt-4 max-w-xl text-lg text-gray-500">
        Base de départ pour vos projets SaaS et applications métier.
        Auth JWT, design system, prêt à déployer.
      </p>

      <div className="mt-8 flex justify-center gap-3">
        <Link to="/register">
          <Button size="lg">Commencer</Button>
        </Link>
        <Link to="/login">
          <Button variant="secondary" size="lg">Se connecter</Button>
        </Link>
      </div>

      <div className="mx-auto mt-16 grid max-w-2xl grid-cols-1 gap-4 text-left sm:grid-cols-3">
        {[
          { title: 'Auth JWT', desc: 'Inscription, connexion, refresh token, blacklist.' },
          { title: 'Design system', desc: 'Composants Tailwind CSS 4 réutilisables.' },
          { title: 'Prêt à étendre', desc: 'Structure claire pour vos features métier.' },
        ].map(({ title, desc }) => (
          <div key={title} className="rounded-lg border border-gray-200 bg-white p-5">
            <p className="font-semibold text-gray-900">{title}</p>
            <p className="mt-1 text-sm text-gray-500">{desc}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
