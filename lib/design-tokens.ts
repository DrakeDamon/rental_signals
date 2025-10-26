/**
 * LeaseRadar Design Tokens
 * Based on competitive analysis of Zillow and Airbnb UX patterns
 */

export const designTokens = {
  breakpoints: {
    mobile: 0,
    sm: 640,
    md: 768,
    lg: 1024,
    xl: 1280,
  },
  
  containerWidths: {
    sm: 540,
    md: 720,
    lg: 960,
    xl: 1140,
  },
  
  spacing: [4, 8, 12, 16, 24, 32, 40, 48, 64],
  
  radii: {
    none: 0,
    sm: 4,
    md: 8,
    lg: 12,
    full: 9999,
  },
  
  shadows: {
    xs: '0 1px 2px rgba(0,0,0,0.05)',
    sm: '0 1px 3px rgba(0,0,0,0.1)',
    md: '0 4px 6px rgba(0,0,0,0.1)',
    lg: '0 10px 15px rgba(0,0,0,0.1)',
  },
  
  typography: {
    families: {
      body: "'Inter', sans-serif",
      heading: "'Inter', sans-serif",
      mono: "'SFMono-Regular', monospace",
    },
    sizes: {
      xs: 12,
      sm: 14,
      base: 16,
      lg: 20,
      xl: 24,
      '2xl': 30,
      '3xl': 36,
      '4xl': 48,
    },
    lineHeights: {
      xs: 1.2,
      sm: 1.3,
      base: 1.5,
      lg: 1.6,
      xl: 1.4,
    },
    weights: {
      light: 300,
      regular: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
    letterSpacing: {
      tight: -0.5,
      normal: 0,
      wide: 0.5,
    },
  },
  
  colors: {
    light: {
      neutral: {
        0: '#FFFFFF',
        50: '#F7FAFC',
        100: '#F1F5F9',
        200: '#E2E8F0',
        300: '#CBD5E1',
        400: '#94A3B8',
        500: '#64748B',
        600: '#475569',
        700: '#334155',
        800: '#1E293B',
        900: '#0F172A',
      },
      brand: {
        primary: '#0057D9',
        hover: '#004BC0',
        active: '#003EAD',
        focus: '#002C7A',
      },
      accent: {
        primary: '#00A099',
        hover: '#009086',
        active: '#007C75',
        focus: '#005C56',
      },
      semantic: {
        success: {
          default: '#28A745',
          hover: '#218838',
          active: '#1E7E34',
        },
        warning: {
          default: '#FFC107',
          hover: '#E0A800',
          active: '#C69500',
        },
        error: {
          default: '#DC3545',
          hover: '#C82333',
          active: '#BD2130',
        },
        info: {
          default: '#17A2B8',
          hover: '#138496',
          active: '#0F667D',
        },
      },
    },
    dark: {
      neutral: {
        0: '#0F172A',
        50: '#1E293B',
        100: '#334155',
        200: '#475569',
        300: '#64748B',
        400: '#94A3B8',
        500: '#AAB8C9',
        600: '#CDD5DF',
        700: '#E2E8F0',
        800: '#F1F5F9',
        900: '#FFFFFF',
      },
      brand: {
        primary: '#508FFF',
        hover: '#6AA3FF',
        active: '#397FFF',
        focus: '#235FD9',
      },
      accent: {
        primary: '#35CFC8',
        hover: '#2DB6B0',
        active: '#249C97',
        focus: '#176B69',
      },
      semantic: {
        success: {
          default: '#28D17C',
          hover: '#1DB869',
          active: '#179B55',
        },
        warning: {
          default: '#FFC857',
          hover: '#E0B04B',
          active: '#C69840',
        },
        error: {
          default: '#F26D6D',
          hover: '#D95A5A',
          active: '#B84A4A',
        },
        info: {
          default: '#5AC8E8',
          hover: '#48B2D4',
          active: '#3A99BB',
        },
      },
    },
  },
  
  motion: {
    durations: {
      fast: 150,
      medium: 300,
      slow: 500,
    },
    easings: {
      standard: 'cubic-bezier(0.4, 0, 0.2, 1)',
      decelerate: 'cubic-bezier(0.0, 0, 0.2, 1)',
      accelerate: 'cubic-bezier(0.4, 0, 1, 1)',
    },
  },
} as const;

export type Theme = 'light' | 'dark' | 'system';

