import { useState, useEffect, useRef } from 'react'
import { getTenants, uploadFile, getBatches } from '../api/client'

const SOURCE_CONFIGS = {
  sap: {
    label: 'SAP Export',
    sublabel: 'Fuel & Procurement (CSV/TXT)',
    description: 'Flat file export from SAP SE16/SE16N. Accepts semicolon or comma delimited. German headers OK.',
    accept: '.csv,.txt,.tsv',
    color: 'border-orange-700 hover:border-orange-500',
    badge: 'badge-scope1',
    badgeText: 'Scope 1',
  },
  utility: {
    label: 'Utility Data',
    sublabel: 'Electricity Portal CSV',
    description: 'Portal export from utility provider. Needs meter ID, billing period, and consumption in kWh or units.',
    accept: '.csv',
    color: 'border-blue-700 hover:border-blue-500',
    badge: 'badge-scope2',
    badgeText: 'Scope 2',
  },
  travel: {
    label: 'Corporate Travel',
    sublabel: 'Concur / Navan Export (CSV)',
    description: 'Standard accounting extract from Concur or Navan. Needs expense type, dates, origin/destination.',
    accept: '.csv',
    color: 'border-purple-700 hover:border-purple-500',
    badge: 'badge-scope3',
    badgeText: 'Scope 3',
  },
}

function UploadZone({ sourceType, tenantId, onSuccess }) {
  const cfg = SOURCE_CONFIGS[sourceType]
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const inputRef = useRef()

  const handleFile = async (file) => {
    if (!tenantId) {
      setError('Select a tenant first')
      return
    }
    setUploading(true)
    setError('')
    setResult(null)
    const formData = new FormData()
    formData.append('file', file)
    formData.append('source_type', sourceType)
    formData.append('tenant_id', tenantId)
    try {
      const res = await uploadFile(formData)
      setResult(res.data)
      onSuccess?.()
    } catch (err) {
      setError(err.response?.data?.error || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const onDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2 mb-0.5">
            <span className="font-medium text-white">{cfg.label}</span>
            <span className={cfg.badge}>{cfg.badgeText}</span>
          </div>
          <div className="text-xs text-gray-400">{cfg.sublabel}</div>
        </div>
      </div>

      <p className="text-xs text-gray-500 mb-3">{cfg.description}</p>

      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
          dragging ? 'border-green-500 bg-green-950' : cfg.color + ' bg-gray-800'
        }`}
      >
        {uploading ? (
          <div className="text-sm text-gray-400 font-mono animate-pulse">processing...</div>
        ) : (
          <>
            <div className="text-2xl mb-1">↑</div>
            <div className="text-sm text-gray-400">drop file or <span className="text-white underline">browse</span></div>
            <div className="text-xs text-gray-600 mt-1">{cfg.accept}</div>
          </>
        )}
        <input
          ref={inputRef}
          type="file"
          accept={cfg.accept}
          className="hidden"
          onChange={(e) => e.target.files[0] && handleFile(e.target.files[0])}
        />
      </div>

      {/* Result */}
      {result && (
        <div className="mt-3 bg-gray-800 rounded p-3 text-xs font-mono">
          <div className="text-green-400 mb-1">✓ {result.file_name}</div>
          <div className="text-gray-400 flex gap-4">
            <span>total: <span className="text-white">{result.total_rows}</span></span>
            <span>parsed: <span className="text-green-300">{result.parsed_rows}</span></span>
            {result.failed_rows > 0 && (
              <span>failed: <span className="text-red-300">{result.failed_rows}</span></span>
            )}
          </div>
        </div>
      )}

      {error && (
        <div className="mt-3 bg-red-950 border border-red-800 rounded px-3 py-2 text-red-300 text-xs">
          {error}
        </div>
      )}
    </div>
  )
}

function BatchHistory({ batches }) {
  if (!batches.length) return null

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-800 text-xs font-mono text-gray-400">
        recent uploads
      </div>
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-gray-800 text-gray-500">
            <th className="px-4 py-2 text-left">file</th>
            <th className="px-4 py-2 text-left">source</th>
            <th className="px-4 py-2 text-left">status</th>
            <th className="px-4 py-2 text-right">rows</th>
            <th className="px-4 py-2 text-right">failed</th>
            <th className="px-4 py-2 text-right">uploaded</th>
          </tr>
        </thead>
        <tbody>
          {batches.map((b) => (
            <tr key={b.id} className="border-b border-gray-800 hover:bg-gray-800 transition-colors">
              <td className="px-4 py-2 font-mono text-gray-300 max-w-48 truncate">{b.file_name}</td>
              <td className="px-4 py-2">
                <span className={`badge-scope${b.source_type === 'sap' ? '1' : b.source_type === 'utility' ? '2' : '3'}`}>
                  {b.source_type}
                </span>
              </td>
              <td className="px-4 py-2">
                <span className={b.status === 'done' ? 'text-green-400' : b.status === 'failed' ? 'text-red-400' : 'text-yellow-400'}>
                  {b.status}
                </span>
              </td>
              <td className="px-4 py-2 text-right text-gray-400">{b.parsed_rows}</td>
              <td className="px-4 py-2 text-right text-red-400">{b.failed_rows > 0 ? b.failed_rows : '—'}</td>
              <td className="px-4 py-2 text-right text-gray-500">
                {new Date(b.uploaded_at).toLocaleString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function UploadPage() {
  const [tenants, setTenants] = useState([])
  const [selectedTenant, setSelectedTenant] = useState('')
  const [batches, setBatches] = useState([])

  const loadBatches = () => {
    getBatches({ ordering: '-uploaded_at', page_size: 10 })
      .then((res) => setBatches(res.data.results || res.data))
      .catch(() => {})
  }

  useEffect(() => {
    getTenants().then((res) => {
      const list = res.data.results || res.data
      setTenants(list)
      if (list.length > 0) setSelectedTenant(list[0].id)
    }).catch(() => {})
    loadBatches()
  }, [])

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-white">Data Ingestion</h1>
          <p className="text-sm text-gray-500 mt-0.5">Upload source data for normalization and review</p>
        </div>

        <div>
          <label className="text-xs text-gray-400 mr-2 font-mono">tenant</label>
          <select
            value={selectedTenant}
            onChange={(e) => setSelectedTenant(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm text-white focus:outline-none focus:border-green-500"
          >
            {tenants.map((t) => (
              <option key={t.id} value={t.id}>{t.name}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {['sap', 'utility', 'travel'].map((src) => (
          <UploadZone
            key={src}
            sourceType={src}
            tenantId={selectedTenant}
            onSuccess={loadBatches}
          />
        ))}
      </div>

      <BatchHistory batches={batches} />
    </div>
  )
}
