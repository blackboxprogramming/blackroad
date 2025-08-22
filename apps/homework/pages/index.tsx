import React, { useState, useEffect } from 'react';

interface Homework {
  id: number;
  title: string;
  description: string;
}

export default function HomeworkPortal() {
  const [homeworks, setHomeworks] = useState<Homework[]>([]);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');

  const fetchHomeworks = async () => {
    const res = await fetch('http://localhost:4000/api/homework');
    const data = await res.json();
    setHomeworks(data);
  };

  useEffect(() => {
    fetchHomeworks();
  }, []);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    await fetch('http://localhost:4000/api/homework', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, description })
    });
    setTitle('');
    setDescription('');
    fetchHomeworks();
  };

  return (
    <main style={{ padding: '2rem' }}>
      <h1>Homework Portal</h1>
      <form onSubmit={submit} style={{ marginBottom: '1rem' }}>
        <input
          value={title}
          onChange={e => setTitle(e.target.value)}
          placeholder="Title"
          required
        />
        <input
          value={description}
          onChange={e => setDescription(e.target.value)}
          placeholder="Description"
          required
        />
        <button type="submit">Add</button>
      </form>
      <ul>
        {homeworks.map(hw => (
          <li key={hw.id}>
            <strong>{hw.title}</strong>: {hw.description}
          </li>
        ))}
      </ul>
    </main>
  );
}
