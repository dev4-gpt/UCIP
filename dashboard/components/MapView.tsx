'use client'

import { useEffect, useRef, useState } from 'react'

export default function MapView() {
  const mapContainer = useRef<HTMLDivElement>(null)
  const [map, setMap] = useState<any>(null)

  useEffect(() => {
    // Initialize Mapbox map
    if (mapContainer.current && !map) {
      // For now, show a placeholder
      // In production, initialize Mapbox GL JS here
      console.log('Map container ready')
    }
  }, [map])

  return (
    <div className="relative">
      <div
        ref={mapContainer}
        className="w-full h-96 bg-gray-200 rounded-lg flex items-center justify-center"
      >
        <div className="text-center">
          <div className="text-6xl mb-4">🗺️</div>
          <p className="text-gray-600">
            Interactive map will load here
          </p>
          <p className="text-sm text-gray-500 mt-2">
            Requires Mapbox token in environment variables
          </p>
        </div>
      </div>
      
      {/* Sample hotspots overlay */}
      <div className="absolute top-4 left-4 bg-white rounded-lg shadow-md p-4">
        <h4 className="font-semibold mb-2">Sample Hotspots</h4>
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-red-500 rounded-full"></div>
            <span className="text-sm">Pattee Library - High Priority</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
            <span className="text-sm">Thomas Building - Medium Priority</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span className="text-sm">Engineering Building - Low Priority</span>
          </div>
        </div>
      </div>
    </div>
  )
}
