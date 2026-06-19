'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'

interface ExportData {
  download_url: string
  filename: string
  completion: string
  total_rows: number
}

export default function ExportPage() {
  const params = useParams()
  const router = useRouter()
  const session_id = params.id as string

  const [exportData, setExportData] = useState<ExportData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchExport = async () => {
      try {
        const res = await fetch(`/api/scan/export/${session_id}`)
        if (!res.ok) {
          const data = await res.json()
          setError(data.detail || 'Export ophalen mislukt')
          return
        }
        const data = await res.json()
        setExportData(data)
      } catch (err) {
        setError('Export kon niet worden opgehaald.')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    if (session_id) {
      fetchExport()
    }
  }, [session_id])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg-page">
        <div className="text-center">
          <div className="mb-4 text-primary text-4xl">⚙️</div>
          <p className="text-secondary">Export voorbereiden...</p>
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

  if (!exportData) return null

  return (
    <div className="min-h-screen bg-bg-page p-6">
      <div className="max-w-2xl mx-auto">
        {/* Success header */}
        <div className="text-center mb-10">
          <div className="text-6xl mb-4">✅</div>
          <h1 className="text-h1 mb-2">Export gereed</h1>
          <p className="text-secondary">Je BMS-compatible CSV is klaar voor import</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-4 mb-8">
          <div className="card text-center">
            <div className="text-3xl font-bold text-primary">{exportData.total_rows}</div>
            <p className="text-secondary text-sm">Artikelen</p>
          </div>
          <div className="card text-center">
            <div className="text-3xl font-bold text-green-600">{exportData.completion}</div>
            <p className="text-secondary text-sm">Compleetheid</p>
          </div>
        </div>

        {/* Download */}
        <div className="card mb-6">
          <h2 className="text-h2 mb-4">Bestand</h2>
          <p className="text-secondary text-sm mb-4">{exportData.filename}</p>
          <a
            href={exportData.download_url}
            download={exportData.filename}
            className="btn btn-primary w-full block text-center"
          >
            ⬇️ Download CSV
          </a>
        </div>

        {/* New scan */}
        <button
          onClick={() => router.push('/dashboard')}
          className="btn btn-secondary w-full"
        >
          Nieuwe prijslijst verwerken
        </button>
      </div>
    </div>
  )
}
