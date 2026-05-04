# Pixel Foundry — Visual Rules

Brand spec for every Pixel Foundry export, scene, and infographic.

Canon doc: `docs/products/blackboard/PIXEL_FOUNDRY_CANON.md`

---

## Pixel art rules

- **Crisp.** All sprites are 32 × 32 native. Render with `image-rendering: pixelated; image-rendering: crisp-edges;`. Never blur, never anti-alias, never sub-pixel.
- **Integer scaling only.** Any export at higher resolution must be a clean integer multiple (×2, ×4, ×8, ×16). No fractional scales.
- **No blurry exports.** If a target dimension would force a fractional scale, render at the next higher integer scale and crop, or pad.
- **Transparent props paint own pixels only.** Props in the world-builder draw their silhouette without filling the background — terrain shows through.

## Frame and chrome

- Keep the **black / white OS frame** where appropriate (HUD, stamps, toasts, controls).
- HUD text: white on black or black on white only — **no colored text in HUD**. (Brand rule from `feedback_brand_colors.md`.)
- Pixel content INSIDE the world frame may use the full color palette — that's the brand-asset surface exception (`feedback_apps_stay_grayscale.md`).

## Color tokens

The 6-color BlackRoad gradient — used as accent strips on social cards, banners, neon route markers, and brand bars:

| Token | Hex |
|---|---|
| Orange | `#FF6B2B` |
| Pink | `#FF2255` |
| Magenta | `#CC00AA` |
| Purple | `#8844FF` |
| Blue | `#4488FF` |
| Cyan | `#00D4FF` |

Linear gradient (90deg): `linear-gradient(90deg, #FF6B2B, #FF2255, #CC00AA, #8844FF, #4488FF, #00D4FF)`.

For the canonical CSS source see `brand.blackroad.io/brand.css` — don't invent new tokens, copy exact values (`feedback_brand_css_match.md`).

## Typography

- **JetBrains Mono** for all labels, controls, captions, copy.
- **Space Grotesk** is allowed for marketing headlines on infographics only.
- Press Start 2P is allowed sparingly for retro/nostalgia headlines.
- All caption text is short and claims-safe.

## Scene HUD conventions

Every walkable scene in `scenes-interactive/` follows the same HUD pattern:

| Position | Content |
|---|---|
| Top-left | Scene title (uppercase, letter-spaced) + key hints (WASD, E, Shift) |
| Top-right | Status / route metadata (e.g., `STATUS · ALL CLEAR`) |
| Bottom-center | Interaction toast (white-on-black, 3-second timer) |
| Bottom-right | Stamp: `BlackRoad OS · <subtitle>` |

## Infographic visual style

- Black or near-black background (`#080808`)
- BlackRoad gradient bar top + bottom (8-12px, full width)
- Pixel sprites at integer scales (commonly ×4, ×6, ×8, ×16)
- White / accent-green / cyan typography
- "→ blackroad.io/foundry/" CTA at bottom-center
- Suggested copy panel beside each infographic in the studio

## World-builder + scene exports

- 40 × 25 tile grid · 32 px tile · 1280 × 800 canvas (the BR standard)
- Faint green grid overlay (`rgba(168,232,168,0.16)`) — every tile, bolder lines every 5
- Exported scenes carry a "made with **BlackRoad**" link in bottom-left, pointing to `blackroad.io/foundry/world-builder/`
- Sovereign-analytics beacon `<script defer src="https://analytics.blackroad.io/beacon.js"></script>` is required in every Pixel Foundry surface

## Suggested copy guidelines

Every export gets a short, claims-safe caption. Patterns we use:

- "Build a playable world in your browser. No code."
- "Make a game in 60 seconds. Drag → paint → walk."
- "450 sprites · 25 walkable scenes · drag-to-paint world builder."
- "Sovereign tools. Built in browsers. Owned by you."
- "→ blackroad.io/foundry/"

Hashtags: `#pixelart #gamedev #indiegame #pixelgame #worldbuilding`

## What's forbidden

- Blurry / anti-aliased pixels in any export
- Colored text in HUD
- Inventing new color tokens not on `brand.blackroad.io`
- Any path containing `/Users/`, `file://`, `/Applications/` in published exports
- Tokens, secrets, API keys in any rendered text
- Internal IPs in any scene
- Unauthorized third-party characters / IP / copyrighted media
- Private user / customer data in any rendered label
- Provider names (Anthropic, OpenAI, Google, xAI) in any rendered text — use BlackRoad identity names only

## Acceptance test

Before any export ships:

- [ ] Pixel scaling is integer
- [ ] No blur / anti-alias
- [ ] HUD text is white/black only
- [ ] Brand colors match `brand.blackroad.io` tokens exactly
- [ ] Beacon script present
- [ ] No leak of local paths, tokens, internal IPs
- [ ] Copy is claims-safe
- [ ] Public-safe checkbox passes

---

*Pixel Foundry visual rules · 2026-04-27 · keep it crisp.*
