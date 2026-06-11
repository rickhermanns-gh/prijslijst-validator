/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#0F4C81',      // Delfts Blauw
        secondary: '#7DA8D0',    // Middenblauw
        'bg-light': '#E8F0FB',   // Lichtblauw
        'bg-page': '#F5F5F5',    // Lichtgrijs
        'border-color': '#D0DFF0', // Randblauw
        'text-color': '#111111',  // Inkt Zwart
      },
      fontFamily: {
        futura: ['Futura', 'Century Gothic', 'Trebuchet MS', 'sans-serif'],
      },
      fontSize: {
        'display': ['48px', { fontWeight: '900', lineHeight: '1.2' }],
        'h1': ['28px', { fontWeight: '900', lineHeight: '1.3' }],
        'h2': ['18px', { fontWeight: '900', lineHeight: '1.4' }],
        'body': ['14px', { fontWeight: '400', lineHeight: '1.7' }],
        'label': ['9px', { fontWeight: '700', textTransform: 'uppercase', letterSpacing: '3px' }],
      },
      borderRadius: {
        'card': '12px',
        'input': '8px',
      },
      boxShadow: {
        'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        'md': '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
      },
    },
  },
  plugins: [],
};
