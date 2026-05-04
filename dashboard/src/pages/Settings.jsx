import { useState } from 'react'
import { Save, Copy } from 'lucide-react'

export default function Settings() {
  const [copied, setCopied] = useState(null)

  const apiKeys = [
    { id: 'pk_live_123...', name: 'Production Key', created: '2026-01-15', last_used: '2 hours ago' },
    { id: 'pk_test_456...', name: 'Test Key', created: '2025-12-20', last_used: '3 days ago' }
  ]

  const handleCopy = (text, id) => {
    navigator.clipboard.writeText(text)
    setCopied(id)
    setTimeout(() => setCopied(null), 2000)
  }

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Settings</h1>

      {/* Organization Settings */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-lg font-semibold mb-6">Organization</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-semibold mb-2">Organization Name</label>
            <input type="text" defaultValue="Acme Corp" className="w-full px-4 py-2 border border-gray-300 rounded-lg" />
          </div>
          <div>
            <label className="block text-sm font-semibold mb-2">Email</label>
            <input type="email" defaultValue="admin@acmecorp.com" className="w-full px-4 py-2 border border-gray-300 rounded-lg" />
          </div>
          <div className="flex gap-2 pt-4">
            <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              <Save size={18} /> Save Changes
            </button>
          </div>
        </div>
      </div>

      {/* API Keys */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-lg font-semibold mb-6">API Keys</h2>
        <div className="space-y-4">
          {apiKeys.map(key => (
            <div key={key.id} className="flex items-center justify-between p-4 border rounded-lg">
              <div className="flex-1">
                <p className="font-semibold">{key.name}</p>
                <p className="text-sm text-gray-600">Created {key.created} • Last used {key.last_used}</p>
              </div>
              <div className="flex items-center gap-2">
                <code className="px-3 py-1 bg-gray-100 rounded font-mono text-sm">{key.id}</code>
                <button
                  onClick={() => handleCopy(key.id, key.id)}
                  className="p-2 hover:bg-gray-100 rounded"
                >
                  {copied === key.id ? '✓' : <Copy size={18} />}
                </button>
              </div>
            </div>
          ))}
          <button className="w-full px-4 py-2 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 text-blue-600 font-semibold">
            + Generate New Key
          </button>
        </div>
      </div>

      {/* Webhooks */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-6">Webhooks</h2>
        <div className="space-y-4">
          <div className="p-4 border rounded-lg">
            <div className="flex justify-between items-start mb-2">
              <h3 className="font-semibold">https://webhook.acmecorp.com/stripe</h3>
              <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-semibold">active</span>
            </div>
            <p className="text-sm text-gray-600 mb-3">Events: payment_intent.succeeded, charge.dispute.created</p>
            <div className="flex gap-2">
              <button className="px-3 py-1 text-sm bg-gray-100 rounded hover:bg-gray-200">Edit</button>
              <button className="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded">Delete</button>
            </div>
          </div>
          <button className="w-full px-4 py-2 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 text-blue-600 font-semibold">
            + Add Webhook Endpoint
          </button>
        </div>
      </div>
    </div>
  )
}
