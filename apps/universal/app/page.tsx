import Link from 'next/link'

const portals = [
  { name: 'Roadbook', desc: 'Trip journals', port: 3001, color: '#FF1D6C', icon: '📔' },
  { name: 'Roadview', desc: 'Live maps', port: 3001, color: '#FF1D6C', icon: '🗺️' },
  { name: 'Lucidia', desc: 'Knowledge base', port: 3002, color: '#9C27B0', icon: '📚' },
  { name: 'Roadcode', desc: 'Code sandbox', port: 3003, color: '#F5A623', icon: '⚡' },
  { name: 'Radius', desc: 'Local meetups', port: 3004, color: '#2979FF', icon: '📍' },
  { name: 'Roadworld', desc: 'Social feed', port: 3005, color: '#FF1D6C', icon: '🌍' },
  { name: 'Roadcoin', desc: 'Wallet', port: 3006, color: '#F5A623', icon: '🪙' },
  { name: 'Roadchain', desc: 'Explorer', port: 3007, color: '#9C27B0', icon: '⛓️' },
  { name: 'Roadie', desc: 'AI assistant', port: 3008, color: '#00E676', icon: '🤖' },
]

export default function Universal() {
  return (
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
      <header className="p-8 text-center border-b border-gray-800">
        <h1 className="text-4xl font-bold mb-2">
          <span className="bg-gradient-to-r from-amber-400 via-pink-500 to-violet-500 bg-clip-text text-transparent">
            Universal Computer
          </span>
        </h1>
        <p className="text-gray-400">All portals. One console.</p>
      </header>

      {/* Search */}
      <div className="max-w-2xl mx-auto p-6">
        <input 
          placeholder="Search across all portals..."
          className="w-full bg-gray-900 border border-gray-700 rounded-xl px-6 py-4 text-lg focus:border-pink-500 outline-none"
        />
      </div>

      {/* Portal Grid */}
      <main className="max-w-6xl mx-auto p-6">
        <div className="grid md:grid-cols-3 gap-6">
          {portals.map(p => (
            <a 
              key={p.name}
              href={`http://localhost:${p.port}`}
              className="group p-6 bg-gray-900 rounded-2xl border border-gray-800 hover:border-gray-600 transition-all"
            >
              <div className="flex items-center gap-4 mb-4">
                <span className="text-4xl">{p.icon}</span>
                <div>
                  <h2 className="text-xl font-bold" style={{color: p.color}}>{p.name}</h2>
                  <p className="text-gray-400">{p.desc}</p>
                </div>
              </div>
              <div className="text-sm text-gray-500">localhost:{p.port}</div>
            </a>
          ))}
        </div>
      </main>

      {/* Status */}
      <footer className="max-w-6xl mx-auto p-6 border-t border-gray-800 mt-12">
        <div className="flex justify-between text-sm text-gray-400">
          <span>BlackRoad OS v1.0</span>
          <span>9 Portals Connected</span>
          <span>Channel: ~/.blackroad/channel/</span>
        </div>
      </footer>
    </div>
  )
}
