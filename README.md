# File Retrieval Engine

A powerful multimodal document search engine that allows you to find files using both text and image-based queries, packaged as a desktop application.
Text and images are extracted and used to generate embeddings using CLIP. These embeddings are then stored in FAISS for document querying based on similarity scores.

<br/>
<p align="center">
  <img src="Frontend/public/logo5.png" alt="File Retrieval Engine" width="200">
</p>

## Features

- **Text-based search** - Find documents by content using natural language queries
- **Image-based search** - Use images to find visually similar documents
- **Multimodal indexing** - Documents are indexed for both text content and visual elements
- **Cross-platform desktop app** - Built with Electron to run on Windows, macOS, and Linux
- **Real-time file monitoring** - Automatically indexes new and modified files
- **Dark/light theme** - User-friendly interface that adapts to your preferences
- **Open files directly** - One-click access to your search results

## Technologies Used

### Backend
- **Python Flask** - Lightweight web server
- **CLIP (Contrastive Language-Image Pre-training)** - Neural network for text and image embeddings
- **FAISS** - Vector similarity search for efficient retrieval
- **PyMuPDF & python-docx** - Document parsing for various file formats

### Frontend
- **React** - Modern UI framework
- **TypeScript** - Type-safe JavaScript
- **Electron** - Desktop application wrapper
- **Vite** - Fast build tooling

## Installation

### Prerequisites
- Python 3.8+ with pip
- Node.js 18+ with npm
- Git

### Setup

Clone the repository:
```bash
git clone https://github.com/Arqam-Siddiqi/File-Retrieval-Engine.git
cd File-Retrieval-Engine
