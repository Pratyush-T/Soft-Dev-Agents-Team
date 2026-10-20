/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Brand Primary (Professional Executive Blue)
        brand: {
          50: '#EFF6FF',
          100: '#DBEAFE',
          200: '#BFDBFE',
          300: '#93C5FD',
          400: '#60A5FA',
          500: '#3B82F6',
          600: '#0A66C2', // Signature ProNet Primary
          700: '#004182',
          800: '#002B56',
          900: '#001833',
          950: '#000E20',
        },
        // Neutral Grayscale (Slate Scale for UI Surfaces & Borders)
        surface: {
          50: '#F8FAFC',  // Main Page Canvas Background
          100: '#F1F5F9', // Secondary Containers / Input Backgrounds
          200: '#E2E8F0', // Card Borders / Dividers
          300: '#CBD5E1', // Hover Borders / Inactive Icons
          400: '#94A3B8', // Placeholder Text / Disabled Indicators
          500: '#64748B', // Muted Secondary Copy / Timestamps
          600: '#475569', // Primary Subtitles / Icon Accents
          700: '#334155', // Body Copy Secondary
          800: '#1E293B', // High-Emphasis Titles
          900: '#0F172A', // Primary Headings & Dark Elements
          950: '#020617', // Extreme Dark / Contrast Overlays
        },
        // Semantic Status Tokens
        success: {
          50: '#ECFDF5',
          100: '#D1FAE5',
          200: '#A7F3D0',
          500: '#10B981',
          600: '#059669', // Confirmed / Accepted / Online Status
          700: '#047857',
        },
        warning: {
          50: '#FFFBEB',
          100: '#FEF3C7',
          200: '#FDE68A',
          500: '#F59E0B',
          600: '#D97706', // Pending Request / Reviewing Status
          700: '#B45309',
        },
        danger: {
          50: '#FEF2F2',
          100: '#FEE2E2',
          200: '#FECACA',
          500: '#EF4444',
          600: '#DC2626', // Rejections / Errors / Disconnect Actions
          700: '#B91C1C',
        },
        info: {
          50: '#EEF2FF',
          100: '#E0E7FF',
          200: '#C7D2FE',
          500: '#6366F1',
          600: '#4F46E5', // System Notices / Info Banners
          700: '#4338CA',
        },
        // Degree Badges & Reaction Tokens
        degree: {
          first: {
            bg: '#ECFDF5',
            text: '#065F46',
            border: '#A7F3D0',
          },
          second: {
            bg: '#EFF6FF',
            text: '#1E40AF',
            border: '#BFDBFE',
          },
          third: {
            bg: '#F1F5F9',
            text: '#475569',
            border: '#CBD5E1',
          },
        },
        reaction: {
          like: '#0A66C2',       // Thumbs Up Blue
          celebrate: '#059669',  // Hands Clapping Green
          insightful: '#D97706', // Lightbulb Amber
        },
      },
      boxShadow: {
        'elevation-1': '0 1px 3px 0 rgba(15, 23, 42, 0.08), 0 1px 2px -1px rgba(15, 23, 42, 0.08)',
        'elevation-2': '0 4px 6px -1px rgba(15, 23, 42, 0.10), 0 2px 4px -2px rgba(15, 23, 42, 0.06)',
        'elevation-3': '0 10px 15px -3px rgba(15, 23, 42, 0.12), 0 4px 6px -4px rgba(15, 23, 42, 0.08)',
        'elevation-float': '0 20px 25px -5px rgba(15, 23, 42, 0.15), 0 8px 10px -6px rgba(15, 23, 42, 0.10)',
      },
    },
  },
  plugins: [],
};
