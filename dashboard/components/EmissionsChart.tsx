'use client'

import { useState, useEffect } from 'react'

export default function EmissionsChart() {
  const [data, setData] = useState<number[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Simulate API call
    const fetchData = async () => {
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // Generate sample data
      const sampleData = Array.from({ length: 30 }, (_, i) => 
        Math.floor(Math.random() * 1000) + 800
      )
      setData(sampleData)
      setLoading(false)
    }

    fetchData()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  const maxValue = Math.max(...data)
  const minValue = Math.min(...data)

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Daily Emissions (kg CO2)</h3>
        <div className="text-sm text-gray-600">
          Last 30 days
        </div>
      </div>
      
      {/* Simple bar chart */}
      <div className="h-48 flex items-end space-x-1">
        {data.map((value, index) => {
          const height = (value / maxValue) * 100
          const color = value > 900 ? 'bg-red-500' : value > 850 ? 'bg-yellow-500' : 'bg-green-500'
          
          return (
            <div
              key={index}
              className={`${color} w-3 rounded-t transition-all duration-300 hover:opacity-80`}
              style={{ height: `${height}%` }}
              title={`Day ${index + 1}: ${value} kg CO2`}
            />
          )
        })}
      </div>
      
      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 pt-4 border-t">
        <div className="text-center">
          <div className="text-2xl font-bold text-primary-600">{maxValue}</div>
          <div className="text-sm text-gray-600">Peak</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-primary-600">
            {Math.round(data.reduce((a, b) => a + b, 0) / data.length)}
          </div>
          <div className="text-sm text-gray-600">Average</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-primary-600">{minValue}</div>
          <div className="text-sm text-gray-600">Lowest</div>
        </div>
      </div>
    </div>
  )
}
