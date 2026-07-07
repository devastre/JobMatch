import { useState, useRef, useEffect } from 'react';

export default function Home() {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState(''); // 'pending', 'done', 'error'
  const [jobs, setJobs] = useState([]);
  const [locationFilter, setLocationFilter] = useState('');
  const fileInputRef = useRef(null);

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
    
    // Simulate upload
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Simulate polling for parsing and searching
    const pollInterval = setInterval(() => {
      const random = Math.random();
      if (random > 0.7) {
        clearInterval(pollInterval);
        setStatus('done');
        setJobs([
          { id: 1, title: 'Frontend Developer', location: 'New York', score: 95, keywords: ['React', 'JavaScript'] },
          { id: 2, title: 'Backend Developer', location: 'San Francisco', score: 80, keywords: ['Node.js'] },
          { id: 3, title: 'Fullstack Engineer', location: 'New York', score: 88, keywords: ['React', 'Node.js'] },
          { id: 4, title: 'UI/UX Designer', location: 'Remote', score: 45, keywords: ['Figma'] }
        ]);
      } else if (random < 0.1) {
        clearInterval(pollInterval);
        setStatus('error');
      }
    }, 1000);
  };

  const filteredJobs = jobs
    .filter(job => job.location.toLowerCase().includes(locationFilter.toLowerCase()))
    .sort((a, b) => b.score - a.score);

  return (
    <div style={{ padding: '2rem', fontFamily: 'sans-serif', maxWidth: '800px', margin: '0 auto' }}>
      <h1>JobMatch Dashboard</h1>
      
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
                <p style={{ margin: '0 0 0.5rem 0' }}><strong>Score:</strong> {job.score}%</p>
                <p style={{ margin: 0 }}><strong>Matched Keywords:</strong> {job.keywords.join(', ')}</p>
              </div>
            ))}
            {filteredJobs.length === 0 && <p>No jobs found for this location.</p>}
          </div>
        </div>
      )}
    </div>
  );
}