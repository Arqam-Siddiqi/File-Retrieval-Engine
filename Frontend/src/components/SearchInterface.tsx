import { useState, useRef } from 'react';
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

// Updated interface to reflect the new response format
interface SearchResultsMap {
  [score: string]: SearchResult[];
}

const SearchInterface = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResultsMap>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

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

  const handleImageSearch = async () => {
    if (!selectedImage) return;
    
    setLoading(true);
    setError('');
    
    try {
      const formData = new FormData();
      formData.append('image', selectedImage);
      
      const response = await fetch('http://localhost:5000/search-by-image', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error('Image search failed. Please try again.');
      }
      
      const data = await response.json();
      console.log('Image search results:', data);
      setResults(data);
    } catch (err) {
      console.error('Image search error:', err);
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

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedImage(file);
      
      // Create preview
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
      
      // Clear text search
      setQuery('');
    }
  };

  const handleImageUploadClick = () => {
    fileInputRef.current?.click();
  };

  const clearImage = () => {
    setSelectedImage(null);
    setImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="search-container">
      <div className="app-title">
        <h1>File Retrieval Engine</h1>
        <p className="subtitle">Search by text or image</p>
      </div>
      
      <div className="search-tabs">
        <div className="search-box">
          <input
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              // Clear image when typing text
              if (selectedImage) {
                clearImage();
              }
            }}
            onKeyDown={handleKeyDown}
            placeholder="Search for files..."
            className="search-input"
          />
          <button 
            onClick={handleSearch}
            disabled={loading || !query.trim()}
            className="search-button"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
        
        <div className="image-search-container">
          <div className="image-upload-area" onClick={handleImageUploadClick}>
            {imagePreview ? (
              <div className="image-preview-container">
                <img src={imagePreview} alt="Preview" className="image-preview" />
                <button className="clear-image-btn" onClick={(e) => {
                  e.stopPropagation();
                  clearImage();
                }}>✕</button>
              </div>
            ) : (
              <>
                <div className="upload-icon">
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                    <circle cx="8.5" cy="8.5" r="1.5"/>
                    <polyline points="21 15 16 10 5 21"/>
                  </svg>
                </div>
                <p className="upload-text">Click to upload an image</p>
              </>
            )}
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleImageChange}
              accept="image/*"
              className="file-input"
            />
          </div>
          
          {selectedImage && (
            <button 
              onClick={handleImageSearch}
              disabled={loading}
              className="search-button image-search-button"
            >
              {loading ? 'Searching...' : 'Search by Image'}
            </button>
          )}
        </div>
      </div>
      
      {error && <p className="error-message">{error}</p>}
      
      <div className="results-container">
        {Object.keys(results).length > 0 ? (
          <div className="results-list">
            <h2>Search Results</h2>
            {Object.entries(results).flatMap(([score, resultList], scoreIndex) => 
              resultList.map((result, resultIndex) => (
                <div key={`${scoreIndex}-${resultIndex}`} className="result-card">
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
              ))
            )}
          </div>
        ) : !loading && (query || selectedImage) ? (
          <p className="no-results">No results found</p>
        ) : null}
      </div>
    </div>
  );
};

export default SearchInterface;