export default function StatCard({ label, value, subtext }) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-gray-600 text-sm font-medium">{label}</h3>
      <div className="mt-2 text-3xl font-bold text-gray-900">{value}</div>
      <p className="mt-2 text-xs text-gray-500">{subtext}</p>
    </div>
  )
}
