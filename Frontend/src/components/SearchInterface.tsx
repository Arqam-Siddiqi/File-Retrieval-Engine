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

// Update the SearchResult interface to include size and last_modified
interface SearchResult {
  filename: string;
  path: string;
  extension: string;
  size: number;
  last_modified: number;
}

// Updated interface to reflect the new response format
interface SearchResultsMap {
  [score: string]: SearchResult[];
}

const SearchInterface = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResultsMap>({});
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const [refreshMessage, setRefreshMessage] = useState('');
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

  const handleRefresh = async () => {
    setRefreshing(true);
    setRefreshMessage('');
    setError('');
    
    try {
      const response = await fetch('http://localhost:5000/refresh');
      
      if (!response.ok) {
        throw new Error('Refresh failed. Please try again.');
      }
      
      const data = await response.json();
      setRefreshMessage(data.message || 'Index refreshed successfully');
      // Clear previous results when refreshing
      setResults({});
    } catch (err) {
      console.error('Refresh error:', err);
      setError('Failed to refresh index. Is the backend server running?');
    } finally {
      setRefreshing(false);
      // Auto-hide refresh message after 5 seconds
      setTimeout(() => {
        setRefreshMessage('');
      }, 5000);
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

  // Add these helper functions inside the SearchInterface component

  // Format file size in bytes to human-readable format
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return parseFloat((bytes / Math.pow(1024, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Format timestamp to readable date
  const formatDate = (timestamp: number): string => {
    const date = new Date(timestamp * 1000); // Convert Unix timestamp to JavaScript Date
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="search-container">
      <div className="app-header">
        <div className="logo-container">
          <img src="/logo5.png" alt="File Retrieval Engine Logo" className="app-logo" />
        </div>
        <div className="title-container">
          <h1>File Retrieval Engine</h1>
          <p className="subtitle">Search by text or image</p>
        </div>
      </div>
      
      <div className="action-bar">
        <button 
          className={`refresh-button ${refreshing ? 'refreshing' : ''}`}
          onClick={handleRefresh}
          disabled={refreshing}
        >
          {refreshing ? (
            <>
              <span className="spinner"></span>
              <span>Refreshing...</span>
            </>
          ) : (
            <>
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/>
              </svg>
              <span>Refresh Index</span>
            </>
          )}
        </button>
        
        {refreshMessage && (
          <p className="refresh-message success">{refreshMessage}</p>
        )}
      </div>
      
      <div className="search-tabs">
        <div className="search-box">
          {selectedImage && (
            <div className="image-preview-chip">
              <img 
                src={imagePreview || ''} 
                alt="Selected" 
                className="image-chip-preview" 
              />
              <span>Image search</span>
              <button 
                className="chip-remove-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  clearImage();
                }}
              >
                ✕
              </button>
            </div>
          )}
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
            placeholder={selectedImage ? "" : "Search for files..."}
            className={`search-input ${selectedImage ? 'with-image' : ''}`}
            disabled={selectedImage !== null || refreshing}
          />
          <div className="image-button-container">
            <button
              className="image-upload-button"
              onClick={handleImageUploadClick}
              title="Search by image"
              disabled={refreshing}
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                <circle cx="8.5" cy="8.5" r="1.5"/>
                <polyline points="21 15 16 10 5 21"/>
              </svg>
            </button>
          </div>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleImageChange}
            accept="image/*"
            className="file-input"
            disabled={refreshing}
          />
          <button 
            onClick={selectedImage ? handleImageSearch : handleSearch}
            disabled={loading || refreshing || (!query.trim() && !selectedImage)}
            className="search-button"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </div>
      
      {error && <p className="error-message">{error}</p>}
      
      <div className="results-container">
        {Object.keys(results).length > 0 ? (
          <div className="results-list">
            <h2>Search Results</h2>
            {Object.entries(results).flatMap(([score, resultList], scoreIndex) => 
              resultList.map((result, resultIndex) => (
                <div 
                  key={`${scoreIndex}-${resultIndex}`} 
                  className="result-card"
                  onClick={() => handleOpenFile(result.path)}
                >
                  <div className="result-header">
                    <h3 className="file-name">{result.filename}</h3>
                  </div>
                  <div className="file-details">
                    <p className="file-path">{result.path}</p>
                    <p className="file-type">Type: {result.extension.toUpperCase()}</p>
                    <p className="file-size">Size: {formatFileSize(result.size)}</p>
                    <p className="file-date">Modified: {formatDate(result.last_modified)}</p>
                  </div>
                  <p className="file-score">Score: {parseFloat(score).toFixed(4)}</p>
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