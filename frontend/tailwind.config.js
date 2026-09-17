/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"IBM Plex Sans"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        display: ['"IBM Plex Sans"', 'ui-sans-serif', 'system-ui', 'sans-serif']
      },
      colors: {
        atoms: {
          DEFAULT: '#4267ff',
          dark: '#3451d6',
          soft: '#eef1ff'
        },
        canvas: '#f6f6f6',
        ink: 'rgba(12,12,12,0.95)'
      },
      boxShadow: {
        card: '0 1px 2px rgba(12,12,12,.04)',
        pop: '0 12px 40px rgba(12,12,12,.12)'
      }
    }
  },
  plugins: []
}
