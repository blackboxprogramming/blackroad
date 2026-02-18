import Link from 'next/link'

const guides = [
  { slug: 'getting-started', title: 'Getting Started with BlackRoad', category: 'Basics', icon: '🚀' },
  { slug: 'roadview-guide', title: 'Using Roadview for Live Maps', category: 'Portals', icon: '🗺️' },
  { slug: 'roadbook-journaling', title: 'Journey Journaling with Roadbook', category: 'Portals', icon: '📔' },
  { slug: 'radius-meetups', title: 'Finding Local Meetups', category: 'Community', icon: '📍' },
  { slug: 'roadcoin-basics', title: 'Understanding Roadcoin', category: 'Tokens', icon: '🪙' },
  { slug: 'api-integration', title: 'API Integration Guide', category: 'Developers', icon: '⚡' },
]

const categories = [...new Set(guides.map(g => g.category))]

export default function Lucidia() {
  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-gray-800 p-6">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">
              <span className="text-[#9C27B0]">Lucidia</span>
            </h1>
            <p className="text-gray-400">Knowledge flows here</p>
          </div>
          <div className="flex gap-4">
            <input 
              type="search" 
              placeholder="Search guides..."
              className="bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 w-64 focus:border-violet-500 outline-none"
            />
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-6xl mx-auto p-6">
        {/* Categories */}
        <div className="flex gap-2 mb-8 flex-wrap">
          <button className="px-4 py-2 bg-violet-600 rounded-full text-sm">All</button>
          {categories.map(cat => (
            <button key={cat} className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-full text-sm">
              {cat}
            </button>
          ))}
        </div>

        {/* Guide grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {guides.map(guide => (
            <Link 
              key={guide.slug}
              href={`/guides/${guide.slug}`}
              className="block p-6 bg-gray-900 rounded-xl border border-gray-800 hover:border-violet-500 transition-colors"
            >
              <div className="text-3xl mb-3">{guide.icon}</div>
              <h2 className="text-lg font-semibold mb-2">{guide.title}</h2>
              <span className="text-sm text-violet-400">{guide.category}</span>
            </Link>
          ))}
        </div>

        {/* Stats */}
        <div className="mt-12 grid grid-cols-3 gap-4 text-center">
          <div className="p-6 bg-gray-900 rounded-xl">
            <div className="text-3xl font-bold text-violet-400">24</div>
            <div className="text-gray-400">Guides</div>
          </div>
          <div className="p-6 bg-gray-900 rounded-xl">
            <div className="text-3xl font-bold text-amber-400">156</div>
            <div className="text-gray-400">Tips</div>
          </div>
          <div className="p-6 bg-gray-900 rounded-xl">
            <div className="text-3xl font-bold text-pink-400">1.2k</div>
            <div className="text-gray-400">Contributors</div>
          </div>
        </div>
      </main>
    </div>
  )
}
