import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        neutral: {
          0: 'var(--color-neutral-0)',
          50: 'var(--color-neutral-50)',
          100: 'var(--color-neutral-100)',
          200: 'var(--color-neutral-200)',
          300: 'var(--color-neutral-300)',
          400: 'var(--color-neutral-400)',
          500: 'var(--color-neutral-500)',
          600: 'var(--color-neutral-600)',
          700: 'var(--color-neutral-700)',
          800: 'var(--color-neutral-800)',
          900: 'var(--color-neutral-900)',
        },
        brand: {
          DEFAULT: 'var(--color-brand-primary)',
          hover: 'var(--color-brand-hover)',
          active: 'var(--color-brand-active)',
          focus: 'var(--color-brand-focus)',
        },
        accent: {
          DEFAULT: 'var(--color-accent-primary)',
          hover: 'var(--color-accent-hover)',
          active: 'var(--color-accent-active)',
          focus: 'var(--color-accent-focus)',
        },
        success: {
          DEFAULT: 'var(--color-success)',
          hover: 'var(--color-success-hover)',
          active: 'var(--color-success-active)',
        },
        warning: {
          DEFAULT: 'var(--color-warning)',
          hover: 'var(--color-warning-hover)',
          active: 'var(--color-warning-active)',
        },
        error: {
          DEFAULT: 'var(--color-error)',
          hover: 'var(--color-error-hover)',
          active: 'var(--color-error-active)',
        },
        info: {
          DEFAULT: 'var(--color-info)',
          hover: 'var(--color-info-hover)',
          active: 'var(--color-info-active)',
        },
      },
      spacing: {
        '1': '4px',
        '2': '8px',
        '3': '12px',
        '4': '16px',
        '6': '24px',
        '8': '32px',
        '10': '40px',
        '12': '48px',
        '16': '64px',
      },
      borderRadius: {
        'none': '0',
        'sm': '4px',
        'md': '8px',
        'lg': '12px',
        'full': '9999px',
      },
      boxShadow: {
        'xs': '0 1px 2px rgba(0,0,0,0.05)',
        'sm': '0 1px 3px rgba(0,0,0,0.1)',
        'md': '0 4px 6px rgba(0,0,0,0.1)',
        'lg': '0 10px 15px rgba(0,0,0,0.1)',
      },
      fontFamily: {
        sans: ['var(--font-inter)', 'Inter', 'sans-serif'],
        mono: ['SFMono-Regular', 'monospace'],
      },
      fontSize: {
        'xs': ['12px', { lineHeight: '1.2' }],
        'sm': ['14px', { lineHeight: '1.3' }],
        'base': ['16px', { lineHeight: '1.5' }],
        'lg': ['20px', { lineHeight: '1.6' }],
        'xl': ['24px', { lineHeight: '1.4' }],
        '2xl': ['30px', { lineHeight: '1.4' }],
        '3xl': ['36px', { lineHeight: '1.3' }],
        '4xl': ['48px', { lineHeight: '1.2' }],
      },
      fontWeight: {
        light: '300',
        normal: '400',
        medium: '500',
        semibold: '600',
        bold: '700',
      },
      transitionDuration: {
        'fast': '150ms',
        'medium': '300ms',
        'slow': '500ms',
      },
      transitionTimingFunction: {
        'standard': 'cubic-bezier(0.4, 0, 0.2, 1)',
        'decelerate': 'cubic-bezier(0.0, 0, 0.2, 1)',
        'accelerate': 'cubic-bezier(0.4, 0, 1, 1)',
      },
    },
  },
  plugins: [],
}
export default config


