'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'

interface GapItem {
  item_number: string
  item_name: string
  missing_fields: string[]
}

interface GapAnalysis {
  total_items: number
  complete_items: number
  missing_specs_items: number
  pricing_only_items: number
  completion_percentage: number
  gap_items: GapItem[]
}

export default function ValidationPage() {
  const params = useParams()
  const router = useRouter()
  const session_id = params.id as string

  const [gapData, setGapData] = useState<GapAnalysis | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [runningScan2, setRunningScan2] = useState(false)

  useEffect(() => {
    const fetchGapAnalysis = async () => {
      try {
        const res = await fetch(`/api/scan/gap-analysis/${session_id}`)
        if (!res.ok) {
          const data = await res.json()
          setError(data.detail || 'Gap analysis ophalen mislukt')
          return
        }
        const data = await res.json()
        setGapData(data)
      } catch (err) {
        setError('Kon gap analysis niet laden.')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    if (session_id) {
      fetchGapAnalysis()
    }
  }, [session_id])

  const handleScan2 = async () => {
    setRunningScan2(true)
    try {
      const res = await fetch(`/api/scan/scan2/${session_id}`, { method: 'POST' })
      if (!res.ok) {
        const data = await res.json()
        setError(data.detail || 'Scan 2 mislukt')
        return
      }
      router.push(`/export/${session_id}`)
    } catch (err) {
      setError('Scan 2 kon niet starten.')
      console.error(err)
    } finally {
      setRunningScan2(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg-page">
        <div className="text-center">
          <div className="mb-4 text-primary text-4xl">⏳</div>
          <p className="text-secondary">Gap analysis laden...</p>
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
            <button onClick={() => router.push('/dashboard')} className="btn btn-primary w-full">
              Terug naar upload
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (!gapData) return null

  return (
    <div className="min-h-screen bg-bg-page p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-h1">Validatie</h1>
          <p className="text-secondary">Controleer ontbrekende specificaties vóór export</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="card text-center">
            <div className="text-2xl font-bold text-primary">{gapData.total_items}</div>
            <p className="text-secondary text-sm">Totaal</p>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-green-600">{gapData.complete_items}</div>
            <p className="text-secondary text-sm">Compleet</p>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-orange-500">{gapData.missing_specs_items}</div>
            <p className="text-secondary text-sm">Specs mist</p>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-primary">{gapData.completion_percentage}%</div>
            <p className="text-secondary text-sm">Compleetheid</p>
          </div>
        </div>

        {/* Progress bar */}
        <div className="card mb-8">
          <div className="flex justify-between mb-2">
            <span className="text-sm font-bold text-primary">Compleetheid</span>
            <span className="text-sm text-secondary">{gapData.completion_percentage}%</span>
          </div>
          <div className="w-full bg-bg-light rounded-full h-3">
            <div
              className="bg-primary h-3 rounded-full transition-all"
              style={{ width: `${gapData.completion_percentage}%` }}
            />
          </div>
        </div>

        {/* Gap items */}
        {gapData.gap_items && gapData.gap_items.length > 0 && (
          <div className="card mb-8">
            <h2 className="text-h2 mb-4">Artikelen met ontbrekende specs</h2>
            <div className="space-y-3">
              {gapData.gap_items.map((item, idx) => (
                <div key={idx} className="border border-border-color rounded-lg p-3 text-sm">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-bold text-primary">{item.item_number}</p>
                      <p className="text-secondary">{item.item_name}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-orange-500 text-xs">
                        {item.missing_fields.join(', ')}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-4">
          <button
            onClick={handleScan2}
            disabled={runningScan2}
            className="btn btn-primary flex-1"
          >
            {runningScan2 ? 'Scan 2 bezig...' : 'Scan 2 starten →'}
          </button>
          <button
            onClick={() => router.push(`/export/${session_id}`)}
            className="btn btn-secondary flex-1"
          >
            Overslaan → Export
          </button>
        </div>
      </div>
    </div>
  )
}
