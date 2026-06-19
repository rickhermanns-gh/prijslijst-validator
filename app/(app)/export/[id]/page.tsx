'use client'

import { useParams, useRouter } from 'next/navigation'

export default function ExportPage() {
  const params = useParams()
  const router = useRouter()
  const session_id = params.id as string

  return (
    <div className="min-h-screen bg-bg-page p-6">
      <div className="max-w-2xl mx-auto">
        <div className="text-center mb-10">
          <div className="text-6xl mb-4">✅</div>
          <h1 className="text-h1 mb-2">Export gereed</h1>
          <p className="text-secondary">Je BMS-compatible CSV is klaar voor import</p>
        </div>

        <div className="card mb-6">
          <h2 className="text-h2 mb-4">Download CSV</h2>
          <p className="text-secondary text-sm mb-6">
            Klik op de knop om de volledige prijslijst als CSV te downloaden.
            Het bestand bevat alle artikelen met specs, prijzen en samenstellingen.
          </p>
          <a
            href={`/api/scan/export/${session_id}`}
            className="btn btn-primary w-full block text-center"
          >
            ⬇️ Download CSV
          </a>
        </div>

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
