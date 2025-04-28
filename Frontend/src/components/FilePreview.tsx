import { useState, useEffect } from 'react';

interface FilePreviewProps {
  filePath: string;
  fileType: string;
}

export default function FilePreview({ filePath, fileType }: FilePreviewProps) {
  const [content, setContent] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchContent = async () => {
      setIsLoading(true);
      setError(null);
      try {
        // Use ElectronAPI to read file contents
        const fileContent = await window.electronAPI?.readFile(filePath);
        setContent(fileContent ?? null);
      } catch (err: any) {
        setError(`Failed to load file: ${err.message}`);
      } finally {
        setIsLoading(false);
      }
    };

    fetchContent();
  }, [filePath]);

  if (isLoading) {
    return <div className="preview-loading">Loading preview...</div>;
  }

  if (error) {
    return <div className="preview-error">{error}</div>;
  }

  // Handle different file types (ensure extension has a dot)
  const extension = fileType.startsWith('.') ? fileType : `.${fileType}`;
  
  switch (extension) {
    case '.txt':
      return (
        <div className="preview-container text-preview">
          <pre>{content}</pre>
        </div>
      );
    
    case '.jpg':
    case '.jpeg':
    case '.png':
      return (
        <div className="preview-container image-preview">
          <img src={`file://${filePath}`} alt="File preview" />
        </div>
      );

    case '.pdf':
      return (
        <div className="preview-container pdf-preview">
          <p>PDF preview is not available. Please open the file to view it.</p>
        </div>
      );

    case '.doc':
    case '.docx':
      return (
        <div className="preview-container docx-preview">
          <p>Document preview is not available. Please open the file to view it.</p>
        </div>
      );

    default:
      return (
        <div className="preview-container unknown-preview">
          <p>Preview not available for this file type ({extension})</p>
        </div>
      );
  }
}