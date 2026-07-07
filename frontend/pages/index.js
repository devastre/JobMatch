import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/router';

export default function Home() {
  const router = useRouter();
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState(''); // 'pending', 'done', 'error'
  const [jobs, setJobs] = useState([]);
  const [locationFilter, setLocationFilter] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const fileInputRef = useRef(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) router.push('/login');
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    router.push('/login');
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const uploadCV = async () => {
    if (!file) return;
    setStatus('pending');
    setErrorMessage('');
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const token = localStorage.getItem('token') || '';
      
      const uploadRes = await fetch('http://localhost:8001/api/cv/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });
      
      if (!uploadRes.ok) {
        const errData = await uploadRes.json().catch(() => ({}));
        throw new Error(errData.detail || 'Upload failed');
      }
      const cvData = await uploadRes.json();
      
      const searchRes = await fetch('http://localhost:8001/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ cv_id: cvData.id })
      });
      
      if (!searchRes.ok) {
        const errData = await searchRes.json().catch(() => ({}));
        throw new Error(errData.detail || 'Search failed');
      }
      const searchData = await searchRes.json();
      
      const pollInterval = setInterval(async () => {
        try {
          const res = await fetch(`http://localhost:8001/api/search/${searchData.search_id}/results`);
          if (res.ok) {
            const data = await res.json();
            if (data.status === 'completed') {
              clearInterval(pollInterval);
              setStatus('done');
              setJobs(data.results);
            } else if (data.status === 'failed') {
              clearInterval(pollInterval);
              setStatus('error');
              setErrorMessage(data.error || 'Search failed');
            }
          } else {
            const errorData = await res.json().catch(() => ({}));
            clearInterval(pollInterval);
            setStatus('error');
            setErrorMessage(errorData.detail || 'Search failed');
          }
        } catch (err) {
          clearInterval(pollInterval);
          setStatus('error');
          setErrorMessage(err.message || 'Network error during polling');
        }
      }, 2000);
      
    } catch (error) {
      console.error(error);
      setStatus('error');
      setErrorMessage(error.message || 'An unexpected error occurred');
    }
  };

  const filteredJobs = jobs
    .filter(job => job.location && job.location.toLowerCase().includes(locationFilter.toLowerCase()))
    .sort((a, b) => b.score - a.score);

  return (
    <div style={{ padding: '2rem', fontFamily: 'sans-serif', maxWidth: '800px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h1 style={{ margin: 0 }}>JobMatch Dashboard</h1>
        <button onClick={handleLogout} style={{ padding: '0.4rem 1rem', cursor: 'pointer', backgroundColor: '#e53935', color: 'white', border: 'none', borderRadius: '4px' }}>
          Logout
        </button>
      </div>
      
      <div 
        onDragOver={handleDragOver} 
        onDrop={handleDrop}
        style={{
          border: '2px dashed #ccc',
          padding: '2rem',
          textAlign: 'center',
          marginBottom: '1rem',
          cursor: 'pointer'
        }}
        onClick={() => fileInputRef.current.click()}
      >
        {file ? <p>Selected: {file.name}</p> : <p>Drag and drop your CV here, or click to select</p>}
        <input 
          type="file" 
          ref={fileInputRef} 
          onChange={handleFileSelect} 
          style={{ display: 'none' }} 
          accept=".pdf,.doc,.docx"
        />
      </div>
      
      <button 
        onClick={(e) => { e.stopPropagation(); uploadCV(); }} 
        disabled={!file || status === 'pending'}
        style={{ padding: '0.5rem 1rem', fontSize: '1rem', cursor: 'pointer' }}
      >
        Upload & Match
      </button>

      <div style={{ marginTop: '1rem' }}>
        <strong>Status: </strong>
        <span style={{
          color: status === 'pending' ? 'orange' : status === 'done' ? 'green' : status === 'error' ? 'red' : 'black'
        }}>
          {status || 'Waiting for upload'}
        </span>
      </div>

      {status === 'error' && errorMessage && (
        <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: '#ffebee', color: '#c62828', borderRadius: '4px' }}>
          <strong>Error:</strong> {errorMessage}
        </div>
      )}

      {status === 'done' && (
        <div style={{ marginTop: '2rem' }}>
          <h2>Matched Job Offers</h2>
          <input 
            type="text" 
            placeholder="Filter by location..." 
            value={locationFilter}
            onChange={(e) => setLocationFilter(e.target.value)}
            style={{ padding: '0.5rem', marginBottom: '1rem', width: '100%' }}
          />
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {filteredJobs.map(job => (
              <div key={job.id} style={{ border: '1px solid #eee', padding: '1rem', borderRadius: '8px' }}>
                <h3 style={{ margin: '0 0 0.5rem 0' }}>{job.title} - {job.location}</h3>
                <p style={{ margin: '0 0 0.5rem 0' }}><strong>Company:</strong> {job.company}</p>
                <p style={{ margin: '0 0 0.5rem 0' }}><strong>Score:</strong> {job.score}%</p>
                <p style={{ margin: 0 }}><strong>Matched Keywords:</strong> {job.keywords ? job.keywords.join(', ') : 'None'}</p>
              </div>
            ))}
            {filteredJobs.length === 0 && <p>No jobs found for this location.</p>}
          </div>
        </div>
      )}
    </div>
  );
}