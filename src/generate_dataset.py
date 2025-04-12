import os
import random

# A list of proper English sentences.
SENTENCES = [
    "The quick brown fox jumps over the lazy dog.",
    "Time and tide wait for no man.",
    "Actions speak louder than words.",
    "Every cloud has a silver lining.",
    "Fortune favors the bold.",
    "Honesty is the best policy.",
    "The early bird catches the worm.",
    "A picture is worth a thousand words.",
    "Better late than never.",
    "Practice makes perfect.",
    "All that glitters is not gold.",
    "Beauty is in the eye of the beholder.",
    "When in Rome, do as the Romans do.",
    "The pen is mightier than the sword.",
    "Knowledge is power."
]

def generate_sentence() -> str:
    """Randomly selects and returns one English sentence from the list."""
    return random.choice(SENTENCES)

def generate_paragraph(min_sentences: int = 3, max_sentences: int = 7) -> str:
    """Generates a paragraph with a random number of sentences."""
    num_sentences = random.randint(min_sentences, max_sentences)
    sentences = [generate_sentence() for _ in range(num_sentences)]
    return " ".join(sentences)

def generate_document(num_paragraphs: int = 5, min_sentences: int = 3, max_sentences: int = 7) -> str:
    """Generates a document composed of several paragraphs."""
    paragraphs = [generate_paragraph(min_sentences, max_sentences) for _ in range(num_paragraphs)]
    return "\n\n".join(paragraphs)

def create_documents_in_folder(folder_path: str, docs_per_folder: int = 10, paragraphs_per_document: int = 5) -> None:
    """
    Creates multiple synthetic documents in the specified folder.
    
    Each document is saved as a text file with a title header and multiple paragraphs.
    """
    os.makedirs(folder_path, exist_ok=True)
    for doc_id in range(1, docs_per_folder + 1):
        doc_text = generate_document(num_paragraphs=paragraphs_per_document)
        filename = f"document_{doc_id}.txt"
        file_path = os.path.join(folder_path, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            title = f"Document {doc_id}"
            f.write(title + "\n" + "=" * len(title) + "\n\n")
            f.write(doc_text)

def create_folder_structure(
    root_dir: str = "synthetic_docs",
    num_folders: int = 10,
    docs_per_folder: int = 10,
    paragraphs_per_document: int = 5
) -> None:
    """
    Generates a folder structure with multiple folders. Each folder will contain synthetic documents.
    
    Parameters:
        root_dir: The root directory where folders will be created.
        num_folders: The number of subfolders to create under root_dir.
        docs_per_folder: The number of documents to create in each folder.
        paragraphs_per_document: The number of paragraphs in each document.
    """
    os.makedirs(root_dir, exist_ok=True)
    for folder_id in range(1, num_folders + 1):
        folder_name = f"folder_{folder_id}"
        folder_path = os.path.join(root_dir, folder_name)
        create_documents_in_folder(folder_path, docs_per_folder, paragraphs_per_document)

if __name__ == "__main__":
    # Customize these parameters as needed:
    ROOT_DIRECTORY = "data"  # Root directory for the synthetic file system.
    NUMBER_OF_FOLDERS = 100             # Total number of folders to create.
    DOCUMENTS_PER_FOLDER = 1000          # Number of documents per folder.
    PARAGRAPHS_PER_DOCUMENT = 5        # Number of paragraphs per document.
    
    create_folder_structure(
        root_dir=ROOT_DIRECTORY,
        num_folders=NUMBER_OF_FOLDERS,
        docs_per_folder=DOCUMENTS_PER_FOLDER,
        paragraphs_per_document=PARAGRAPHS_PER_DOCUMENT
    )
