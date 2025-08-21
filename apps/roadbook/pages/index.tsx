import React from 'react';
import Link from 'next/link';

export default function Home() {
  return (
    <main style={{ padding: '2rem' }}>
      <h1>Welcome to RoadBook</h1>
      <p>Hello World</p>
      <p>This is the documentation site for the BlackRoad ecosystem.</p>
      <nav>
        <ul>
          <li>
            <Link href="/docs/intro">Introduction</Link>
          </li>
          <li>
            <Link href="/docs/getting-started">Getting Started</Link>
          </li>
        </ul>
      </nav>
    </main>
  );
}
