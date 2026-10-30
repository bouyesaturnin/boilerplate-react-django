import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../features/auth/AuthContext'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'
import Alert from '../components/ui/Alert'
import { Card, CardBody, CardHeader } from '../components/ui/Card'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  function handleChange(e) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(form)
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Identifiants incorrects.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto mt-16 max-w-sm">
      <Card>
        <CardHeader>
          <h1 className="text-xl font-semibold text-gray-900">Connexion</h1>
          <p className="mt-1 text-sm text-gray-500">
            Pas encore de compte ?{' '}
            <Link to="/register" className="font-medium text-primary-600 hover:text-primary-500">
              S'inscrire
            </Link>
          </p>
        </CardHeader>

        <CardBody>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && <Alert variant="error">{error}</Alert>}

            <Input
              id="email"
              name="email"
              type="email"
              label="Email"
              autoComplete="email"
              required
              value={form.email}
              onChange={handleChange}
            />

            <Input
              id="password"
              name="password"
              type="password"
              label="Mot de passe"
              autoComplete="current-password"
              required
              value={form.password}
              onChange={handleChange}
            />

            <Button type="submit" loading={loading} className="w-full">
              Se connecter
            </Button>
          </form>
        </CardBody>
      </Card>
    </div>
  )
}
