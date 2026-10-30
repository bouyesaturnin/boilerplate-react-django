import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../features/auth/AuthContext'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'
import Alert from '../components/ui/Alert'
import { Card, CardBody, CardHeader } from '../components/ui/Card'

export default function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', username: '', password: '' })
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)

  function handleChange(e) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }))
  }

  function firstError(field) {
    const msg = errors[field]
    if (!msg) return undefined
    return Array.isArray(msg) ? msg[0] : msg
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setErrors({})
    setLoading(true)
    try {
      await register(form)
      navigate('/dashboard')
    } catch (err) {
      setErrors(err.response?.data || { non_field_errors: ['Une erreur est survenue.'] })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto mt-16 max-w-sm">
      <Card>
        <CardHeader>
          <h1 className="text-xl font-semibold text-gray-900">Créer un compte</h1>
          <p className="mt-1 text-sm text-gray-500">
            Déjà un compte ?{' '}
            <Link to="/login" className="font-medium text-primary-600 hover:text-primary-500">
              Se connecter
            </Link>
          </p>
        </CardHeader>

        <CardBody>
          <form onSubmit={handleSubmit} className="space-y-4">
            {errors.non_field_errors && (
              <Alert variant="error">{errors.non_field_errors[0]}</Alert>
            )}

            <Input
              id="email"
              name="email"
              type="email"
              label="Email"
              autoComplete="email"
              required
              value={form.email}
              onChange={handleChange}
              error={firstError('email')}
            />

            <Input
              id="username"
              name="username"
              type="text"
              label="Nom d'utilisateur"
              autoComplete="username"
              required
              value={form.username}
              onChange={handleChange}
              error={firstError('username')}
            />

            <Input
              id="password"
              name="password"
              type="password"
              label="Mot de passe"
              autoComplete="new-password"
              required
              minLength={8}
              value={form.password}
              onChange={handleChange}
              error={firstError('password')}
              helper="Minimum 8 caractères"
            />

            <Button type="submit" loading={loading} className="w-full">
              Créer mon compte
            </Button>
          </form>
        </CardBody>
      </Card>
    </div>
  )
}
