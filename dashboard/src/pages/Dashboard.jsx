import { useEffect, useState } from 'react'
import StatCard from '../components/StatCard'
import Chart from '../components/Chart'
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export default function Dashboard({ user }) {
  const [stats, setStats] = useState({
    requests: 12500,
    revenue: 250,
    users: 5,
    tier: 'Light'
  })

  const [chartData, setChartData] = useState([
    { day: 'Mon', requests: 1200 },
    { day: 'Tue', requests: 1900 },
    { day: 'Wed', requests: 1500 },
    { day: 'Thu', requests: 2100 },
    { day: 'Fri', requests: 1800 },
    { day: 'Sat', requests: 900 },
    { day: 'Sun', requests: 1100 }
  ])

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Dashboard</h1>
      
      {/* Stats Grid */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <StatCard label="This Month" value={`${stats.requests.toLocaleString()}`} subtext="Requests" />
        <StatCard label="Revenue" value={`$${stats.revenue}`} subtext="USD" />
        <StatCard label="Subscription" value={stats.tier} subtext="Current plan" />
        <StatCard label="Active Users" value={stats.users} subtext="Concurrent" />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-2 gap-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Usage Trend</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="requests" stroke="#667eea" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Daily Breakdown</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="requests" fill="#764ba2" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
