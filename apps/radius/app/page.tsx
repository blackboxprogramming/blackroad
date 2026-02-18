const events = [
  { id: 1, title: 'Road Trip Planning Meetup', location: 'Minneapolis, MN', distance: '2.3 mi', attendees: 12, time: 'Tomorrow, 6pm' },
  { id: 2, title: 'Photographers on the Road', location: 'St. Paul, MN', distance: '5.1 mi', attendees: 8, time: 'Sat, 2pm' },
  { id: 3, title: 'Van Life Community Gathering', location: 'Uptown, MN', distance: '3.7 mi', attendees: 24, time: 'Sun, 10am' },
]

export default function Radius() {
  return (
    <div className="min-h-screen bg-black text-white p-6">
      <h1 className="text-3xl font-bold mb-2"><span className="text-blue-400">Radius</span></h1>
      <p className="text-gray-400 mb-6">Find travelers near you</p>
      
      <div className="flex gap-2 mb-6">
        <input placeholder="Search events..." className="flex-1 bg-gray-900 border border-gray-700 rounded-lg px-4 py-2" />
        <button className="px-4 py-2 bg-blue-500 rounded-lg">Near Me</button>
      </div>

      <div className="space-y-4">
        {events.map(e => (
          <div key={e.id} className="p-4 bg-gray-900 rounded-xl border border-gray-800 hover:border-blue-500">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="font-semibold text-lg">{e.title}</h3>
                <p className="text-gray-400 text-sm">{e.location} • {e.distance}</p>
              </div>
              <span className="text-blue-400 text-sm">{e.time}</span>
            </div>
            <div className="mt-3 flex items-center gap-4">
              <span className="text-sm text-gray-400">{e.attendees} attending</span>
              <button className="text-sm text-blue-400 hover:underline">Join</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
