import { useState } from 'react'
import { CreditCard, Download, AlertCircle } from 'lucide-react'

export default function Billing() {
  const [activeTab, setActiveTab] = useState('current')

  const currentPlan = {
    name: 'Light',
    price: 25,
    next_billing_date: '2026-06-04',
    status: 'active'
  }

  const invoices = [
    { id: 'INV-001', date: '2026-04-04', amount: 25, status: 'paid' },
    { id: 'INV-002', date: '2026-03-04', amount: 22.50, status: 'paid' },
    { id: 'INV-003', date: '2026-02-04', amount: 18.75, status: 'paid' }
  ]

  const usage = {
    requests_this_month: 12500,
    included_requests: 50000,
    overage_cost: 0,
    forecast_total: 25.00
  }

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Billing</h1>

      {/* Current Plan */}
      <div className="grid grid-cols-2 gap-8 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Current Plan</h2>
          <div className="space-y-4">
            <div>
              <p className="text-gray-600 text-sm">Plan Name</p>
              <p className="text-2xl font-bold">{currentPlan.name}</p>
            </div>
            <div>
              <p className="text-gray-600 text-sm">Monthly Price</p>
              <p className="text-2xl font-bold">${currentPlan.price}</p>
            </div>
            <div>
              <p className="text-gray-600 text-sm">Next Billing Date</p>
              <p className="text-lg font-semibold">{new Date(currentPlan.next_billing_date).toLocaleDateString()}</p>
            </div>
            <div className="flex gap-2 pt-4">
              <button className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                Upgrade Plan
              </button>
              <button className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
                Cancel
              </button>
            </div>
          </div>
        </div>

        {/* Usage & Forecast */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Usage & Forecast</h2>
          <div className="space-y-4">
            <div>
              <p className="text-gray-600 text-sm">Requests This Month</p>
              <p className="text-2xl font-bold">{usage.requests_this_month.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-gray-600 text-sm">Included (Light Plan)</p>
              <p className="text-lg">{usage.included_requests.toLocaleString()} requests</p>
            </div>
            <div className="bg-blue-50 border border-blue-200 rounded p-3 flex gap-2">
              <AlertCircle size={20} className="text-blue-600" />
              <div className="text-sm">
                <p className="font-semibold">Good news!</p>
                <p>You're well within your monthly limit.</p>
              </div>
            </div>
            <div className="pt-4 border-t">
              <p className="text-gray-600 text-sm">Estimated This Month</p>
              <p className="text-2xl font-bold">${usage.forecast_total.toFixed(2)}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b flex">
          {[
            { id: 'current', label: 'Current Month' },
            { id: 'invoices', label: 'Invoice History' },
            { id: 'payments', label: 'Payment Methods' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-6 py-4 font-semibold border-b-2 transition ${
                activeTab === tab.id 
                  ? 'border-blue-600 text-blue-600' 
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="p-6">
          {activeTab === 'current' && (
            <div className="space-y-4">
              <div className="flex justify-between items-center pb-4 border-b">
                <div>
                  <h3 className="font-semibold">Light Plan</h3>
                  <p className="text-sm text-gray-600">Monthly subscription</p>
                </div>
                <span className="text-lg font-bold">$25.00</span>
              </div>
              <div className="text-center pt-4">
                <p className="text-gray-600">Next invoice will be generated on {new Date(currentPlan.next_billing_date).toLocaleDateString()}</p>
              </div>
            </div>
          )}

          {activeTab === 'invoices' && (
            <div className="space-y-2">
              {invoices.map(invoice => (
                <div key={invoice.id} className="flex items-center justify-between p-4 border rounded hover:bg-gray-50">
                  <div>
                    <p className="font-semibold">{invoice.id}</p>
                    <p className="text-sm text-gray-600">{new Date(invoice.date).toLocaleDateString()}</p>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-lg font-bold">${invoice.amount.toFixed(2)}</span>
                    <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-semibold">
                      {invoice.status}
                    </span>
                    <button className="p-2 hover:bg-gray-200 rounded">
                      <Download size={18} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'payments' && (
            <div className="space-y-4">
              <div className="flex items-center gap-4 p-4 border rounded">
                <CreditCard size={32} className="text-gray-400" />
                <div className="flex-1">
                  <p className="font-semibold">Visa ending in 4242</p>
                  <p className="text-sm text-gray-600">Expires 12/2025</p>
                </div>
                <button className="px-4 py-2 text-red-600 hover:bg-red-50 rounded">Remove</button>
              </div>
              <button className="w-full px-4 py-2 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 text-blue-600 font-semibold">
                + Add Payment Method
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
