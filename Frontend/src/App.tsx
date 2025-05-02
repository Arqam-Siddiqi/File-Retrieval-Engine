import './App.css'
import SearchInterface from './components/SearchInterface'
import ThemeToggle from './components/ThemeToggle'
import { ThemeProvider } from './context/ThemeContext'

function App() {
  return (
    <ThemeProvider>
      <div className="app-container">
        <ThemeToggle />
        <SearchInterface />
      </div>
    </ThemeProvider>
  )
}

export default App
