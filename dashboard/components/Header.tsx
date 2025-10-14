'use client'

interface HeaderProps {
  activeView: 'overview' | 'analytics' | 'hotspots'
  setActiveView: (view: 'overview' | 'analytics' | 'hotspots') => void
}

export default function Header({ activeView, setActiveView }: HeaderProps) {
  return (
    <header className="bg-white shadow-md">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-2xl font-bold text-primary-600">
              🌍 UCIP Dashboard
            </h1>
            <span className="text-sm text-gray-500">
              Urban Carbon Intelligence Platform
            </span>
          </div>
          
          <nav className="flex space-x-4">
            <button
              onClick={() => setActiveView('overview')}
              className={`px-4 py-2 rounded-lg transition-colors ${
                activeView === 'overview'
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => setActiveView('analytics')}
              className={`px-4 py-2 rounded-lg transition-colors ${
                activeView === 'analytics'
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              Analytics
            </button>
            <button
              onClick={() => setActiveView('hotspots')}
              className={`px-4 py-2 rounded-lg transition-colors ${
                activeView === 'hotspots'
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              AI Assistant
            </button>
          </nav>
        </div>
      </div>
    </header>
  )
}
