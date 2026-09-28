/** @type {import('tailwindcss').Config} */
export default {
    content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
    theme: {
        extend: {
            fontFamily: {
                // Matches aeonnimbus.com exactly
                display: ['Newsreader', 'Georgia', 'serif'],      // editorial headings
                body:    ['Inter', 'system-ui', 'sans-serif'],    // UI / body
                mono:    ['"JetBrains Mono"', 'monospace'],       // data / numbers
            },
            colors: {
                // Exact aeonnimbus.com CSS variable values
                surface: {
                    DEFAULT: '#07070A',   // --bg
                    raised:  '#0D0C10',   // --bg1 / --paper
                    elevated:'#131217',   // --bg2 / --paper2
                    overlay: '#1A1920',   // --bg3 / --paper3
                },
                ink: {
                    DEFAULT: '#F0ECE4',   // --ink  (warm cream)
                    2:       '#B4AFA8',   // --ink2
                    3:       '#706B65',   // --ink3
                },
                accent: {
                    DEFAULT: '#C8830A',   // --gold
                    light:   '#E09820',   // --gold2
                    tint:    'rgba(200,131,10,0.10)',  // --goldlt
                    rule:    'rgba(200,131,10,0.13)',  // --rule
                    glow:    'rgba(200,131,10,0.18)',
                },
                gold: {
                    DEFAULT: '#C8830A',
                    light:   '#E09820',
                    tint:    'rgba(200,131,10,0.10)',
                    glow:    'rgba(200,131,10,0.15)',
                },
                emerald: {
                    DEFAULT: '#3EAF72',   // --green
                    light:   '#5DC98E',
                    dark:    '#2A8A57',
                },
                rose: {
                    DEFAULT: '#DC5555',   // --red
                    light:   '#F07070',
                    dark:    '#C03030',
                },
                sky: {
                    DEFAULT: '#5B9CF6',   // --blue
                    light:   '#80B4FF',
                    dark:    '#3A7CD4',
                },
                teal: {
                    DEFAULT: '#2A7A82',   // --teal
                    light:   '#3A9AA4',   // --teal2
                },
                muted: '#706B65',          // --ink3
                rule:  'rgba(200,131,10,0.13)',
                rule2: 'rgba(255,255,255,0.06)',
            },
            borderRadius: {
                DEFAULT: '4px',
                sm: '2px',
                md: '6px',
                lg: '8px',
                xl: '10px',
                '2xl': '12px',
                '3xl': '16px',
            },
            boxShadow: {
                glow:         '0 0 20px rgba(200,131,10,0.15), 0 0 6px rgba(200,131,10,0.08)',
                'glow-gold':  '0 0 20px rgba(200,131,10,0.20)',
                card:         '0 2px 16px rgba(0,0,0,0.55), 0 1px 2px rgba(0,0,0,0.30)',
                'card-hover': '0 4px 32px rgba(0,0,0,0.65), 0 0 16px rgba(200,131,10,0.06)',
                panel:        '0 1px 0 rgba(200,131,10,0.13)',
            },
            animation: {
                'fade-in':  'fadeIn 0.4s ease-out forwards',
                'slide-up': 'slideUp 0.4s ease-out forwards',
                shimmer:    'shimmer 2.5s linear infinite',
            },
            keyframes: {
                fadeIn: {
                    '0%':   { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                slideUp: {
                    '0%':   { opacity: '0', transform: 'translateY(12px)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' },
                },
                shimmer: {
                    '0%':   { backgroundPosition: '-200% 0' },
                    '100%': { backgroundPosition: '200% 0' },
                },
            },
        },
    },
    plugins: [],
};
