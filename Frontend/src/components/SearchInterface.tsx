import { useState } from 'react';
import '../styles/SearchInterface.css';

// Define the Electron API for TypeScript
declare global {
  interface Window {
    electronAPI?: {
      openFile: (filePath: string) => Promise<{ success: boolean, error?: string }>;
    };
  }
}

interface SearchResult {
  filename: string;
  path: string;
  extension: string;
}

interface SearchResultsMap {
  [score: string]: SearchResult;
}

const SearchInterface = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResultsMap>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch(`http://localhost:5000/search/${encodeURIComponent(query)}`);
      
      if (!response.ok) {
        throw new Error('Search failed. Please try again.');
      }
      
      const data = await response.json();
      setResults(data);
    } catch (err) {
      console.error('Search error:', err);
      setError('Failed to fetch results. Is the backend server running?');
      setResults({});
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const handleOpenFile = async (filePath: string) => {
    if (window.electronAPI) {
      try {
        const result = await window.electronAPI.openFile(filePath);
        if (!result.success) {
          console.error('Failed to open file:', result.error);
        }
      } catch (err) {
        console.error('Error opening file:', err);
      }
    } else {
      console.error('Electron API not available');
    }
  };

  return (
    <div className="search-container">
      <h1>File Retrieval Engine</h1>
      
      <div className="search-box">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Search for files..."
          className="search-input"
        />
        <button 
          onClick={handleSearch}
          disabled={loading}
          className="search-button"
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>
      
      {error && <p className="error-message">{error}</p>}
      
      <div className="results-container">
        {Object.keys(results).length > 0 ? (
          <div className="results-list">
            <h2>Search Results</h2>
            {Object.entries(results).map(([score, result], index) => (
              <div key={index} className="result-card">
                <div className="result-header">
                  <h3 className="file-name">{result.filename}</h3>
                  <button 
                    className="open-button"
                    onClick={() => handleOpenFile(result.path)}
                  >
                    Open
                  </button>
                </div>
                <p className="file-path">Path: {result.path}</p>
                <p className="file-type">Type: {result.extension.toUpperCase()}</p>
                <p className="file-score">Relevance Score: {parseFloat(score).toFixed(4)}</p>
              </div>
            ))}
          </div>
        ) : !loading && query ? (
          <p className="no-results">No results found</p>
        ) : null}
      </div>
    </div>
  );
};

export default SearchInterface;