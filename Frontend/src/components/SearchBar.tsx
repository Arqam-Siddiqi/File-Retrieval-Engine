import { useState, useRef } from 'react';

interface SearchBarProps {
  onSearch: (query: string | File) => void;
  isLoading: boolean;
}

export default function SearchBar({ onSearch, isLoading }: SearchBarProps) {
  const [searchText, setSearchText] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null);

  const handleTextSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchText.trim()) {
      onSearch(searchText);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      setSelectedFileName(file.name);
      onSearch(file);
    }
  };

  const clearSelectedFile = () => {
    setSelectedFileName(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="search-container">
      <form onSubmit={handleTextSearch} className="search-form">
        <div className="search-input-wrapper">
          <input
            type="text"
            className="search-input"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            placeholder="Search for files..."
            disabled={isLoading}
          />
          <button 
            type="submit" 
            className="search-button"
            disabled={isLoading || !searchText.trim()}
          >
            {isLoading ? 'Searching...' : 'Search'}
          </button>
        </div>

        <div className="file-upload-section">
          <span className="or-divider">OR</span>
          <div className="file-input-container">
            <label className="file-input-label">
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                accept="image/*"
                className="file-input"
                disabled={isLoading}
              />
              <span className="file-button">Upload Image</span>
            </label>
            
            {selectedFileName && (
              <div className="selected-file">
                <span className="file-name">{selectedFileName}</span>
                <button 
                  type="button" 
                  className="clear-file-btn"
                  onClick={clearSelectedFile}
                  disabled={isLoading}
                >
                  ×
                </button>
              </div>
            )}
          </div>
        </div>
      </form>
    </div>
  );
}