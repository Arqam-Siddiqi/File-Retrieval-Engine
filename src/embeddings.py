import os
import faiss
import numpy as np
import nltk
from nltk.tokenize import sent_tokenize
import torch
from PIL import Image, UnidentifiedImageError
import clip
from collections import defaultdict

# Download NLTK sentence splitter
# nltk.download('punkt', quiet=True)

# --- Initialize CLIP components ---
device = "cuda" if torch.cuda.is_available() else "cpu"
model_name = "openai/clip-vit-base-patch32"
model, preprocess = clip.load("ViT-B/32", device=device)


# ID offset for combining doc_id and segment index
offset = 10**5


def _load_or_create_index(index_path: str, dim: int) -> faiss.IndexIDMap:
    """
    Helper to load an existing FAISS IndexIDMap or create a new one.
    Uses inner-product (IP) index for cosine similarity on normalized vectors.
    """
    if os.path.exists(index_path):
        return faiss.read_index(index_path)
    flat = faiss.IndexFlatIP(dim)
    return faiss.IndexIDMap(flat)


def embed_text(text_input: str, doc_id: int, index_path: str = "faiss_index.idx"):
    """
    Read a text file, split into sentences, encode with CLIP text encoder
    (via the `clip` package), normalize embeddings, and add to a FAISS index.
    """
    if os.path.exists(text_input):
        with open(text_input, "r", encoding="utf-8") as f:
            text_input = f.read()

    # 1) Read & split
    sentences = sent_tokenize(text_input)
    if not sentences:
        raise ValueError("No sentences were extracted from the document.")

    if len(sentences) > 0.9 * offset:
        raise Exception(f"Only {0.9 * offset} sentences can be embedded.")

    # 2) Encode under no_grad, detach, move to CPU & numpy
    with torch.no_grad():
        text_tokens = clip.tokenize(sentences).to(device)        # [N, token_len]
        emb = model.encode_text(text_tokens)                     # torch.Tensor [N,512]
        emb = emb.detach().cpu().numpy()                         # ndarray [N,512]

    # 3) L2‐normalize row‐wise
    emb = emb / np.linalg.norm(emb, axis=1, keepdims=True)

    # 4) Print (optional) & determine dim
    dim = 512

    # 5) Build unique IDs for each sentence
    # [100,000 - 190,000]
    ids = np.array([doc_id * offset + i for i in range(len(sentences))], dtype=np.int64)

    # 6) Load or create FAISS index, add embeddings
    index = _load_or_create_index(index_path, dim)
    index.add_with_ids(emb, ids)
    faiss.write_index(index, index_path)

    print(f"Indexed text DocID {doc_id} ({len(sentences)} segments) → {index_path}")


def embed_image(image_input: list[Image.Image] | str, doc_id: int, index_path: str = "faiss_index.idx"):
    """
    Read an image file path or PIL Image, encode with CLIP vision encoder,
    normalize embeddings, and add to the shared FAISS index.
    """
    if isinstance(image_input, str):
        if not os.path.exists(image_input):
            raise FileNotFoundError(f"The image {image_input} does not exist.")
        
        image_input = [Image.open(image_input).convert("RGB")]
    
    if len(image_input) > 0.1 * offset:
        raise Exception(f"Only {0.1 * offset} images can be embedded.")
    
    prepped = [preprocess(img) for img in image_input]
    batch = torch.stack(prepped, dim=0).to(device)

    # 4) Encode + normalize
    with torch.no_grad():
        emb = model.encode_image(batch)
        emb = emb / emb.norm(dim=1, keepdim=True)
    emb_np = emb.cpu().numpy()

    dim = 512

    start = int(doc_id * offset + 0.9 * offset)
    ids = np.arange(start, start + emb_np.shape[0], dtype=np.int64)

    index = _load_or_create_index(index_path, dim)
    index.add_with_ids(emb_np, ids)
    faiss.write_index(index, index_path)

    print(f"Indexed {emb_np.shape[0]} image(s) for doc_id={doc_id} into '{index_path}'.")


def retrieve_closest_doc(query, index_path: str = "faiss_index.idx", k: int = 1, balance_factor: float = 3):
    """
    Accepts a text string or image (file‑path or PIL.Image), encodes it
    with the CLIP model you loaded via `clip.load("ViT-B/32")`, then
    searches your shared FAISS index. Returns a list of (doc_id, score).
    """
    # Determine modality
    is_image = False
    image = None
    if isinstance(query, Image.Image):
        is_image = True
        image = query
    elif isinstance(query, str) and os.path.exists(query):
        try:
            image = Image.open(query).convert("RGB")
            is_image = True
        except UnidentifiedImageError:
            is_image = False

    # Load index
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"Index file '{index_path}' not found.")
    index: faiss.IndexIDMap = faiss.read_index(index_path)

    # Encode query to a 512‑d numpy vector
    if is_image:
        img_input = preprocess(image).unsqueeze(0).to(device)
        with torch.no_grad():
            q_emb = model.encode_image(img_input).cpu().numpy()
    else:
        tokens = clip.tokenize([query]).to(device)
        with torch.no_grad():
            q_emb = model.encode_text(tokens).cpu().numpy()

    q_emb = q_emb / np.linalg.norm(q_emb, axis=1, keepdims=True)

    search_k = k * 100
    distances, ids = index.search(q_emb, search_k)

    results = {}
    seen = set()
    for dist, idx in zip(distances[0], ids[0]):
        if idx < 0: continue

        is_image_embedding = False
        if (idx % offset) >= (0.9 * offset):
            is_image_embedding = True

        doc_id = idx // offset

        if (doc_id, is_image_embedding) not in seen:
            if doc_id in results:
                score = float(dist)
                if (is_image and not is_image_embedding) or (not is_image and is_image_embedding):
                    score *= balance_factor
                
                seen.add((doc_id, is_image_embedding))                
                results[doc_id] = max(results[doc_id], score)
            else:
                score = float(dist)
                if (is_image and not is_image_embedding) or (not is_image and is_image_embedding):
                    score *= balance_factor
                results[doc_id] = score
        
        # if len(results) == k:
        #     break

    if not results:
        raise ValueError("No results found for the given query.")
    
    results = [(int(k), v) for k, v in results.items()]

    return results


def delete_doc_embeddings(
    doc_ids: list[int],
    index_path: str = "faiss_index.idx",
    offset: int = 10**5
) -> dict[int, int]:
    """
    Delete all vectors for each `doc_id` in `doc_ids` from a FAISS IndexIDMap.

    Vectors were originally added with IDs = doc_id * offset + segment_index.
    Uses IDSelectorRange to avoid loading the entire id_map into Python.

    Returns a dict mapping each doc_id to the number of vectors removed.
    """
    index = faiss.read_index(index_path)
    if not hasattr(index, "id_map"):
        raise ValueError("Index is not an IndexIDMap; cannot remove by ID.")

    removed_counts: dict[int, int] = {}
    total_before = index.ntotal

    for doc_id in doc_ids:
        imin = doc_id * offset
        imax = (doc_id + 1) * offset
        pre_ntotal = index.ntotal

        selector = faiss.IDSelectorRange(imin, imax)
        index.remove_ids(selector)

        post_ntotal = index.ntotal
        removed = pre_ntotal - post_ntotal
        removed_counts[doc_id] = removed

    faiss.write_index(index, index_path)

    total_removed = total_before - index.ntotal
    print(f"Removed a total of {total_removed} vectors across doc_ids={doc_ids}")
    return removed_counts

def display_document_ids_in_vector_db():
    from pprint import pprint
    index = _load_or_create_index("faiss_index.idx", 512)
    stored_ids = faiss.vector_to_array(index.id_map)

    ids = defaultdict(lambda: {"images": 0, "text": 0})
    for id in stored_ids:
        reduced_id = int(id // offset)
        if (id % offset) >= (0.9 * offset):
            ids[reduced_id]["images"] += 1
        else:
            ids[reduced_id]["text"] += 1

    pprint(dict(ids))
