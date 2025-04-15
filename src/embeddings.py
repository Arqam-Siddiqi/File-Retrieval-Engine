import os
import faiss
import numpy as np
import nltk
from nltk.tokenize import sent_tokenize
from sentence_transformers import SentenceTransformer

# Ensure sentence tokenizer is available
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)

def encode_and_index(filepath, doc_id, index_path="faiss_index.idx"):
    """
    Read the file contents, split into sentences, encode them, and add the resulting embeddings to the FAISS index.
    If an index file exists, merge the new embeddings; otherwise, create a new index.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"The file {filepath} does not exist.")

    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    sentences = sent_tokenize(text)
    if not sentences:
        raise ValueError("No sentences were extracted from the document.")

    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(sentences, convert_to_numpy=True)

    # Normalize for cosine similarity
    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

    embedding_dim = embeddings.shape[1]
    OFFSET = 10 ** 5  
    ids = np.array([doc_id * OFFSET + i for i in range(len(sentences))], dtype=np.int64)

    if os.path.exists(index_path):
        index = faiss.read_index(index_path)
    else:
        index_flat = faiss.IndexFlatIP(embedding_dim)
        index = faiss.IndexIDMap(index_flat)

    index.add_with_ids(embeddings, ids)
    faiss.write_index(index, index_path)
    print(f"DocID {doc_id} has been indexed.")

def retrieve_closest_doc(query_str, index_path="faiss_index.idx", k=1):
    """
    Compute cosine similarity between the input query and indexed sentence embeddings.
    Return k distinct docIds with their similarity scores as list of (docId, score) tuples.
    """
    OFFSET = 10 ** 5

    if not os.path.exists(index_path):
        raise FileNotFoundError(f"The FAISS index file '{index_path}' does not exist.")

    index = faiss.read_index(index_path)
    model = SentenceTransformer("all-MiniLM-L6-v2")
    query_embedding = model.encode([query_str], convert_to_numpy=True)
    query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)

    # Search for more to ensure we get enough distinct docIds
    distances, ids = index.search(query_embedding, k * 10)

    # Decode to docIds and filter for unique ones
    seen = set()
    result = []
    for i, idx in enumerate(ids[0]):
        if idx == -1:
            continue
        doc_id = idx // OFFSET
        if doc_id not in seen:
            seen.add(doc_id)
            # Add tuple of (docId, score) where score is the distance (similarity)
            result.append((int(doc_id), float(distances[0][i])))
        if len(result) == k:
            break

    if not result:
        raise ValueError("No results found in the index for the given query.")

    return result

