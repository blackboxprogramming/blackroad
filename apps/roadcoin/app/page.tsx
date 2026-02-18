export default function Roadcoin() {
  return (
    <div className="min-h-screen bg-black text-white p-6">
      <h1 className="text-3xl font-bold mb-6"><span className="text-amber-400">Road</span>coin</h1>
      
      <div className="max-w-md mx-auto">
        <div className="bg-gradient-to-br from-amber-500 to-orange-600 rounded-2xl p-6 mb-6">
          <p className="text-sm opacity-80">Total Balance</p>
          <p className="text-4xl font-bold">1,247.50 RC</p>
          <p className="text-sm opacity-80 mt-2">≈ $124.75 USD</p>
        </div>

        <div className="grid grid-cols-3 gap-4 mb-6">
          <button className="p-4 bg-gray-900 rounded-xl text-center hover:bg-gray-800">
            <div className="text-2xl mb-1">↑</div><div className="text-sm">Send</div>
          </button>
          <button className="p-4 bg-gray-900 rounded-xl text-center hover:bg-gray-800">
            <div className="text-2xl mb-1">↓</div><div className="text-sm">Receive</div>
          </button>
          <button className="p-4 bg-gray-900 rounded-xl text-center hover:bg-gray-800">
            <div className="text-2xl mb-1">🔒</div><div className="text-sm">Stake</div>
          </button>
        </div>

        <h3 className="text-lg font-semibold mb-3">Recent Activity</h3>
        <div className="space-y-3">
          {[
            { type: 'Earned', amount: '+50 RC', desc: 'Trip completion bonus', time: '2h ago' },
            { type: 'Sent', amount: '-25 RC', desc: 'To @marcus', time: '1d ago' },
            { type: 'Staked', amount: '500 RC', desc: 'Earning 8% APY', time: '3d ago' },
          ].map((tx, i) => (
            <div key={i} className="flex justify-between items-center p-3 bg-gray-900 rounded-lg">
              <div><p className="font-medium">{tx.type}</p><p className="text-sm text-gray-400">{tx.desc}</p></div>
              <div className="text-right"><p className={tx.amount.startsWith('+') ? 'text-green-400' : ''}>{tx.amount}</p><p className="text-sm text-gray-400">{tx.time}</p></div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
