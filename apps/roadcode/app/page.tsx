'use client'
import { useState } from 'react'

export default function Roadcode() {
  const [code, setCode] = useState('// Welcome to Roadcode\nconsole.log("Hello, BlackRoad!");')
  const [output, setOutput] = useState('')

  const runCode = () => {
    try {
      const logs: string[] = []
      const mockConsole = { log: (...args: any[]) => logs.push(args.join(' ')) }
      new Function('console', code)(mockConsole)
      setOutput(logs.join('\n') || 'No output')
    } catch (e: any) {
      setOutput(`Error: ${e.message}`)
    }
  }

  return (
    <div className="min-h-screen bg-black text-white p-6">
      <h1 className="text-2xl font-bold mb-4"><span className="text-amber-400">Road</span>code</h1>
      <div className="grid lg:grid-cols-2 gap-4">
        <div>
          <textarea 
            value={code} 
            onChange={e => setCode(e.target.value)}
            className="w-full h-96 bg-gray-900 p-4 font-mono text-sm rounded-lg border border-gray-700"
          />
          <button onClick={runCode} className="mt-2 px-4 py-2 bg-amber-500 text-black font-semibold rounded-lg">
            Run Code
          </button>
        </div>
        <div className="bg-gray-900 p-4 rounded-lg border border-gray-700 h-96 overflow-auto">
          <pre className="text-green-400 font-mono text-sm">{output || 'Output will appear here...'}</pre>
        </div>
      </div>
    </div>
  )
}
