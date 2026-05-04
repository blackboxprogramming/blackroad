# Pixel Foundry — Canon

**Canonical name:** Pixel Foundry
**Primary parent:** BlackBoard
**Status:** BlackBoard tool / surface · NOT a separate active product road

---

## CANON LINE

> **Pixel Foundry is BlackRoad's browser-native pixel asset and scene maker for social graphics, sprite sheets, rooms, maps, and walkable worlds.**

### Alternate lines

- Make the world before you enter it.
- Pixel art, scenes, and worlds — built in the browser.
- The sprite sheet becomes the room. The room becomes the road.
- Build a playable world in your browser. No code.

---

## Positioning

### Pixel Foundry IS

- a **BlackBoard creative tool**
- a **RoadWorld scene pipeline**
- an **OfficeRoad room builder**
- a **RoadShow demo / showcase source**
- a **brand / social asset generator**
- a browser-native pixel studio
- a downloadable graphic generator
- a sprite sheet maker
- a walkable-scene generator

### Pixel Foundry IS NOT

- a separate active product road
- a replacement for BlackBoard
- a replacement for RoadWorld
- a replacement for OfficeRoad
- a random mockup page
- a private-only tool
- a one-off experiment

---

## SECTION 1 — What exists now

### Infographics / graphics surface (`infographics.html`)

- hero cards (1200×630 — Twitter / OG)
- stories (1080×1920 — Instagram / TikTok)
- Instagram squares (1080×1080) — sprite sheet gallery
- posters (1080×1350 — print / Instagram portrait)
- banners (1500×500 — Twitter header / GitHub cover)
- downloadable PNGs (one click)
- suggested copy blocks beside every export
- BlackRoad gradient route strips
- black background + pixel assets + neon route accents

### Interactive / walkable scenes (`scenes-interactive/`)

| Scene | File |
|---|---|
| Fire Station — Engine 27 | `fire-station.html` |
| Sunshine Preschool | `preschool.html` |
| Dino Valley | `dino-valley.html` |
| Sunny Cove Beach | `beach.html` |
| Drive-In | `drive-in.html` |
| Daycare | `daycare.html` |
| A Quiet House | `house.html` |
| Memorial Hall (Museum) | `museum.html` |
| Memorial Hospital · 4th Floor | `hospital.html` |
| Roadside Station 24 (Gas) | `gas-station.html` |
| Cozy House — Felix & Oliver | `cozy-house-felix-oliver.html` |
| Bus Stop BR-07 | `bus-stop.html` |
| BlackRoad Lab | `blackroad-lab.html` |
| Office Floor | `pixel-office.html` |
| Town & Lake | `pixel-town.html` |
| Subway Car | `subway-car.html` |
| City Skyline | `city-skyline.html` |
| Candy Land | `candy-land.html` |
| Zen Garden | `zen-garden.html` |
| Deepsea Reef | `deepsea-reef.html` |
| Pirate Ship Deck | `pirate-ship-deck.html` |
| Haunted Manor | `haunted-manor.html` |
| Classroom 7 | `amundson-classroom-7.html` |
| World Builder (drag-to-paint) | `world-builder.html` |

### Scene UI conventions

- WASD walk (and ↑↓←→)
- E to interact
- Shift sprint
- Status / route metadata (top-right)
- Scene title (top-left)
- Bottom-right stamp: `BlackRoad OS · …`
- White / black HUD (brand rule — no colored text in HUD)

### Asset library — sprite catalog (`catalog/`)

- 21 batches shipped (F001 — F725, ~75% to the 1,000 goal)
- 32 × 32 px native, integer-scale-clean
- Per-batch self-contained browser HTML with palette + items + filter UI

### Asset style

- pixel sprites
- simple walkable objects
- playful worlds
- product-ready scenes
- bright colors INSIDE black/white OS frame
- downloadable / exportable social collateral

---

## SECTION 2 — BlackBoard integration

### BlackBoard role

Pixel Foundry is the **pixel-art and scene creation tool inside BlackBoard.**

### BlackBoard surfaces (target)

BlackBoard should expose Pixel Foundry as cards / actions:

- Create Pixel Asset
- Create Sprite Sheet
- Create Scene
- Create Social Banner
- Create OG Image
- Create Room
- Export PNG
- Export Scene JSON
- Send to RoadWorld
- Send to OfficeRoad
- Send to RoadShow

### Asset shape

BlackBoard treats Pixel Foundry outputs as creative assets carrying:

- `assetId`
- `title`
- `type` (`sprite | sheet | scene | room | social`)
- `dimensions` (`w × h`)
- `palette`
- `sourceScene`
- `exportFormat` (`png | sceneJson | roadworldPackage`)
- `usageNotes`
- `publicSafe` (bool)
- `relatedRoad`

---

## SECTION 5 — RoadShow integration

### Role

RoadShow can showcase weird / cool Pixel Foundry scenes as demos and prototypes.

### Examples

Dino Valley · Beach · Fire Station · Preschool · Drive-In · odd mini-games · old mockup rooms · Easter-egg scenes · prototype worlds.

### Labels

`Demo` · `Prototype` · `Easter Egg` · `Old Mockup` · `Playable Scene` · `Archived Cool Thing`.

### Safe phrase (UI footnote)

> RoadShow contains experiments and prototypes. Items may be incomplete, unstable, or purely for demonstration.

---

## SECTION 6 — RoadStream integration

### Role

Pixel Foundry can create channel art and stream collateral for RoadStream:

- channel cards
- show posters
- thumbnail frames
- lower thirds
- TV-guide graphics
- stream room backgrounds (Drive-In etc.)
- creator channel art

### Safe note

> RoadStream media must use embedded, linked, owned, licensed, or authorized media only where rights and platform terms allow.

---

## SECTION 7 — Brand / social collateral

Pixel Foundry generates:

- Twitter / X headers
- GitHub covers
- OG images
- Instagram squares
- TikTok / Instagram vertical stories
- posters
- product cards
- launch graphics
- sprite sheet previews
- campaign frames

### Export sizes

| Use | Size |
|---|---|
| OG image / Twitter card | 1200 × 630 |
| Twitter header | 1500 × 500 |
| GitHub cover | 1280 × 640 (TBD — confirm) |
| Instagram square | 1080 × 1080 |
| Story / Reel vertical | 1080 × 1920 |
| Poster | 1080 × 1350 (digital) · print TBD |
| Custom | full-resolution canvas |

### Every export includes

- download PNG button
- suggested copy block
- route the asset belongs to
- public-safe check

---

## SECTION 8 — File / app structure (current)

### Current paths

```
packages/pixel-foundry/
  index.html                           # foundry overview / nav
  infographics.html                    # Infographic Studio
  reference-board.html                 # sprite reference grid
  transit-stop.html                    # legacy demo scene
  catalog/                             # 21 batch HTML browsers
    index.html
    pixel-furniture-001-025.html
    ...
    pixel-furniture-701-725.html
  scenes-interactive/                  # 24 walkable scene HTMLs
    world-builder.html                 # ★ drag-to-paint scene maker
    fire-station.html
    preschool.html
    dino-valley.html
    beach.html
    drive-in.html
    daycare.html
    ... (all listed in Section 1)
  external/                            # downloaded reference asset packs (not BR-owned)
  lib/                                 # 86 sprite modules (older, partly superseded by catalog)
  assets/                              # currently empty
  manifest.json                        # 10,000-sprite phase tracker
```

### Recommended future structure (TODO — do not break working pages)

```
apps/blackboard/pixel-foundry/
  index.html
  studio.html
  infographics.html
  scenes/
  scenes-interactive/
  sprites/
  exports/
  README.md

packages/pixel-foundry/
  engine/
  sprites/
  palettes/
  scene-schema/
  export-utils/
```

---

## SECTION 9 — Pixel Foundry scene schema (first pass)

### `PixelFoundryScene`

```ts
{
  id: string,                   // 'beach-001'
  title: string,                // 'Sunny Cove Beach'
  slug: string,                 // 'beach'
  category: string,             // 'outdoor'
  theme: string,                // 'summer'
  parentRoad: string,           // 'roadworld' | 'officeroad' | 'roadshow' | ...
  exportTargets: string[],      // ['roadworldPackage', 'png']
  canvasWidth: number,          // 1280
  canvasHeight: number,         // 800
  tileSize: number,             // 32
  palette: Record<string,string>,
  spritesheet: string,          // path or asset id
  layers: Layer[],
  objects: Object[],
  collision: number[][],
  interactions: Interaction[],
  spawn: { x, y },
  metadata: { createdAt, author, version, license },
  safety: { publicSafe: bool, notes: string },
  credits: string[]
}
```

### `Object`

```ts
{
  id: string,
  type: string,               // 'tree' | 'bench' | 'house' | 'npc' | ...
  x: number,
  y: number,
  width: number,
  height: number,
  sprite: string,             // sprite key
  collidable: bool,
  interactive: bool,
  label: string,              // 'Bench — Mom went for coffee'
  action: string,             // 'open-dialog' | 'warp:beach' | null
  relatedRoad: string         // optional cross-road link
}
```

### `Export`

```ts
{
  png: string,                // url or buffer
  sceneJson: PixelFoundryScene,
  roadworldPackage: ZipUrl,
  officeroadRoom: RoomDescriptor,
  socialCard: { size, png },
  poster: { size, png }
}
```

---

## SECTION 10 — UX next steps

Top bar: Pixel Foundry title · current route · current mode · export button.

### Modes

- Infographics
- Sprite Sheet
- Scene Builder
- Interactive Scene
- Social Export
- Room Export

### Controls

- choose template
- choose scene
- add sprite
- drag-to-place
- edit text
- choose export size
- download PNG
- export scene JSON
- send to RoadWorld
- send to OfficeRoad
- send to RoadShow

---

## SECTION 11 — Public safety checklist

Before publishing / exporting any Pixel Foundry asset:

- [ ] no `file://` paths in exports
- [ ] no `/Users/alexa/` or any home-dir path
- [ ] no `/Applications/` paths
- [ ] no private repo names
- [ ] no private screenshots
- [ ] no tokens / secrets / API keys
- [ ] no internal IPs
- [ ] no unauthorized third-party characters / assets
- [ ] no copyrighted media unless authorized
- [ ] no private user / customer data
- [ ] route must be HTTPS if public
- [ ] suggested copy is claims-safe

---

## SECTION 12 — Visual rules (summary)

See `docs/brand/PIXEL_FOUNDRY_VISUAL_RULES.md` for the full spec. Summary:

- pixel art crisp · integer scaling preserved · no blurry exports
- keep black / white OS frame where appropriate
- bright colors allowed INSIDE the pixel world
- neon route strip = brand accent on social cards (gradient: orange → pink → magenta → purple → blue → cyan)
- readable mono labels (JetBrains Mono)
- exact export dimensions
- short captions
- suggested copy beside every export

---

## SECTION 13 — Acceptance test (manual checks)

- [ ] Infographics page opens (`infographics.html`)
- [ ] Hero card / banner / story / square / poster export buttons all download a PNG
- [ ] Suggested copy visible beside each card
- [ ] Fire Station scene opens
- [ ] Preschool scene opens
- [ ] Dino Valley scene opens
- [ ] Beach scene opens
- [ ] WASD / arrow controls work
- [ ] E interact + Shift sprint hints visible
- [ ] No local / private paths leak inside exported images
- [ ] No private repo names appear in public copy
- [ ] Pixel Foundry is documented as BlackBoard tool, not new active product

---

## SECTION 14 — BRTODO

### P0

- Document Pixel Foundry canon and integrations (this doc + the 3 sibling integration docs)

### P1

- Add Pixel Foundry card to BlackBoard
- Add Pixel Foundry output links to RoadWorld and OfficeRoad docs
- Create `PixelFoundryScene` JSON schema
- Create public-safe export checklist in UI
- Normalize routes for public deployment (`blackroad.io/foundry/`, `/blackboard/pixel-foundry/`, etc.)

### P2

- Add drag-to-paint scene builder (✅ partially done — `world-builder.html`)
- Add send-to-RoadWorld export
- Add send-to-OfficeRoad room export
- Add RoadShow showcase feed
- Add RoadStream channel-art template
- Finish 1,000-sprite catalog (currently 525 / 1,000 — batches 19-21 + 22 farm pending)

---

## Commit

```
docs(products): canonize Pixel Foundry scene and asset pipeline
```

After commit, update:

- `[MEMORY]` — Pixel Foundry is BlackBoard tool/surface, feeds RoadWorld + OfficeRoad
- `[CODEX]` — link this canon doc
- `[PRODUCTS]` — add Pixel Foundry as BlackBoard surface (NOT a new active road)
- `[BRTODO]` — copy P0/P1/P2 list above
- `[COLLAB]` — note canonization
- `[ROADTRIP]` — note product placement decision

---

*Pixel Foundry · canonized 2026-04-27 · BlackRoad OS, Inc.*
