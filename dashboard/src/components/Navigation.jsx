import { Link } from 'react-router-dom'
import { BarChart3, TrendingUp, CreditCard, Settings } from 'lucide-react'

export default function Navigation() {
  const items = [
    { path: '/', label: 'Dashboard', icon: BarChart3 },
    { path: '/analytics', label: 'Analytics', icon: TrendingUp },
    { path: '/billing', label: 'Billing', icon: CreditCard },
    { path: '/settings', label: 'Settings', icon: Settings }
  ]

  return (
    <nav className="w-64 bg-gradient-to-b from-blue-600 to-purple-600 text-white shadow-lg">
      <div className="p-6">
        <h1 className="text-2xl font-bold">BlackRoad</h1>
        <p className="text-blue-100">Analytics</p>
      </div>
      
      <ul className="mt-8">
        {items.map(({ path, label, icon: Icon }) => (
          <li key={path}>
            <Link
              to={path}
              className="flex items-center gap-3 px-6 py-3 hover:bg-white/10 transition"
            >
              <Icon size={20} />
              {label}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  )
}
