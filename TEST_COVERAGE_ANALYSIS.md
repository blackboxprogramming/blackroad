# Test Coverage Analysis

## Current State: No Tests Exist

The BlackRoad monorepo currently has **zero test files, zero test configuration, and zero CI test execution**. No testing framework (Jest, Vitest, Mocha, Testing Library, Playwright, etc.) is installed in any workspace. The CI pipeline (`core-ci.yml`) contains only a placeholder: `echo "Add lint/test here"`.

This means every module described below has **0% test coverage**.

---

## Codebase Inventory

| Module | Location | Language | Lines | Test Files | Coverage |
|---|---|---|---|---|---|
| API server | `apps/api/index.js` | JS | 49 | 0 | 0% |
| Standalone server | `server_full.js` | JS | 44 | 0 | 0% |
| Homework portal | `apps/homework/pages/index.tsx` | TSX | 63 | 0 | 0% |
| RoadBook site | `apps/roadbook/pages/*.tsx` | TSX | ~135 | 0 | 0% |
| UI: Button | `packages/ui/src/components/Button.tsx` | TSX | 76 | 0 | 0% |
| UI: Input | `packages/ui/src/components/Input.tsx` | TSX | 53 | 0 | 0% |
| UI: Tabs | `packages/ui/src/components/Tabs.tsx` | TSX | 60 | 0 | 0% |
| UI: Badge | `packages/ui/src/components/Badge.tsx` | TSX | 61 | 0 | 0% |
| UI: Card | `packages/ui/src/components/Card.tsx` | TSX | 37 | 0 | 0% |
| UI: Dialog | `packages/ui/src/components/Dialog.tsx` | TSX | 85 | 0 | 0% |
| UI: Drawer | `packages/ui/src/components/Drawer.tsx` | TSX | 93 | 0 | 0% |
| UI: DataTable | `packages/ui/src/components/DataTable.tsx` | TSX | 92 | 0 | 0% |
| UI: Toast | `packages/ui/src/components/Toast.tsx` | TSX | 78 | 0 | 0% |

---

## Proposed Testing Strategy

### Priority 1 (High) — API Server Unit/Integration Tests

**Why:** The API layer (`apps/api/index.js` and `server_full.js`) is the highest-risk code. It handles user input, manages in-memory state, and bridges to external services. Bugs here affect every consumer.

**Recommended framework:** [Vitest](https://vitest.dev/) + [supertest](https://github.com/ladakh/supertest) for HTTP assertions.

**What to test:**

1. **`GET /api/health`** — returns `{ ok: true }` with status 200.
2. **`GET /api/homework`** — returns an empty array initially; returns items after POST.
3. **`POST /api/homework`** — with valid body creates a homework item and returns 201.
4. **`POST /api/homework`** — with missing `title` returns 400 with error message.
5. **`POST /api/homework`** — with missing `description` returns 400 with error message.
6. **`POST /api/homework`** — with empty body returns 400.
7. **CORS middleware** — `OPTIONS` requests return 200 with correct headers; `Access-Control-Allow-Origin` is `*`.
8. **`server_full.js` — `GET /api/hello`** — returns expected JSON.
9. **`server_full.js` — `GET /health`** — returns `{ status: 'ok', service: 'blackroad-api' }`.
10. **`server_full.js` — `POST /api/llm/chat`** — with missing/empty message returns 400; with valid message and unreachable upstream returns 502.

**Example test file location:** `apps/api/__tests__/api.test.ts`

---

### Priority 2 (High) — UI Component Library Tests

**Why:** The `@blackroad/ui` package is a shared dependency consumed by multiple apps. Regressions here cascade across the entire platform. The components contain variant logic, conditional rendering, keyboard event handling, and timer-based behavior that are all easy to break silently.

**Recommended framework:** Vitest + [@testing-library/react](https://testing-library.com/docs/react-testing-library/intro/) + jsdom.

**What to test per component:**

#### Button (`Button.tsx`)
- Renders children text.
- Applies correct CSS classes for each `variant` (primary, secondary, accent, neutral, info, danger, warning, success, outline).
- Applies correct CSS classes for each `size` (sm, md, lg).
- Defaults to `variant="primary"` and `size="md"` when no props are passed.
- Forwards native button attributes (`disabled`, `onClick`, `type`).
- Merges custom `className` with generated classes.

#### Input (`Input.tsx`)
- Renders an `<input>` element.
- Renders a `<label>` when the `label` prop is provided, and binds it via `htmlFor`.
- Does not render a `<label>` when `label` is omitted.
- Applies variant-specific border/ring classes (default, danger, success, warning).
- Forwards native input attributes (`placeholder`, `value`, `onChange`).

#### Tabs (`Tabs.tsx`)
- Renders all tab buttons with correct titles.
- Shows the first tab's content by default.
- Switches displayed content when a different tab button is clicked.
- Respects `defaultTabId` to show a specific tab initially.
- Applies active styling to the selected tab button.

#### Badge (`Badge.tsx`)
- Renders children.
- Applies variant-specific classes for all 8 variants.
- Applies size-specific classes (sm, md, lg).
- Defaults to `variant="primary"`, `size="md"`.

#### Card (`Card.tsx`)
- Renders children.
- Applies variant-specific classes (plain, outlined, elevated).
- Defaults to `variant="plain"`.
- Merges custom `className`.

#### Dialog (`Dialog.tsx`)
- Renders children and title when `open` is `true`.
- Calls `onClose` when the Escape key is pressed.
- Calls `onClose` when the backdrop overlay is clicked.
- Renders the `footer` slot when provided.
- Sets `aria-modal="true"` and `role="dialog"` for accessibility.
- Applies visibility/pointer-events classes based on `open` state.

#### Drawer (`Drawer.tsx`)
- Renders children when `open` is `true`.
- Renders the `title` in a header when provided.
- Calls `onClose` when the backdrop is clicked.
- Applies correct positioning classes for each `side` (left, right, top, bottom).
- Applies correct transform classes for open/closed states.

#### DataTable (`DataTable.tsx`)
- Renders column headers from the `columns` prop.
- Renders the correct number of rows from the `data` prop.
- Uses `col.render` custom renderer when provided.
- Falls back to `String(row[col.key])` when no renderer is given.
- Applies column alignment classes (left, center, right).
- Renders an empty body gracefully when `data` is `[]`.

#### Toast (`Toast.tsx`)
- Displays the `message` text when `open` is `true`.
- Calls `onClose` after `duration` milliseconds (use fake timers).
- Does not auto-dismiss when `duration` is `0`.
- Calls `onClose` when the close button is clicked.
- Applies variant-specific background classes (info, success, warning, danger).
- Has `role="status"` for accessibility.

**Example test file location:** `packages/ui/src/components/__tests__/Button.test.tsx` (and similar for each component).

---

### Priority 3 (Medium) — Homework Portal Component Tests

**Why:** The homework page (`apps/homework/pages/index.tsx`) contains client-side fetching, form submission, and list rendering logic. These are the primary user interactions.

**Recommended framework:** Vitest + @testing-library/react + [msw](https://mswjs.io/) (Mock Service Worker) for API mocking.

**What to test:**

1. **Initial render** — fetches homework from the API and displays items.
2. **Empty state** — renders an empty `<ul>` when API returns `[]`.
3. **Form submission** — calls `POST /api/homework` with form field values, then re-fetches the list.
4. **Form field clearing** — title and description inputs are cleared after successful submission.
5. **Error state** — handles fetch failure gracefully (currently unhandled — this test would expose the gap).

**Example test file location:** `apps/homework/__tests__/HomeworkPortal.test.tsx`

---

### Priority 4 (Medium) — RoadBook Page Tests

**Why:** The roadbook app has mostly static content, but testing that pages render without crashing and that navigation links are correct prevents regressions.

**What to test:**

1. **Home page** — renders "Welcome to RoadBook" heading and navigation links.
2. **Components demo page** — renders all component sections; interactive state (drawer/dialog/toast toggles) works.
3. **`_app.tsx`** — renders the passed `Component` with `pageProps`.

**Example test file location:** `apps/roadbook/__tests__/pages.test.tsx`

---

### Priority 5 (Lower) — End-to-End Tests

**Why:** E2E tests would validate the full stack (API + frontend) working together. Since the homework portal makes real HTTP calls to the API, E2E tests catch integration issues that unit tests miss.

**Recommended framework:** [Playwright](https://playwright.dev/)

**What to test:**

1. Start the API server, navigate to the homework portal, verify the page loads.
2. Submit a homework item through the form, verify it appears in the list.
3. Verify the RoadBook documentation site renders and navigation works.

---

### Priority 6 (Lower) — Design Token Validation

**Why:** `blackroad/design-tokens.json` defines the shared design language. A schema test would catch invalid tokens before they reach components.

**What to test:**

1. The JSON file is valid and parseable.
2. Required color keys exist (primary, secondary, accent, etc.).
3. Font sizes and weights are defined.
4. Border radius values are present.

---

## Infrastructure Recommendations

### 1. Install a test runner in each workspace

For the UI package and Next.js apps, **Vitest** is the best fit — it shares Vite's transform pipeline, has native TypeScript/JSX support, and is faster than Jest for this stack.

```
# Root or per-workspace
pnpm add -D vitest @testing-library/react @testing-library/jest-dom jsdom
```

For the API server (plain JS/Express):

```
pnpm add -D vitest supertest
```

### 2. Add `test` scripts to each `package.json`

```json
"scripts": {
  "test": "vitest run",
  "test:watch": "vitest"
}
```

### 3. Add a root-level test command

```json
"scripts": {
  "test": "pnpm -r run test"
}
```

### 4. Update CI to run tests

Replace the placeholder in `.github/workflows/core-ci.yml`:

```yaml
- name: Install dependencies
  run: pnpm install --frozen-lockfile
- name: Run tests
  run: pnpm -r run test
```

### 5. Add coverage reporting

```json
"scripts": {
  "test:coverage": "vitest run --coverage"
}
```

Configure a coverage threshold to prevent regressions (e.g., 80% for the UI package).

---

## Summary of Gaps by Risk

| Risk Level | Area | Gap |
|---|---|---|
| Critical | API endpoints | No validation that endpoints return correct status codes and bodies |
| Critical | API input validation | `POST /api/homework` validation logic is untested |
| Critical | LLM chat bridge | Error handling for unreachable upstream is untested |
| High | UI component variants | 9 components x multiple variants = dozens of untested CSS class paths |
| High | UI interactive behavior | Dialog Escape key, Toast auto-dismiss timer, Tabs switching, Drawer backdrop click |
| High | UI accessibility | `aria-modal`, `role="dialog"`, `role="status"`, label binding — none verified |
| Medium | Homework portal | Fetch-on-mount, form submission, list rendering all untested |
| Medium | CORS middleware | Cross-origin headers never verified |
| Low | Static pages | RoadBook pages could silently break on dependency updates |
| Low | Design tokens | No schema validation on the shared token file |
| Low | CI pipeline | No test execution in CI; regressions can be merged freely |
