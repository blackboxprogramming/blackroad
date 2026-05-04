import { useState, useEffect } from 'react'
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ScatterChart, Scatter } from 'recharts'

export default function Analytics() {
  const [timeRange, setTimeRange] = useState('7d')
  const [metrics, setMetrics] = useState({
    avgResponseTime: 245,
    errorRate: 0.12,
    p95Latency: 890,
    throughput: 1240
  })

  // Sample data - would come from ML endpoint
  const churnRiskData = [
    { name: 'Low Risk', value: 78 },
    { name: 'Medium Risk', value: 15 },
    { name: 'High Risk', value: 7 }
  ]

  const ltvData = [
    { month: 'Jan', ltv: 450 },
    { month: 'Feb', ltv: 520 },
    { month: 'Mar', ltv: 615 },
    { month: 'Apr', ltv: 750 },
    { month: 'May', ltv: 920 }
  ]

  const cohortData = [
    { week: 'W1', retention: 100 },
    { week: 'W2', retention: 85 },
    { week: 'W3', retention: 72 },
    { week: 'W4', retention: 65 }
  ]

  const colors = ['#667eea', '#764ba2', '#f093fb']

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
        <select 
          value={timeRange} 
          onChange={(e) => setTimeRange(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg"
        >
          <option value="7d">Last 7 Days</option>
          <option value="30d">Last 30 Days</option>
          <option value="90d">Last 90 Days</option>
        </select>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-gray-600 text-sm">Avg Response Time</h3>
          <div className="text-3xl font-bold mt-2">{metrics.avgResponseTime}ms</div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-gray-600 text-sm">Error Rate</h3>
          <div className="text-3xl font-bold mt-2 text-red-600">{(metrics.errorRate * 100).toFixed(2)}%</div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-gray-600 text-sm">P95 Latency</h3>
          <div className="text-3xl font-bold mt-2">{metrics.p95Latency}ms</div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-gray-600 text-sm">Throughput</h3>
          <div className="text-3xl font-bold mt-2">{metrics.throughput} req/s</div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-2 gap-8 mb-8">
        {/* LTV Forecasting */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">12-Month LTV Forecast</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={ltvData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="ltv" stroke="#667eea" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Churn Risk Distribution */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Churn Risk Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={churnRiskData} cx="50%" cy="50%" labelLine={false} label={({ name, value }) => `${name}: ${value}%`}>
                {churnRiskData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={colors[index]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Cohort Retention */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Cohort Retention</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={cohortData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="week" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="retention" fill="#764ba2" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Segmentation Overview */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Customer Segments</h2>
          <div className="space-y-4">
            {[
              { name: 'Enterprise', count: 12, growth: '+8%' },
              { name: 'Mid-Market', count: 45, growth: '+12%' },
              { name: 'SMB', count: 143, growth: '+25%' },
              { name: 'Starter', count: 289, growth: '-3%' }
            ].map(seg => (
              <div key={seg.name} className="flex justify-between items-center pb-4 border-b">
                <div>
                  <h4 className="font-semibold">{seg.name}</h4>
                  <p className="text-sm text-gray-600">{seg.count} customers</p>
                </div>
                <span className={seg.growth.startsWith('+') ? 'text-green-600' : 'text-red-600'}>
                  {seg.growth}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
