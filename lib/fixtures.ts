import type { Listing, PricePoint } from '@/types';

// Helper to generate 90 days of price history
function generatePriceHistory(basePrice: number, hasDrop: boolean = false): PricePoint[] {
  const points: PricePoint[] = [];
  const now = new Date();
  
  for (let i = 11; i >= 0; i--) {
    const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const period = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
    
    // Simulate price variation with trend
    let price = basePrice;
    
    // General upward trend (0-3% growth per month)
    const growthFactor = 1 + (Math.random() * 0.03);
    price = price * Math.pow(growthFactor, 11 - i);
    
    // Add recent drop if applicable (last 1-2 months)
    if (hasDrop && i <= 1) {
      price = price * 0.90; // 10% drop
    }
    
    // Add some randomness
    price = price * (0.98 + Math.random() * 0.04);
    
    points.push({
      period,
      value: Math.round(price),
    });
  }
  
  return points;
}

export const fixtureListings: Listing[] = [
  {
    id: 'tampa-1',
    title: 'Modern Loft in Hyde Park',
    address: '456 S Hyde Park Ave, Tampa, FL 33606',
    neighborhood: 'Hyde Park',
    beds: 2,
    baths: 2,
    sqft: 1250,
    currentAsk: 2800,
    priceSeries: generatePriceHistory(2650, false),
    images: [
      'https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800',
      'https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800',
    ],
    amenities: ['Pool', 'Fitness Center', 'Pet Friendly', 'In-Unit Laundry'],
    lat: 27.9389,
    lng: -82.4731,
    yoyPct: 8.5,
    momPct: 2.1,
  },
  {
    id: 'tampa-2',
    title: 'Waterfront Studio - Channelside',
    address: '789 Channelside Dr, Tampa, FL 33602',
    neighborhood: 'Channelside',
    beds: 0,
    baths: 1,
    sqft: 650,
    currentAsk: 1650,
    lastDrop: {
      amount: 150,
      daysAgo: 14,
    },
    concessions: ['1 month free'],
    priceSeries: generatePriceHistory(1800, true),
    images: [
      'https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800',
      'https://images.unsplash.com/photo-1536376072261-38c75010e6c9?w=800',
    ],
    amenities: ['Waterfront', 'Rooftop Deck', 'Concierge', 'Parking'],
    lat: 27.9433,
    lng: -82.4487,
    yoyPct: -8.3,
    momPct: -8.3,
  },
  {
    id: 'tampa-3',
    title: 'Spacious 3BR Family Home - Westshore',
    address: '234 Westshore Blvd, Tampa, FL 33607',
    neighborhood: 'Westshore',
    beds: 3,
    baths: 2.5,
    sqft: 1850,
    currentAsk: 3200,
    priceSeries: generatePriceHistory(2950, false),
    images: [
      'https://images.unsplash.com/photo-1493809842364-78817add7ffb?w=800',
      'https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800',
    ],
    amenities: ['Garage', 'Backyard', 'Updated Kitchen', 'Fireplace'],
    lat: 27.9506,
    lng: -82.5170,
    yoyPct: 10.2,
    momPct: 3.4,
  },
  {
    id: 'tampa-4',
    title: 'Student-Friendly 2BR near USF',
    address: '123 Fletcher Ave, Tampa, FL 33612',
    neighborhood: 'USF',
    beds: 2,
    baths: 2,
    sqft: 950,
    currentAsk: 1550,
    concessions: ['$500 deposit special'],
    priceSeries: generatePriceHistory(1500, false),
    images: [
      'https://images.unsplash.com/photo-1522771739844-6a9f6d5f14af?w=800',
      'https://images.unsplash.com/photo-1484154218962-a197022b5858?w=800',
    ],
    amenities: ['Pool', 'Bus Stop', 'Study Room', 'Free WiFi'],
    lat: 28.0587,
    lng: -82.4139,
    yoyPct: 4.8,
    momPct: 1.2,
  },
  {
    id: 'tampa-5',
    title: 'Luxury Penthouse - Downtown',
    address: '555 N Ashley Dr, Tampa, FL 33602',
    neighborhood: 'Downtown',
    beds: 2,
    baths: 2,
    sqft: 1450,
    currentAsk: 3500,
    priceSeries: generatePriceHistory(3300, false),
    images: [
      'https://images.unsplash.com/photo-1512918728675-ed5a9ecdebfd?w=800',
      'https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=800',
    ],
    amenities: ['City Views', 'Concierge', 'Valet', 'Rooftop Pool'],
    lat: 27.9506,
    lng: -82.4572,
    yoyPct: 12.1,
    momPct: 2.8,
  },
  {
    id: 'tampa-6',
    title: 'Cozy 1BR in Seminole Heights',
    address: '888 N Florida Ave, Tampa, FL 33603',
    neighborhood: 'Seminole Heights',
    beds: 1,
    baths: 1,
    sqft: 750,
    currentAsk: 1400,
    lastDrop: {
      amount: 100,
      daysAgo: 7,
    },
    priceSeries: generatePriceHistory(1500, true),
    images: [
      'https://images.unsplash.com/photo-1449844908441-8829872d2607?w=800',
      'https://images.unsplash.com/photo-1513694203232-719a280e022f?w=800',
    ],
    amenities: ['Hardwood Floors', 'Pet Friendly', 'Patio', 'Bike Storage'],
    lat: 27.9731,
    lng: -82.4567,
    yoyPct: -6.7,
    momPct: -6.7,
  },
  {
    id: 'tampa-7',
    title: 'Beachside Apartment - South Tampa',
    address: '999 Bayshore Blvd, Tampa, FL 33606',
    neighborhood: 'South Tampa',
    beds: 1,
    baths: 1,
    sqft: 850,
    currentAsk: 2100,
    priceSeries: generatePriceHistory(1950, false),
    images: [
      'https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800',
      'https://images.unsplash.com/photo-1522050212171-61b01dd24579?w=800',
    ],
    amenities: ['Bay Views', 'Balcony', 'Walking Trail', 'Gated'],
    lat: 27.9336,
    lng: -82.4797,
    yoyPct: 9.3,
    momPct: 2.5,
  },
  {
    id: 'tampa-8',
    title: '2BR Townhome - New Tampa',
    address: '321 Bruce B Downs Blvd, Tampa, FL 33647',
    neighborhood: 'New Tampa',
    beds: 2,
    baths: 2.5,
    sqft: 1350,
    currentAsk: 2200,
    priceSeries: generatePriceHistory(2100, false),
    images: [
      'https://images.unsplash.com/photo-1512915922686-57c11dde9b6b?w=800',
      'https://images.unsplash.com/photo-1523217582562-09d0def993a6?w=800',
    ],
    amenities: ['2 Car Garage', 'Community Pool', 'Playground', 'HOA Maintained'],
    lat: 28.0678,
    lng: -82.3987,
    yoyPct: 7.8,
    momPct: 1.8,
  },
  {
    id: 'tampa-9',
    title: 'Industrial Loft - Ybor City',
    address: '1515 E 7th Ave, Tampa, FL 33605',
    neighborhood: 'Ybor City',
    beds: 1,
    baths: 1,
    sqft: 900,
    currentAsk: 1750,
    lastDrop: {
      amount: 200,
      daysAgo: 21,
    },
    concessions: ['First month free'],
    priceSeries: generatePriceHistory(1950, true),
    images: [
      'https://images.unsplash.com/photo-1502672023488-70e25813eb80?w=800',
      'https://images.unsplash.com/photo-1493809842364-78817add7ffb?w=800',
    ],
    amenities: ['Historic Building', 'Exposed Brick', 'High Ceilings', 'Walk to Nightlife'],
    lat: 27.9606,
    lng: -82.4372,
    yoyPct: -10.3,
    momPct: -10.3,
  },
  {
    id: 'tampa-10',
    title: '3BR Home with Pool - Carrollwood',
    address: '678 Carrollwood Village Dr, Tampa, FL 33618',
    neighborhood: 'Carrollwood',
    beds: 3,
    baths: 2,
    sqft: 1750,
    currentAsk: 2900,
    priceSeries: generatePriceHistory(2700, false),
    images: [
      'https://images.unsplash.com/photo-1480074568708-e7b720bb3f09?w=800',
      'https://images.unsplash.com/photo-1448630360428-65456885c650?w=800',
    ],
    amenities: ['Private Pool', 'Large Yard', 'Updated Appliances', 'Pet Friendly'],
    lat: 28.0514,
    lng: -82.5106,
    yoyPct: 11.5,
    momPct: 3.1,
  },
];

// Tampa-specific neighborhoods
export const neighborhoods = [
  'Hyde Park',
  'Channelside',
  'Westshore',
  'USF',
  'Downtown',
  'Seminole Heights',
  'South Tampa',
  'New Tampa',
  'Ybor City',
  'Carrollwood',
];

// Default map center (Tampa)
export const defaultMapCenter = {
  latitude: 27.9506,
  longitude: -82.4572,
  zoom: 11,
};

