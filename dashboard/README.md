# UCIP Dashboard

React + Next.js dashboard for the Urban Carbon Intelligence Platform.

## Features

- **Interactive Map**: Mapbox-powered visualization of emissions hotspots
- **Real-time Data**: Live emissions monitoring and alerts
- **Forecasting**: Time series predictions with confidence intervals
- **Policy Simulator**: Test intervention scenarios
- **AI Chatbot**: Natural language queries and recommendations

## Getting Started

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Open http://localhost:3000
```

## Tech Stack

- **Framework**: Next.js 14 (React 18)
- **Maps**: Mapbox GL JS, react-map-gl
- **Charts**: Plotly.js
- **Styling**: TailwindCSS
- **State**: React Query
- **API**: Axios

## Project Structure

```
dashboard/
├── app/                 # Next.js app directory
│   ├── page.tsx        # Home page
│   ├── map/            # Map view
│   ├── analytics/      # Analytics dashboard
│   └── policy/         # Policy simulator
├── components/         # Reusable components
│   ├── Map.tsx
│   ├── Chart.tsx
│   └── Chatbot.tsx
├── lib/                # Utilities
│   └── api.ts          # API client
└── public/             # Static assets
```

## Environment Variables

Create a `.env.local` file:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_MAPBOX_TOKEN=your_mapbox_token
```

## Build for Production

```bash
npm run build
npm start
```

