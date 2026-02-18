'use client'

import { useState, useEffect, useCallback } from 'react'
import Map, { Marker, Source, Layer, NavigationControl } from 'react-map-gl/maplibre'
import 'maplibre-gl/dist/maplibre-gl.css'

interface Journey {
  id: string
  user: string
  coordinates: [number, number][]
  live: boolean
  color: string
}

const COLORS = ['#FF1D6C', '#F5A623', '#2979FF', '#9C27B0', '#00E676']

export default function Roadview() {
  const [journeys, setJourneys] = useState<Journey[]>([])
  const [viewport, setViewport] = useState({
    longitude: -93.2650,
    latitude: 44.9778,
    zoom: 10
  })

  // Simulate live journey data
  useEffect(() => {
    const mockJourneys: Journey[] = [
      {
        id: '1',
        user: 'Alexa',
        coordinates: [[-93.2650, 44.9778], [-93.2750, 44.9850], [-93.2900, 44.9900]],
        live: true,
        color: COLORS[0]
      },
      {
        id: '2', 
        user: 'Traveler',
        coordinates: [[-93.1000, 44.9500], [-93.1500, 44.9600]],
        live: true,
        color: COLORS[1]
      }
    ]
    setJourneys(mockJourneys)

    // Simulate live updates
    const interval = setInterval(() => {
      setJourneys(prev => prev.map(j => {
        if (!j.live) return j
        const last = j.coordinates[j.coordinates.length - 1]
        const newCoord: [number, number] = [
          last[0] + (Math.random() - 0.5) * 0.01,
          last[1] + (Math.random() - 0.5) * 0.01
        ]
        return { ...j, coordinates: [...j.coordinates, newCoord] }
      }))
    }, 2000)

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="h-screen w-screen relative">
      {/* Header */}
      <div className="absolute top-0 left-0 right-0 z-10 p-4 bg-gradient-to-b from-black/80 to-transparent">
        <h1 className="text-2xl font-bold">
          <span className="text-[#FF1D6C]">Road</span>
          <span className="text-white">view</span>
        </h1>
        <p className="text-gray-400 text-sm">Live journey streaming</p>
      </div>

      {/* Map */}
      <Map
        {...viewport}
        onMove={evt => setViewport(evt.viewState)}
        style={{ width: '100%', height: '100%' }}
        mapStyle="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
      >
        <NavigationControl position="bottom-right" />
        
        {/* Journey lines */}
        {journeys.map(journey => (
          <Source
            key={journey.id}
            type="geojson"
            data={{
              type: 'Feature',
              properties: {},
              geometry: {
                type: 'LineString',
                coordinates: journey.coordinates
              }
            }}
          >
            <Layer
              type="line"
              paint={{
                'line-color': journey.color,
                'line-width': 3,
                'line-opacity': 0.8
              }}
            />
          </Source>
        ))}

        {/* Live markers */}
        {journeys.filter(j => j.live).map(journey => {
          const pos = journey.coordinates[journey.coordinates.length - 1]
          return (
            <Marker key={journey.id} longitude={pos[0]} latitude={pos[1]}>
              <div 
                className="marker-pulse w-4 h-4 rounded-full border-2 border-white"
                style={{ backgroundColor: journey.color }}
              />
            </Marker>
          )
        })}
      </Map>

      {/* Journey list */}
      <div className="absolute bottom-4 left-4 z-10 bg-black/80 rounded-lg p-4 min-w-[200px]">
        <h3 className="text-sm font-semibold mb-2 text-gray-400">ACTIVE JOURNEYS</h3>
        {journeys.map(j => (
          <div key={j.id} className="flex items-center gap-2 py-1">
            <div 
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: j.color }}
            />
            <span className="text-sm">{j.user}</span>
            {j.live && <span className="text-xs text-green-400">LIVE</span>}
          </div>
        ))}
      </div>
    </div>
  )
}
