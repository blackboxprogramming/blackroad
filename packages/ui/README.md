# BlackRoad UI Library

This package provides a collection of reusable, accessible UI primitives
built with **React** and **Tailwind CSS**.  It is designed to
standardize the look and feel of applications in the BlackRoad
ecosystem by consuming the shared [design tokens](../../blackroad/design-tokens.json).

## Installation

First install the package as a dependency in your project:

```bash
pnpm add @blackroad/ui
# or
yarn add @blackroad/ui
# or
npm install @blackroad/ui
```

You'll also need to install `react` and `react-dom` if they are not
already present as peer dependencies.

## Usage

Import the components you need from the library.  The package
automatically includes its Tailwind styles when you import the
generated CSS file from `dist/styles.css`.

```tsx
import { Button, Input, Tabs, Drawer, Dialog, Toast, DataTable, Badge, Card } from '@blackroad/ui';
import '@blackroad/ui/dist/styles.css';

function Example() {
  return (
    <div className="space-y-4">
      <Button variant="primary">Primary Button</Button>
      <Input label="Email" placeholder="you@example.com" />
      <Badge variant="success">Live</Badge>
      <Card variant="elevated">Card content</Card>
    </div>
  );
}
```

See the individual component files in [`src/components`](./src/components)
for all available props and usage examples.

## Development

This package is authored in TypeScript and compiled to JavaScript via
`tsc`.  To build the package locally run:

```bash
pnpm --filter @blackroad/ui build
```

This will generate compiled JavaScript in `dist/` and process the
Tailwind styles into `dist/styles.css`.

## Storybook

To preview the components in isolation you can integrate this library
into a Storybook instance in your consuming application.  Storybook
configuration is not included in this package to keep the build
lightweight, but the components are designed to work seamlessly in
Storybook.
