# OfficeRoad ⇄ Pixel Foundry Integration

**OfficeRoad role:** consumes Pixel Foundry **rooms** as visible workspaces.
**Pixel Foundry role:** room layout production for OfficeRoad.

Canon doc: `docs/products/blackboard/PIXEL_FOUNDRY_CANON.md`

---

## Important — consent and access first

> **OfficeRoad is not surveillance.** OfficeRoad is **visible work with consent, roles, and access controls.**

Every Pixel Foundry → OfficeRoad room export must:

- Carry an `accessControls` block declaring who can view / interact
- Carry a `consentNotice` rendered in-room
- Default to private until an explicit publish step
- Never embed real-time location, device IDs, or other surveilling signals

## What flows from Pixel Foundry → OfficeRoad

A Pixel Foundry room export includes:

- **office room layout** (40 × 25 tile grid by default)
- **desks** (with seat positions, name plates, status)
- **meeting rooms** (with door warps to subrooms)
- **team zones** (color-coded floor regions)
- **agent stations** (chairs designated for specific agents/identities)
- **task boards** (interactive prop → opens task dialog)
- **file cabinets** (interactive prop → opens drive view)
- **status signs** (live text from BlackBoard)
- **doors / routes to products** (warp tiles labeled with destination)
- **room metadata** (`title`, `team`, `purpose`, `consent`, `access`)

## Existing scene examples that fit OfficeRoad

| Foundry scene | OfficeRoad use |
|---|---|
| Office Floor (`pixel-office.html`) | Pixel Office HQ — main floor |
| BlackRoad Lab (`blackroad-lab.html`) | R&D lab |
| Memorial Hospital · 4th Floor | template for "Support room" / nurse's station style |
| Fire Station — Engine 27 | template for "Command center" / "operations room" |
| Classroom 7 | template for "Studio" / "classroom" / training |
| A Quiet House | template for remote/work-from-home rooms |

Plus rooms built in the **World Builder** explicitly tagged `room` instead of `scene`.

## Room schema (extends `PixelFoundryScene`)

```ts
interface OfficeRoadRoom extends PixelFoundryScene {
  team: string;                 // 'engineering' | 'support' | 'design' | ...
  purpose: string;              // 'standup' | 'focus' | 'review' | ...
  consent: {
    notice: string;             // displayed in-room
    capturedFrom: string[];     // ['admin-jane', 'agent-cecilia']
    capturedAt: string;         // iso timestamp
  };
  access: {
    public: boolean;
    allowedRoles: string[];     // ['admin', 'agent', 'guest']
    allowedUsers: string[];
  };
  desks: Desk[];
  agentStations: AgentStation[];
  doors: Door[];                // warp tiles to other rooms / products
}

interface Desk {
  id: string;
  x: number; y: number;
  occupant: string | null;      // user id or null
  nameplate: string;
  status: 'available' | 'busy' | 'away' | 'do-not-disturb';
}

interface AgentStation {
  id: string;
  x: number; y: number;
  agent: string;                // 'cecilia' | 'cordelia' | 'gaia' | 'gematria' | 'lucidia'
  state: 'present' | 'away';
}

interface Door {
  x: number; y: number;
  warp: string;                 // 'product:roadpay' | 'room:standup' | 'home'
  label: string;
}
```

## Tying into the Identity Sovereignty Layer

Per memory `project_identity_sovereignty.md`: the 5 BlackRoad identities (Cecilia, Cordelia, Gaia, Gematria, Lucidia) get **agent stations** in OfficeRoad rooms. Provider names never appear — only the BlackRoad-canonized identity names. The room renderer pulls names from the sealed registry (`identity/registry.js`) — no provider leaks.

## Door warps to other products

Each door in an OfficeRoad room can warp to:

- another OfficeRoad room
- a RoadWorld scene
- a BlackBoard board
- a product page (`product:roadpay`, `product:roadbook`, etc.)
- the user's home / dashboard

## Export contract (TODO — implement)

```ts
function sendToOfficeRoad(room: OfficeRoadRoom): OfficeRoadPackage {
  // Validate: consent notice present, access controls set, no PII in labels
  validateConsent(room);
  validateAccess(room);
  validateNoPII(room);
  return {
    schemaVersion: 1,
    room,
    sprites: collectSprites(room),
    bundleAt: nowIso(),
  };
}
```

## BRTODO

- P1: implement `sendToOfficeRoad()` with consent + access validation
- P1: define `OfficeRoadRoom` schema (above)
- P1: build agent-station renderer that reads from identity registry
- P2: build door-warp routing layer
- P2: add live status feed to status signs (from BlackBoard)
- P2: build standup-room template that auto-arranges agent stations

---

*OfficeRoad ⇄ Pixel Foundry · 2026-04-27 · consent first.*
