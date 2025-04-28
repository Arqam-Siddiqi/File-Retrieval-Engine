import { useState } from 'react';
import SearchBar from './components/SearchBar';
import SearchResults from './components/SearchResults';
import './App.css';

interface ResultItem {
  filename: string;
  path: string;
  extension: string;
}

export default function App() {
  const [results, setResults] = useState<Record<string, ResultItem>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (query: string | File) => {
    setIsLoading(true);
    setError(null);
    
    try {
      if (typeof query === 'string') {
        // Text search
        const response = await fetch(`http://localhost:8000/search/${encodeURIComponent(query)}`);
        
        if (!response.ok) {
          throw new Error(`Error: ${response.status}`);
        }
        
        const data = await response.json();
        setResults(data);
      } else {
        // File search - implement file upload
        const formData = new FormData();
        formData.append('image', query);
        
        const response = await fetch('http://localhost:8000/search/image', {
          method: 'POST',
          body: formData,
        });
        
        if (!response.ok) {
          throw new Error(`Error: ${response.status}`);
        }
        
        const data = await response.json();
        setResults(data);
      }
    } catch (err: any) {
      setError(`Failed to search: ${err.message}`);
      setResults({});
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      <header>
        <h1>File Retrieval Engine</h1>
      </header>
      
      <main>
        <SearchBar onSearch={handleSearch} isLoading={isLoading} />
        <SearchResults 
          results={results} 
          isLoading={isLoading} 
          error={error} 
        />
      </main>
      
      <footer>
        <p>File Retrieval Engine &copy; 2024</p>
      </footer>
    </div>
  );
}
