'use client'
import { useState } from 'react'

export default function Roadie() {
  const [messages, setMessages] = useState([
    { role: 'assistant', text: "Hey! I'm Roadie, your travel companion. Where are we heading today?" }
  ])
  const [input, setInput] = useState('')

  const send = () => {
    if (!input.trim()) return
    setMessages(m => [...m, { role: 'user', text: input }, { role: 'assistant', text: "Sounds great! Let me check the routes and weather for you..." }])
    setInput('')
  }

  return (
    <div className="min-h-screen bg-black text-white flex flex-col">
      <header className="p-4 border-b border-gray-800 text-center">
        <h1 className="text-2xl font-bold"><span className="text-green-400">Roadie</span></h1>
        <p className="text-gray-400 text-sm">Your AI Travel Companion</p>
      </header>

      <div className="flex-1 p-4 overflow-y-auto space-y-4">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] p-3 rounded-2xl ${m.role === 'user' ? 'bg-green-600' : 'bg-gray-800'}`}>
              {m.text}
            </div>
          </div>
        ))}
      </div>

      <div className="p-4 border-t border-gray-800">
        <div className="flex gap-2">
          <button className="p-3 bg-gray-800 rounded-full">🎤</button>
          <input 
            value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && send()}
            placeholder="Ask Roadie anything..."
            className="flex-1 bg-gray-900 border border-gray-700 rounded-full px-4"
          />
          <button onClick={send} className="p-3 bg-green-500 rounded-full">→</button>
        </div>
      </div>
    </div>
  )
}
