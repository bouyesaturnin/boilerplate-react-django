import { useEffect, useState } from 'react'
import { User } from 'lucide-react'
import { authApi } from '../api/auth'
import { Card, CardBody, CardHeader } from '../components/ui/Card'
import Alert from '../components/ui/Alert'
import Badge from '../components/ui/Badge'
import Spinner from '../components/ui/Spinner'

export default function DashboardPage() {
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    authApi.me()
      .then(({ data }) => setProfile(data))
      .catch(() => setError('Impossible de charger le profil.'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner size="lg" />
      </div>
    )
  }

  if (error) {
    return <Alert variant="error">{error}</Alert>
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Tableau de bord</h1>
        <p className="mt-1 text-sm text-gray-500">Bienvenue, {profile.username}.</p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-gray-900">Mon profil</h2>
            <Badge variant="success">Actif</Badge>
          </div>
        </CardHeader>

        <CardBody>
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary-100">
              <User size={22} className="text-primary-600" />
            </div>
            <div>
              <p className="font-semibold text-gray-900">{profile.username}</p>
              <p className="text-sm text-gray-500">{profile.email}</p>
            </div>
          </div>

          <dl className="mt-6 grid grid-cols-1 gap-4 text-sm sm:grid-cols-3">
            <div className="rounded-md bg-gray-50 px-4 py-3">
              <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Prénom</dt>
              <dd className="mt-1 font-medium text-gray-900">{profile.first_name || '—'}</dd>
            </div>
            <div className="rounded-md bg-gray-50 px-4 py-3">
              <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Nom</dt>
              <dd className="mt-1 font-medium text-gray-900">{profile.last_name || '—'}</dd>
            </div>
            <div className="rounded-md bg-gray-50 px-4 py-3">
              <dt className="text-xs font-medium uppercase tracking-wide text-gray-500">Membre depuis</dt>
              <dd className="mt-1 font-medium text-gray-900">
                {new Date(profile.date_joined).toLocaleDateString('fr-FR')}
              </dd>
            </div>
          </dl>
        </CardBody>
      </Card>
    </div>
  )
}
