import React, { useCallback, useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import axios from 'axios';
import './styles.css';

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api' });
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('annotation_access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

function App() {
  const [token, setToken] = useState(() => localStorage.getItem('annotation_access_token') || '');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [projects, setProjects] = useState([]);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const loadProjects = useCallback(async () => {
    if (!token) { setProjects([]); return; }
    setLoading(true);
    setError('');
    try {
      const result = await api.get('/projects/');
      const payload = result.data;
      setProjects(Array.isArray(payload) ? payload : (payload.results || []));
    } catch (err) {
      if (err.response?.status === 401) {
        localStorage.removeItem('annotation_access_token');
        setToken('');
        setError('Your session has expired. Sign in again.');
      } else {
        setError('Could not load projects. Check that the API is running.');
      }
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => { loadProjects(); }, [loadProjects]);

  async function signIn(event) {
    event.preventDefault();
    setError('');
    setNotice('');
    try {
      const result = await api.post('/auth/token/', { username, password });
      localStorage.setItem('annotation_access_token', result.data.access);
      setToken(result.data.access);
      setPassword('');
      setNotice('Signed in successfully.');
    } catch {
      setError('Sign-in failed. Check your username and password.');
    }
  }

  async function createProject(event) {
    event.preventDefault();
    if (!name.trim()) { setError('Enter a project name first.'); return; }
    setSaving(true);
    setError('');
    setNotice('');
    try {
      await api.post('/projects/', { name: name.trim(), description: description.trim() });
      setName('');
      setDescription('');
      setNotice('Project created.');
      await loadProjects();
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not create the project. Confirm your session and try again.');
    } finally {
      setSaving(false);
    }
  }

  function signOut() {
    localStorage.removeItem('annotation_access_token');
    setToken('');
    setProjects([]);
    setNotice('Signed out.');
    setError('');
  }

  return <div className="shell">
    <header>
      <div>
        <span className="eyebrow">AI DATASET OPERATIONS</span>
        <h1>Annotation Studio</h1>
        <p>Build reliable datasets with human annotation, review and measurable quality.</p>
      </div>
      {token
        ? <button className="secondary" onClick={signOut}>Sign out</button>
        : <span className="health">JWT authentication required</span>}
    </header>
    <main>
      <section className="hero">
        <div>
          <span className="eyebrow hero-eyebrow">WORKSPACE OVERVIEW</span>
          <h2>Your annotation projects</h2>
          <p>Manage datasets and keep annotation work organized from import to review.</p>
        </div>
        <div className="stats"><b>{projects.length}</b><span>Projects loaded</span></div>
      </section>

      {!token && <section className="panel auth-panel">
        <h3>Sign in to your workspace</h3>
        <p className="muted">Use an account created in the Django application.</p>
        <form className="form-grid" onSubmit={signIn}>
          <label>Username<input autoComplete="username" value={username} onChange={e => setUsername(e.target.value)} required /></label>
          <label>Password<input type="password" autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} required /></label>
          <button type="submit">Sign in</button>
        </form>
      </section>}

      {token && <section className="panel">
        <h3>Create a project</h3>
        <form className="form-grid" onSubmit={createProject}>
          <label>Project name<input value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Customer support intent labels" maxLength={160} required /></label>
          <label>Description<textarea value={description} onChange={e => setDescription(e.target.value)} placeholder="What data will be annotated and why?" rows={3} /></label>
          <button type="submit" disabled={saving}>{saving ? 'Creating…' : 'Create project'}</button>
        </form>
      </section>}

      {error && <p className="message error" role="alert">{error}</p>}
      {notice && <p className="message success" role="status">{notice}</p>}

      {token && <section className="panel">
        <div className="section-heading"><div><h3>Projects</h3><p className="muted">Only projects belonging to your account are shown.</p></div><button className="secondary" onClick={loadProjects} disabled={loading}>{loading ? 'Refreshing…' : 'Refresh'}</button></div>
        {loading ? <p className="muted">Loading projects…</p> : projects.length
          ? <div className="grid">{projects.map(project => <article key={project.id}>
              <span className="tag">PROJECT #{project.id}</span>
              <h4>{project.name}</h4>
              <p>{project.description || 'No description provided yet.'}</p>
              <small>{project.task_count ?? 0} tasks tracked</small>
            </article>)}</div>
          : <div className="empty"><strong>No projects yet</strong><p>Create your first project to start organizing datasets and annotation tasks.</p></div>}
      </section>}
    </main>
    <footer>Annotation Studio · Development workspace</footer>
  </div>;
}

createRoot(document.getElementById('root')).render(<App />);
