'use client'

import { useState } from 'react'

interface Hotspot {
  id: string
  name: string
  emissions: number
  priority: 'high' | 'medium' | 'low'
  reduction: number
}

export default function HotspotList() {
  const [hotspots] = useState<Hotspot[]>([
    {
      id: '1',
      name: 'Pattee Library',
      emissions: 3500,
      priority: 'high',
      reduction: 1050
    },
    {
      id: '2', 
      name: 'Thomas Building',
      emissions: 2800,
      priority: 'high',
      reduction: 840
    },
    {
      id: '3',
      name: 'Engineering Building',
      emissions: 2600,
      priority: 'medium',
      reduction: 780
    },
    {
      id: '4',
      name: 'Student Union',
      emissions: 2200,
      priority: 'medium',
      reduction: 660
    },
    {
      id: '5',
      name: 'Recreation Hall',
      emissions: 1800,
      priority: 'low',
      reduction: 540
    }
  ])

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800 border-red-200'
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'low': return 'bg-green-100 text-green-800 border-green-200'
      default: return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  return (
    <div className="space-y-3">
      {hotspots.map((hotspot) => (
        <div
          key={hotspot.id}
          className="p-3 border rounded-lg hover:shadow-md transition-shadow cursor-pointer"
        >
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-medium">{hotspot.name}</h4>
            <span className={`px-2 py-1 rounded-full text-xs border ${getPriorityColor(hotspot.priority)}`}>
              {hotspot.priority}
            </span>
          </div>
          
          <div className="space-y-1">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Current:</span>
              <span className="font-medium">{hotspot.emissions.toLocaleString()} kg CO2</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Potential Reduction:</span>
              <span className="font-medium text-green-600">
                -{hotspot.reduction.toLocaleString()} kg CO2
              </span>
            </div>
          </div>
        </div>
      ))}
      
      <div className="pt-3 border-t">
        <button className="w-full text-primary-600 hover:text-primary-700 text-sm font-medium">
          View All Hotspots →
        </button>
      </div>
    </div>
  )
}
