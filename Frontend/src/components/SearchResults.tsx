import { useState } from 'react';
import FilePreview from './FilePreview';

interface ResultItem {
  filename: string;
  path: string;
  extension: string;
}

interface SearchResultsProps {
  results: Record<string, ResultItem>;
  isLoading: boolean;
  error: string | null;
}

export default function SearchResults({ results, isLoading, error }: SearchResultsProps) {
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  
  // Parse and sort results by score (descending)
  const sortedResults = Object.entries(results)
    .sort(([scoreA, _], [scoreB, __]) => parseFloat(scoreB) - parseFloat(scoreA));
  
  const handleOpenFile = (path: string) => {
    // Use electron IPC to open file
    window.electronAPI?.openFile(path);
  };

  const handlePreviewFile = (path: string) => {
    setSelectedFile(path === selectedFile ? null : path);
  };
  
  if (isLoading) {
    return (
      <div className="results-container loading">
        <div className="loading-spinner"></div>
        <p>Searching for relevant files...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="results-container error">
        <p className="error-message">{error}</p>
      </div>
    );
  }

  if (sortedResults.length === 0) {
    return (
      <div className="results-container empty">
        <p className="no-results">Search for files or upload an image to see results</p>
      </div>
    );
  }

  return (
    <div className="results-container">
      <h2>Search Results</h2>
      <div className="results-list">
        {sortedResults.map(([score, item], index) => {
          const scoreValue = parseFloat(score);
          const isSelected = selectedFile === item.path;
          
          return (
            <div key={index} className={`result-item ${isSelected ? 'selected' : ''}`}>
              <div className="result-content">
                <div className="result-header">
                  <h3 className="filename">{item.filename}</h3>
                  <div className="file-actions">
                    <button 
                      className="preview-btn" 
                      onClick={() => handlePreviewFile(item.path)}
                      title={isSelected ? "Hide preview" : "Preview file"}
                    >
                      {isSelected ? "Hide Preview" : "Preview"}
                    </button>
                    <button 
                      className="open-btn" 
                      onClick={() => handleOpenFile(item.path)}
                      title="Open file"
                    >
                      Open
                    </button>
                  </div>
                </div>
                
                <div className="score-container">
                  <div 
                    className="score-bar" 
                    style={{ width: `${Math.min(scoreValue * 100, 100)}%` }}
                  ></div>
                  <span className="score-value">{scoreValue.toFixed(4)}</span>
                </div>
                
                <div className="file-path">{item.path}</div>
                
                {isSelected && <FilePreview filePath={item.path} fileType={item.extension} />}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}