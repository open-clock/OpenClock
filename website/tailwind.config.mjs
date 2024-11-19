/** @type {import('tailwindcss').Config} */
export default {
	content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
	theme: {
		extend: {
			colors: {
				'dark-text': '#f4f4f4',
				'dark-background': '#222222',
				'dark-primary': '#eeeeee',
				'dark-secondary': '#4c4c4c',
				'dark-accent': '#a8a8a8',
				'text': '#0a0a0a',
				'background': '#ffffff',
				'primary': '#121212',
				'secondary': '#b3b3b3',
				'accent': '#575757'
			},
		},
	},
	plugins: [],
}
