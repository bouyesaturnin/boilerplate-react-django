import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return (
    <div className="py-24 text-center">
      <p className="text-5xl font-bold text-indigo-600">404</p>
      <h1 className="mt-4 text-2xl font-semibold text-gray-900">Page introuvable</h1>
      <p className="mt-2 text-gray-500">Cette page n'existe pas.</p>
      <Link
        to="/"
        className="mt-6 inline-block rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
      >
        Retour à l'accueil
      </Link>
    </div>
  )
}
