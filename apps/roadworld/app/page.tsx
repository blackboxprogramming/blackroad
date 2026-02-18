const feed = [
  { id: 1, user: 'Alexa', avatar: '🧑‍💻', action: 'completed a 500mi road trip', portal: 'Roadbook', time: '2h ago' },
  { id: 2, user: 'Marcus', avatar: '🚐', action: 'shared a new route', portal: 'Roadview', time: '4h ago' },
  { id: 3, user: 'Luna', avatar: '📸', action: 'published a travel guide', portal: 'Lucidia', time: '6h ago' },
  { id: 4, user: 'Dev Collective', avatar: '⚡', action: 'released Roadcode v2.0', portal: 'Roadcode', time: '1d ago' },
]

export default function Roadworld() {
  return (
    <div className="min-h-screen bg-black text-white p-6">
      <h1 className="text-3xl font-bold mb-2"><span className="text-pink-400">Road</span>world</h1>
      <p className="text-gray-400 mb-6">The pulse of the community</p>

      <div className="max-w-2xl space-y-4">
        {feed.map(item => (
          <div key={item.id} className="p-4 bg-gray-900 rounded-xl border border-gray-800">
            <div className="flex items-center gap-3">
              <span className="text-2xl">{item.avatar}</span>
              <div className="flex-1">
                <p><span className="font-semibold">{item.user}</span> {item.action}</p>
                <p className="text-sm text-gray-400">via {item.portal} • {item.time}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
