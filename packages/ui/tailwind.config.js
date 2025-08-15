const path = require('path');

// Import design tokens from the root of the monorepo.  A relative
// `require` call is used so that Tailwind can read static values at
// build time.  Should the tokens file be relocated, update this path
// accordingly.
const tokens = require('../../blackroad/design-tokens.json');

// Destructure the pieces of the design tokens for easier access.  The
// structure mirrors the contents of `design-tokens.json`.
const { color, font, radius } = tokens;

/**
 * Tailwind CSS configuration for the BlackRoad UI library.
 *
 * The configuration extends the default Tailwind theme to include
 * semantic color names, font families, sizes and border radii based on
 * our design tokens.  Using the token values directly ensures that
 * updates to the tokens automatically propagate to all components.
 */
module.exports = {
  content: [
    path.join(__dirname, 'src/**/*.{js,ts,jsx,tsx}'),
  ],
  theme: {
    extend: {
      colors: {
        primary: color.primary,
        secondary: color.secondary,
        accent: color.accent,
        neutral: color.neutral,
        info: color.info,
        danger: color.danger,
        warning: color.warning,
        success: color.success,
      },
      fontFamily: {
        sans: [font.family.sans],
        mono: [font.family.mono],
      },
      fontSize: font.size,
      borderRadius: radius,
    },
  },
  plugins: [],
};
