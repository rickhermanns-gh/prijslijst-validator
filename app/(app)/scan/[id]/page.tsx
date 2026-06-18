'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'

interface ScanResult {
  session_id: string
  supplier: string
  file_name: string
  scan1_items: number
  scan1_completion: number
  gap_analysis: any[]
  status: string
}

export default function ScanPage() {
  const params = useParams()
  const router = useRouter()
  const session_id = params.id as string

  const [result, setResult] = useState<ScanResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const runScan = async () => {
      try {
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

        // Call Scan 1
        const res = await fetch(`${backendUrl}/api/scan/scan1/${session_id}`, {
          method: 'POST',
        })

        if (!res.ok) {
          const data = await res.json()
          setError(data.detail || 'Scan mislukt')
          return
        }

        const data = await res.json()
        setResult(data)
      } catch (err) {
        setError('Scan kon niet starten. Probeer opnieuw.')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    if (session_id) {
      runScan()
    }
  }, [session_id])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg-page">
        <div className="text-center">
          <div className="mb-4 text-primary text-4xl">⏳</div>
          <p className="text-secondary">PDF wordt gescand...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg-page px-4">
        <div className="w-full max-w-md">
          <div className="card">
            <div className="alert alert-error mb-4">{error}</div>
            <button
              onClick={() => router.push('/dashboard')}
              className="btn btn-primary w-full"
            >
              Terug naar upload
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (!result) return null

  return (
    <div className="min-h-screen bg-bg-page p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-h1">Scan-resultaten</h1>
          <p className="text-secondary">{result.supplier} • {result.file_name}</p>
        </div>

        {/* Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          <div className="card">
            <div className="text-3xl font-bold text-primary mb-2">
              {result.scan1_items}
            </div>
            <p className="text-secondary text-sm">Artikelen gedetecteerd</p>
          </div>
          <div className="card">
            <div className="text-3xl font-bold text-primary mb-2">
              {result.scan1_completion}%
            </div>
            <p className="text-secondary text-sm">Specs voltooid</p>
          </div>
        </div>

        {/* Gap Analysis */}
        {result.gap_analysis && result.gap_analysis.length > 0 && (
          <div className="card mb-8">
            <h2 className="text-h2 mb-4">Ontbrekende data</h2>
            <div className="space-y-3">
              {result.gap_analysis.slice(0, 5).map((gap, idx) => (
                <div
                  key={idx}
                  className="border border-border-color rounded-lg p-3 text-sm"
                >
                  <p className="font-bold text-primary">{gap.item_id}</p>
                  <p className="text-secondary">{gap.missing_fields.join(', ')}</p>
                </div>
              ))}
              {result.gap_analysis.length > 5 && (
                <p className="text-secondary text-sm pt-2">
                  +{result.gap_analysis.length - 5} meer ontbrekende velden...
                </p>
              )}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-4">
          <button
            onClick={() => router.push(`/validation/${session_id}`)}
            className="btn btn-primary flex-1"
          >
            Naar validatie →
          </button>
          <button
            onClick={() => router.push('/dashboard')}
            className="btn btn-secondary flex-1"
          >
            Annuleer
          </button>
        </div>
      </div>
    </div>
  )
}
