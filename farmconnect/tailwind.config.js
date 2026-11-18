/** Design tokens for Local Farm Map.
 * Single source of truth for palette, type and spacing — change here,
 * rebuild (npm run build), and every screen updates (SDD §6).
 *
 * Palette rationale: leaf greens for brand/action, warm stone neutrals for
 * surfaces (soil, not corporate grey), harvest amber as the accent for
 * exact-pin markers and cautions. No webfonts — system stack only for
 * bandwidth (NFR-03).
 */
export default {
  content: ['./templates/**/*.html', './static/**/*.js'],
  theme: {
    extend: {
      colors: {
        // primary — deep leaf greens (brand, buttons, approximate-pin dots)
        leaf: {
          50: '#F2F7F1',
          100: '#DFEEDC',
          200: '#BFDCBC',
          300: '#93C193',
          400: '#64A268',
          500: '#46854B',
          600: '#356C3A',
          700: '#2B5A31',  // primary action / brand
          800: '#224728',
          900: '#1A3820',
        },
        // accent — harvest amber (exact-pin dots, cautions)
        harvest: {
          50: '#FDF7ED',
          100: '#F9EACC',
          300: '#E5B967',
          500: '#C2761B',
          600: '#A35F13',
          700: '#82490F',
        },
        // warm neutral surfaces — soil tones, not corporate grey
        soil: {
          50: '#FAF9F4',   // page background
          100: '#F1EFE6',
          200: '#E1DECF',
          300: '#C8C3AE',
          400: '#99947D',
          500: '#6F6B59',
          700: '#45432F',
          800: '#33321F',
          900: '#262516',  // ink
        },
      },
      fontFamily: {
        sans: [
          'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'Ubuntu',
          '"Noto Sans"', 'sans-serif',
        ],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Consolas', 'monospace'],
      },
      borderRadius: {
        card: '0.75rem',
      },
      maxWidth: {
        shell: '42rem',  // single-column content width
      },
    },
  },
  plugins: [],
};
