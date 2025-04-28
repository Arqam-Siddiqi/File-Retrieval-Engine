/// <reference types="vite/client" />

interface Window {
  electronAPI?: {
    openFile: (filePath: string) => void;
    readFile: (filePath: string) => Promise<string | null>;
  }
}
