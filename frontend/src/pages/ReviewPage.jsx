import { useState, useEffect, useCallback } from 'react'
import { getRecords, approveRecord, flagRecord, rejectRecord, getReviewSummary, getTenants } from '../api/client'

const SCOPE_LABELS = { '1': 'Scope 1', '2': 'Scope 2', '3': 'Scope 3' }
const SCOPE_BADGES = { '1': 'badge-scope1', '2': 'badge-scope2', '3': 'badge-scope3' }
const STATUS_BADGES = {
  pending: 'badge-pending',
  approved: 'badge-approved',
  flagged: 'badge-flagged',
  rejected: 'badge-rejected',
}

function SummaryBar({ summary }) {
  if (!summary) return null
  const { stats, scope_breakdown } = summary

  return (
    <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
      {[
        { label: 'total', value: stats.total, color: 'text-white' },
        { label: 'pending', value: stats.pending, color: 'text-yellow-400' },
        { label: 'approved', value: stats.approved, color: 'text-green-400' },
        { label: 'flagged', value: stats.flagged, color: 'text-red-400' },
        { label: 'suspicious', value: stats.suspicious, color: 'text-orange-400' },
        {
          label: 'total CO₂e (kg)',
          value: stats.total_co2e ? Math.round(stats.total_co2e).toLocaleString() : '—',
          color: 'text-blue-300',
        },
      ].map(({ label, value, color }) => (
        <div key={label} className="bg-gray-900 border border-gray-800 rounded-lg px-4 py-3">
          <div className={`text-xl font-mono font-semibold ${color}`}>{value ?? '—'}</div>
          <div className="text-xs text-gray-500 mt-0.5">{label}</div>
        </div>
      ))}
    </div>
  )
}

function RecordRow({ record, onAction }) {
  const [comment, setComment] = useState('')
  const [showComment, setShowComment] = useState(false)
  const [pendingAction, setPendingAction] = useState(null)
  const [loading, setLoading] = useState(false)

  const doAction = async (actionFn, action) => {
    setLoading(true)
    try {
      await actionFn(record.id, comment)
      onAction(record.id, action)
    } catch (_) {}
    setLoading(false)
    setShowComment(false)
    setComment('')
    setPendingAction(null)
  }

  const locked = record.review_status === 'approved' || record.review_status === 'rejected'

  return (
    <div className={`border-b border-gray-800 hover:bg-gray-900 transition-colors ${
      record.is_suspicious ? 'border-l-2 border-l-orange-500' : ''
    }`}>
      <div className="px-4 py-3 grid grid-cols-12 gap-3 items-center text-sm">
        {/* Date */}
        <div className="col-span-2 font-mono text-gray-400 text-xs">
          {record.activity_date || '—'}
        </div>

        {/* Scope + Source */}
        <div className="col-span-1">
          <span className={SCOPE_BADGES[record.scope]}>{SCOPE_LABELS[record.scope]}</span>
        </div>

        {/* Category */}
        <div className="col-span-2 text-xs text-gray-300 truncate">
          {record.category || record.source_type}
        </div>

        {/* Quantity */}
        <div className="col-span-2 font-mono text-xs text-gray-300">
          {record.quantity != null ? (
            <>
              <span className="text-white">{record.quantity.toLocaleString(undefined, { maximumFractionDigits: 2 })}</span>
              <span className="text-gray-500 ml-1">{record.unit}</span>
            </>
          ) : '—'}
        </div>

        {/* CO2e */}
        <div className="col-span-1 font-mono text-xs">
          {record.co2e_kg != null ? (
            <span className="text-blue-300">{Math.round(record.co2e_kg).toLocaleString()} kg</span>
          ) : (
            <span className="text-gray-600">n/a</span>
          )}
        </div>

        {/* Flags */}
        <div className="col-span-1">
          {record.is_suspicious && (
            <span className="text-orange-400 text-xs" title={record.suspicion_reasons?.join('\n')}>
              ⚠ flag
            </span>
          )}
        </div>

        {/* Status */}
        <div className="col-span-1">
          <span className={STATUS_BADGES[record.review_status]}>{record.review_status}</span>
        </div>

        {/* Actions */}
        <div className="col-span-2 flex gap-1 justify-end">
          {!locked && (
            <>
              <button
                disabled={loading}
                onClick={() => doAction(approveRecord, 'approved')}
                className="px-2 py-1 bg-green-900 hover:bg-green-800 text-green-200 text-xs rounded transition-colors disabled:opacity-50"
              >
                ✓
              </button>
              <button
                disabled={loading}
                onClick={() => {
                  setPendingAction('flag')
                  setShowComment(true)
                }}
                className="px-2 py-1 bg-red-900 hover:bg-red-800 text-red-200 text-xs rounded transition-colors disabled:opacity-50"
              >
                ⚑
              </button>
            </>
          )}
        </div>
      </div>

      {/* Suspicious reasons */}
      {record.is_suspicious && record.suspicion_reasons?.length > 0 && (
        <div className="px-4 pb-2 flex flex-wrap gap-1">
          {record.suspicion_reasons.map((r, i) => (
            <span key={i} className="text-xs bg-orange-950 text-orange-300 px-2 py-0.5 rounded">
              {r}
            </span>
          ))}
        </div>
      )}

      {/* Comment box */}
      {showComment && (
        <div className="px-4 pb-3 flex gap-2 items-center">
          <input
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="reason (optional)"
            className="flex-1 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-white focus:outline-none focus:border-red-500"
          />
          <button
            onClick={() => doAction(flagRecord, 'flagged')}
            className="px-3 py-1 bg-red-800 hover:bg-red-700 text-red-100 text-xs rounded"
          >
            flag
          </button>
          <button
            onClick={() => { setShowComment(false); setPendingAction(null) }}
            className="px-2 py-1 text-gray-500 text-xs hover:text-white"
          >
            cancel
          </button>
        </div>
      )}
    </div>
  )
}

export default function ReviewPage() {
  const [records, setRecords] = useState([])
  const [summary, setSummary] = useState(null)
  const [tenants, setTenants] = useState([])
  const [filters, setFilters] = useState({
    tenant: '',
    scope: '',
    source_type: '',
    review_status: '',
    is_suspicious: '',
  })
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [count, setCount] = useState(0)
  const PAGE_SIZE = 50

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const params = { page, page_size: PAGE_SIZE }
      Object.entries(filters).forEach(([k, v]) => { if (v) params[k] = v })
      const [recRes, sumRes] = await Promise.all([
        getRecords(params),
        getReviewSummary(filters.tenant || undefined),
      ])
      setRecords(recRes.data.results || recRes.data)
      setCount(recRes.data.count || 0)
      setSummary(sumRes.data)
    } catch (_) {}
    setLoading(false)
  }, [filters, page])

  useEffect(() => {
    loadData()
  }, [loadData])

  useEffect(() => {
    getTenants()
      .then((res) => setTenants(res.data.results || res.data))
      .catch(() => {})
  }, [])

  const handleAction = (recordId, newStatus) => {
    setRecords((prev) =>
      prev.map((r) => r.id === recordId ? { ...r, review_status: newStatus } : r)
    )
    // Reload summary
    getReviewSummary(filters.tenant || undefined)
      .then((res) => setSummary(res.data))
      .catch(() => {})
  }

  const setFilter = (key, val) => {
    setFilters((prev) => ({ ...prev, [key]: val }))
    setPage(1)
  }

  return (
    <div className="max-w-7xl mx-auto space-y-5">
      <div>
        <h1 className="text-xl font-semibold text-white">Analyst Review</h1>
        <p className="text-sm text-gray-500 mt-0.5">Review normalized records before audit lock</p>
      </div>

      <SummaryBar summary={summary} />

      {/* Filters */}
      <div className="flex flex-wrap gap-2 items-center">
        <select
          value={filters.tenant}
          onChange={(e) => setFilter('tenant', e.target.value)}
          className="bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-xs text-white focus:outline-none focus:border-green-500"
        >
          <option value="">all tenants</option>
          {tenants.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
        </select>

        {[
          { key: 'scope', options: [['', 'all scopes'], ['1', 'Scope 1'], ['2', 'Scope 2'], ['3', 'Scope 3']] },
          { key: 'source_type', options: [['', 'all sources'], ['sap', 'SAP'], ['utility', 'Utility'], ['travel', 'Travel']] },
          { key: 'review_status', options: [['', 'all status'], ['pending', 'Pending'], ['approved', 'Approved'], ['flagged', 'Flagged'], ['rejected', 'Rejected']] },
          { key: 'is_suspicious', options: [['', 'all'], ['true', 'suspicious only']] },
        ].map(({ key, options }) => (
          <select
            key={key}
            value={filters[key]}
            onChange={(e) => setFilter(key, e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-xs text-white focus:outline-none focus:border-green-500"
          >
            {options.map(([val, label]) => <option key={val} value={val}>{label}</option>)}
          </select>
        ))}

        <span className="text-xs text-gray-500 ml-auto font-mono">{count} records</span>
      </div>

      {/* Table */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
        {/* Header */}
        <div className="px-4 py-2 grid grid-cols-12 gap-3 text-xs text-gray-500 border-b border-gray-800 bg-gray-950">
          <div className="col-span-2">date</div>
          <div className="col-span-1">scope</div>
          <div className="col-span-2">category</div>
          <div className="col-span-2">quantity</div>
          <div className="col-span-1">CO₂e</div>
          <div className="col-span-1">flags</div>
          <div className="col-span-1">status</div>
          <div className="col-span-2 text-right">actions</div>
        </div>

        {loading ? (
          <div className="py-12 text-center text-gray-500 text-sm font-mono animate-pulse">
            loading records...
          </div>
        ) : records.length === 0 ? (
          <div className="py-12 text-center text-gray-600 text-sm">
            no records match current filters
          </div>
        ) : (
          records.map((record) => (
            <RecordRow key={record.id} record={record} onAction={handleAction} />
          ))
        )}
      </div>

      {/* Pagination */}
      {count > PAGE_SIZE && (
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>page {page} of {Math.ceil(count / PAGE_SIZE)}</span>
          <div className="flex gap-2">
            <button
              disabled={page === 1}
              onClick={() => setPage((p) => p - 1)}
              className="px-3 py-1.5 bg-gray-800 rounded disabled:opacity-30 hover:bg-gray-700 transition-colors"
            >
              ← prev
            </button>
            <button
              disabled={page >= Math.ceil(count / PAGE_SIZE)}
              onClick={() => setPage((p) => p + 1)}
              className="px-3 py-1.5 bg-gray-800 rounded disabled:opacity-30 hover:bg-gray-700 transition-colors"
            >
              next →
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
