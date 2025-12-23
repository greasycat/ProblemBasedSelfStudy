/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#8C5E35', // brilliant azure
          light: '#F2CEA2', // light azure
          dark: '#736555', // darker azure for hover
        },
        background: {
          DEFAULT: '#F2EBDC', // light yellow
          off: '#fafafa', // off-white
          subtle: '#f5f5f5', // subtle off-white
        },
        text: {
          primary: '#000', // dusty grape
          secondary: '#666', // dark gray
          light: '#9ca3af', // light gray
        },
        border: {
          DEFAULT: '#3083DC', // brilliant azure
          light: '#a8cbf0', // light azure
        },
        error: '#c1121f', // brick red
        success: '#27ae60',
        warning: '#f39c12',
      },
    },
  },
  plugins: [],
}
