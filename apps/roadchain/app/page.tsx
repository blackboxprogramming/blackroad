const blocks = [
  { height: 12847, hash: '0x7f3a...c92b', txs: 24, time: '12s ago', validator: 'cecilia.blackroad' },
  { height: 12846, hash: '0x8b2c...a7f1', txs: 18, time: '24s ago', validator: 'lucidia.blackroad' },
  { height: 12845, hash: '0x3e9d...f4c8', txs: 31, time: '36s ago', validator: 'alice.blackroad' },
]

export default function Roadchain() {
  return (
    <div className="min-h-screen bg-black text-white p-6">
      <h1 className="text-3xl font-bold mb-2"><span className="text-violet-400">Road</span>chain</h1>
      <p className="text-gray-400 mb-6">Explore the decentralized road network</p>

      <div className="grid md:grid-cols-4 gap-4 mb-8">
        {[
          { label: 'Block Height', value: '12,847' },
          { label: 'Total Txs', value: '2.4M' },
          { label: 'Active Validators', value: '8' },
          { label: 'TPS', value: '142' },
        ].map(s => (
          <div key={s.label} className="p-4 bg-gray-900 rounded-xl">
            <p className="text-gray-400 text-sm">{s.label}</p>
            <p className="text-2xl font-bold text-violet-400">{s.value}</p>
          </div>
        ))}
      </div>

      <h3 className="text-lg font-semibold mb-3">Latest Blocks</h3>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead><tr className="text-left text-gray-400 text-sm">
            <th className="p-3">Height</th><th className="p-3">Hash</th><th className="p-3">Txs</th><th className="p-3">Time</th><th className="p-3">Validator</th>
          </tr></thead>
          <tbody>
            {blocks.map(b => (
              <tr key={b.height} className="border-t border-gray-800 hover:bg-gray-900">
                <td className="p-3 text-violet-400">{b.height}</td>
                <td className="p-3 font-mono text-sm">{b.hash}</td>
                <td className="p-3">{b.txs}</td>
                <td className="p-3 text-gray-400">{b.time}</td>
                <td className="p-3">{b.validator}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
