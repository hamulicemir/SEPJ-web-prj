export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
    "node_modules/flowbite-react/lib/esm/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        'neutral-secondary-medium': '#f0f2f5',
        'default-medium': '#d1d5db',
        'heading': '#111827',
        'brand': '#2563eb',
        'body': '#6b7280',
      },
      borderRadius: {
        base: '0.5rem',
      },
      boxShadow: {
        xs: '0 1px 2px rgba(0, 0, 0, 0.05)',
      },
    },
  },
  plugins: [require("flowbite/plugin")],
};
