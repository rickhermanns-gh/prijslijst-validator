'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

const SUPPLIERS = ['ZR', 'Eijffinger', 'Artex', 'Andere']

export default function DashboardPage() {
  const router = useRouter()
  const [supplier, setSupplier] = useState('ZR')
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      const selectedFile = files[0]
      if (selectedFile.type === 'application/pdf') {
        setFile(selectedFile)
        setError('')
      } else {
        setError('Alleen PDF-bestanden zijn toegestaan')
        setFile(null)
      }
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!file) {
      setError('Selecteer een PDF-bestand')
      return
    }

    if (!supplier) {
      setError('Selecteer een leverancier')
      return
    }

    setLoading(true)

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('supplier', supplier)

      const res = await fetch(`/api/upload`, {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        const data = await res.json()
        setError(data.detail || 'Upload mislukt')
        return
      }

      const data = await res.json()
      router.push(`/scan/${data.session_id}`)
    } catch (err) {
      setError('Upload mislukt. Probeer opnieuw.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-bg-light to-bg-page">
      {/* Header */}
      <div className="bg-primary text-white py-8">
        <div className="container">
          <h1 className="text-display text-white mb-2">Prijslijst Validator</h1>
          <p className="text-lg opacity-90">Zet je PDF om naar 100% complete specs</p>
        </div>
      </div>

      {/* Content */}
      <div className="container py-12">
        <div className="max-w-2xl mx-auto">
          <div className="card">
            <h2>Nieuw project</h2>

            <form onSubmit={handleSubmit}>
              {error && (
                <div className="alert alert-error mb-6">
                  {error}
                </div>
              )}

              {/* Supplier selection */}
              <div className="form-group">
                <label htmlFor="supplier">Leverancier</label>
                <select
                  id="supplier"
                  value={supplier}
                  onChange={(e) => setSupplier(e.target.value)}
                  disabled={loading}
                >
                  {SUPPLIERS.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>

              {/* File upload */}
              <div className="form-group">
                <label>PDF-bestand</label>
                <div className="border-2 border-dashed border-border-color rounded-lg p-8 text-center hover:bg-bg-light transition">
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={handleFileChange}
                    disabled={loading}
                    className="hidden"
                    id="file-input"
                  />
                  <label
                    htmlFor="file-input"
                    className="cursor-pointer block"
                  >
                    {file ? (
                      <div>
                        <p className="font-bold text-primary">{file.name}</p>
                        <p className="text-secondary text-sm mt-1">
                          {(file.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                    ) : (
                      <div>
                        <p className="text-lg font-bold text-primary mb-2">
                          📄 Selecteer PDF
                        </p>
                        <p className="text-secondary text-sm">
                          Sleep en drop of klik om te bladeren
                        </p>
                      </div>
                    )}
                  </label>
                </div>
              </div>

              {/* Submit */}
              <button
                type="submit"
                disabled={loading || !file}
                className="btn btn-primary w-full mt-6"
              >
                {loading ? 'Uploaden...' : 'Scan starten'}
              </button>
            </form>

            {/* Info */}
            <div className="mt-8 pt-8 border-t border-border-color">
              <h3>Hoe werkt dit?</h3>
              <ol className="mt-4 space-y-3 text-sm">
                <li><strong>1. Upload</strong> — PDF van je leverancier</li>
                <li><strong>2. Scan 1</strong> — Automatische extraction van prijzen & specs</li>
                <li><strong>3. Gap Analysis</strong> — Zie wat ontbreekt</li>
                <li><strong>4. Scan 2</strong> — Geavanceerde patroonherkenning</li>
                <li><strong>5. Validatie</strong> — Vul ontbrekende specs in</li>
                <li><strong>6. Export</strong> — 100% complete CSV</li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
