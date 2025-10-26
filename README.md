# LeaseRadar - Tampa Rental Price Tracker

A modern Next.js application for tracking Tampa rental prices with real-time updates, price drop alerts, and comprehensive market analytics.

## ✨ Features

- **🏠 Smart Search** - Neighborhood, address, and ZIP code search with autocomplete
- **📊 Price Tracking** - Historical rent trends with 30/90-day views
- **💰 Price Drop Alerts** - Get notified when prices drop on your favorite listings
- **❤️ Watchlist** - Save and track multiple listings
- **🗺️ Map Integration** - Visual map with synchronized list view (placeholder)
- **🎨 Modern Design** - LeaseRadar design system with light/dark mode
- **📱 Responsive** - Mobile-first design with adaptive layouts
- **♿ Accessible** - WCAG 2.2 AA compliant with keyboard navigation

## 🎨 Design System

### Design Tokens

- **Colors**: Light/dark themes with neutral, brand (blue), accent (teal), and semantic colors
- **Typography**: Inter font with 8 size scales (xs to 4xl)
- **Spacing**: 4px rhythm system [4, 8, 12, 16, 24, 32, 40, 48, 64]
- **Shadows**: 4 levels (xs, sm, md, lg)
- **Motion**: 3 durations (fast, medium, slow) with cubic-bezier easings
- **Breakpoints**: sm (640px), md (768px), lg (1024px), xl (1280px)

### Components Built

- `SearchBar` - Autocomplete neighborhood search
- `FilterBar` - Sticky filter bar with price range, beds, baths, neighborhoods
- `RangeSlider` - Accessible dual-thumb price slider
- `ResultCard` - Listing cards with hover effects and watchlist integration
- `TrendChart` - Price history charts with interval toggles
- `Map` - Placeholder map component (MapLibre integration pending)
- `ThemeToggle` - Light/dark/system theme switcher
- `Skeleton` - Loading placeholders with shimmer animation
- `Navbar` - Responsive navigation with mobile menu
- `Footer` - Multi-column footer with links

## 📁 Project Structure

```
rent-signals-ui/
├── app/                          # Next.js 14 App Router
│   ├── page.tsx                  # Landing page with hero
│   ├── search/page.tsx           # Search with map/list split view
│   ├── markets/page.tsx          # All markets grid view
│   ├── drops/page.tsx            # Price drops page
│   ├── watchlist/page.tsx        # Saved listings & alerts
│   ├── listing/[id]/page.tsx     # Listing detail page
│   ├── layout.tsx                # Root layout with nav/footer
│   └── globals.css               # CSS variables & utility classes
├── components/                   # React components
│   ├── SearchBar.tsx
│   ├── FilterBar.tsx
│   ├── RangeSlider.tsx
│   ├── ResultCard.tsx
│   ├── TrendChart.tsx
│   ├── Map.tsx
│   ├── ThemeToggle.tsx
│   ├── Skeleton.tsx
│   ├── Navbar.tsx
│   └── Footer.tsx
├── lib/                          # Utilities & state
│   ├── design-tokens.ts          # Design system tokens
│   ├── store.ts                  # Zustand state management
│   ├── fixtures.ts               # Sample Tampa listings
│   ├── fetcher.ts                # API fetch wrapper
│   └── utils.ts                  # Helper functions
├── hooks/                        # Custom React hooks
│   └── useTheme.ts               # Theme management
├── types/                        # TypeScript definitions
│   └── index.ts                  # Type definitions
└── tailwind.config.ts            # Tailwind with design tokens
```

## 🚀 Getting Started

### Prerequisites

- **Node.js 18.17.0+** (required by Next.js 14)
- **npm** or **yarn**

### Installation

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Open http://localhost:3000
```

### Development

```bash
# Start dev server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run linter
npm run lint
```

## 🎯 Pages & Routes

| Route | Description |
|-------|-------------|
| `/` | Landing page with hero and featured drops |
| `/search` | Search results with map/list view |
| `/markets` | Browse all available listings |
| `/drops` | Listings with recent price drops |
| `/watchlist` | Saved listings and alerts management |
| `/listing/[id]` | Detailed listing view with price history |

## 💾 State Management

Uses **Zustand** for lightweight state management:

- **Listings** - 10 fixture listings with 90-day price history
- **Watchlist** - Persisted to localStorage
- **Alerts** - Persisted to localStorage
- **Filters** - Price range, beds, baths, neighborhoods
- **Map View** - Center, zoom level
- **Theme** - Light/dark/system preference

## 🎨 Theme System

Toggle between light, dark, and system themes with the `ThemeToggle` component. Theme preference is persisted to localStorage.

```tsx
import { useTheme } from '@/hooks/useTheme';

const { theme, setTheme, resolvedTheme } = useTheme();
```

## 📊 Data & Fixtures

Sample data includes 10 Tampa listings across neighborhoods:

- Hyde Park
- Channelside
- Westshore
- USF
- Downtown
- Seminole Heights
- South Tampa
- New Tampa
- Ybor City
- Carrollwood

Each listing includes:
- 90-day price history
- 30% have recent price drops
- Realistic addresses and amenities
- Concessions and special offers

## 🗺️ Map Integration (Pending)

The current Map component is a placeholder. To integrate MapLibre GL:

1. Install dependencies:
```bash
npm install react-map-gl maplibre-gl
```

2. Get a free map style:
   - Use OpenStreetMap with MapLibre
   - Or Maptiler free tier

3. Update `components/Map.tsx` with react-map-gl implementation

## 🔌 API Integration

The app is structured to work with the existing API:

```typescript
// lib/fetcher.ts already configured for:
GET /v1/markets              → Market listings
GET /v1/markets/{metro}/trends → Price history
GET /v1/prices/drops         → Recent drops

// To switch from fixtures to API:
// Update components to use SWR with fetchJson()
```

## 🎨 Customization

### Modify Design Tokens

Edit `tailwind.config.ts` and `app/globals.css`:

```css
/* app/globals.css */
:root {
  --color-brand-primary: #0057D9;  /* Change brand color */
  --color-accent-primary: #00A099; /* Change accent color */
}
```

### Add New Neighborhoods

Edit `lib/fixtures.ts`:

```typescript
export const neighborhoods = [
  'Hyde Park',
  'Your New Neighborhood',
  // ...
];
```

## 📱 Responsive Design

- **Mobile** (`< 768px`): Stacked layout, collapsible map, hamburger menu
- **Tablet** (`768px - 1024px`): 2-column grids, partial map visibility
- **Desktop** (`> 1024px`): Full split-view with map, 3-column grids

## ♿ Accessibility

- Keyboard navigation for all interactive elements
- Focus indicators on buttons, inputs, and links
- ARIA labels on complex components (map, charts, sliders)
- Respects `prefers-reduced-motion`
- Color contrast meets WCAG AA standards
- Semantic HTML throughout

## 🚧 Future Enhancements

- [ ] Complete MapLibre GL integration
- [ ] Real-time price alerts via email/SMS
- [ ] User authentication and profiles
- [ ] Advanced filtering (amenities, pet-friendly, etc.)
- [ ] Saved searches with notifications
- [ ] Comparison tool for multiple listings
- [ ] Neighborhood analytics dashboard
- [ ] Price prediction with ML
- [ ] PWA with offline support

## 📄 License

Built for Tampa Rent Signals data pipeline. Design inspired by Zillow and Airbnb UX patterns.

## 🙏 Acknowledgments

- **Design Inspiration**: Zillow, Airbnb
- **Data Sources**: Zillow ZORI, ApartmentList, FRED
- **Tech Stack**: Next.js 14, Tailwind CSS, Zustand, Radix UI, Recharts

