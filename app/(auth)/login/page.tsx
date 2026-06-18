'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

export default function LoginPage() {
  const router = useRouter()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [agreeTerms, setAgreeTerms] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!agreeTerms) {
      setError('Je moet akkoord gaan met de voorwaarden')
      return
    }

    if (!username || !password) {
      setError('Vul username en wachtwoord in')
      return
    }

    setLoading(true)

    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
      const res = await fetch(`${backendUrl}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })

      if (!res.ok) {
        const data = await res.json()
        setError(data.detail || 'Inloggen mislukt')
        return
      }

      router.push('/dashboard')
    } catch (err) {
      setError('Er ging iets mis. Probeer opnieuw.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-bg-page px-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="mb-8 text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-primary rounded-lg flex items-center justify-center">
            <span className="text-3xl text-white font-bold">Z</span>
          </div>
          <h1 className="text-h1">Prijslijst Validator</h1>
          <p className="text-secondary mt-2">Inloggen om te starten</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="card">
          {error && (
            <div className="alert alert-error mb-4">
              {error}
            </div>
          )}

          {/* Microsoft SSO (placeholder) */}
          <button
            type="button"
            disabled
            className="w-full btn btn-secondary mb-2 opacity-50 cursor-not-allowed"
          >
            🔒 Inloggen met Microsoft
          </button>

          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-border-color"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-secondary">of</span>
            </div>
          </div>

          {/* Username */}
          <div className="form-group">
            <label htmlFor="username">Gebruikersnaam</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="je_gebruikersnaam"
              disabled={loading}
            />
          </div>

          {/* Password */}
          <div className="form-group">
            <label htmlFor="password">Wachtwoord</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              disabled={loading}
            />
          </div>

          {/* Terms checkbox */}
          <div className="form-group flex items-start gap-3">
            <input
              id="terms"
              type="checkbox"
              checked={agreeTerms}
              onChange={(e) => setAgreeTerms(e.target.checked)}
              disabled={loading}
              className="mt-1 w-4 h-4 cursor-pointer"
              required
            />
            <label htmlFor="terms" className="cursor-pointer text-sm">
              Ik begrijp dat het gebruik van dit systeem voor eigen risico is.
              AI-gegenereerde informatie kan onnauwkeurigheden bevatten en dient ter
              ondersteuning, niet ter vervanging van eigen oordeel.
            </label>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            className="btn btn-primary w-full mt-6"
          >
            {loading ? 'Even geduld...' : 'Inloggen'}
          </button>
        </form>

        {/* Footer */}
        <p className="text-center text-sm text-secondary mt-6">
          Gebouwd door ai-werkers
        </p>
      </div>
    </div>
  )
}
