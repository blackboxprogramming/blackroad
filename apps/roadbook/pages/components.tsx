import React, { useState } from 'react';
import {
  Button,
  Input,
  Tabs,
  Drawer,
  Dialog,
  Toast,
  DataTable,
  Badge,
  Card,
  type Column,
} from '@blackroad/ui';

export default function ComponentsDemo() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [toastOpen, setToastOpen] = useState(false);

  const tabs = [
    { id: 'tab1', title: 'Tab One', content: <p>First tab content</p> },
    { id: 'tab2', title: 'Tab Two', content: <p>Second tab content</p> },
    { id: 'tab3', title: 'Tab Three', content: <p>Third tab content</p> },
  ];

  type Person = { name: string; role: string };
  const tableData: Person[] = [
    { name: 'Alice', role: 'Explorer' },
    { name: 'Bob', role: 'Guide' },
  ];

  const columns: Column<Person>[] = [
    { key: 'name', header: 'Name' },
    { key: 'role', header: 'Role' },
  ];

  return (
    <main style={{ padding: '2rem' }}>
      <h1>UI Component Showcase</h1>

      <section style={{ marginTop: '1.5rem' }}>
        <h2>Button & Toast</h2>
        <Button onClick={() => setToastOpen(true)}>Show Toast</Button>
        <Toast
          open={toastOpen}
          onClose={() => setToastOpen(false)}
          message="Hello from the toast!"
        />
      </section>

      <section style={{ marginTop: '1.5rem' }}>
        <h2>Input</h2>
        <Input label="Your Name" placeholder="Type your name" />
      </section>

      <section style={{ marginTop: '1.5rem' }}>
        <h2>Tabs</h2>
        <Tabs tabs={tabs} />
      </section>

      <section style={{ marginTop: '1.5rem' }}>
        <h2>Drawer</h2>
        <Button onClick={() => setDrawerOpen(true)}>Open Drawer</Button>
        <Drawer
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          title="Sample Drawer"
        >
          <p>This is the drawer content.</p>
        </Drawer>
      </section>

      <section style={{ marginTop: '1.5rem' }}>
        <h2>Dialog</h2>
        <Button onClick={() => setDialogOpen(true)}>Open Dialog</Button>
        <Dialog
          open={dialogOpen}
          onClose={() => setDialogOpen(false)}
          title="Example Dialog"
          footer={<Button onClick={() => setDialogOpen(false)}>Close</Button>}
        >
          <p>This dialog demonstrates the modal component.</p>
        </Dialog>
      </section>

      <section style={{ marginTop: '1.5rem' }}>
        <h2>DataTable</h2>
        <DataTable columns={columns} data={tableData} />
      </section>

      <section style={{ marginTop: '1.5rem' }}>
        <h2>Badge</h2>
        <Badge variant="accent">New</Badge>
      </section>

      <section style={{ marginTop: '1.5rem' }}>
        <h2>Card</h2>
        <Card>
          <p>This is a simple card component.</p>
        </Card>
      </section>
    </main>
  );
}
