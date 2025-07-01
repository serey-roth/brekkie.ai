/** @type {import('tailwindcss').Config} */
export default {
    content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
    theme: {
        extend: {
            fontFamily: {
                'heading': ['Fredoka', 'sans-serif'],
                'body': ['Nunito', 'sans-serif'],
                'sans': ['Nunito', 'sans-serif'],
            },
        },
    },
    plugins: [require('@tailwindcss/typography'), require('tailwindcss-safe-area')],
};
