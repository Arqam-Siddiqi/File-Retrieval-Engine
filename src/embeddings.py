import os
import faiss
import numpy as np
import nltk
from nltk.tokenize import sent_tokenize
import torch
from PIL import Image, UnidentifiedImageError
import clip

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


def encode_and_index_text(filepath: str, doc_id: int, index_path: str = "faiss_index.idx"):
    """
    Read a text file, split into sentences, encode with CLIP text encoder
    (via the `clip` package), normalize embeddings, and add to a FAISS index.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"The file {filepath} does not exist.")

    # 1) Read & split
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    sentences = sent_tokenize(text)
    if not sentences:
        raise ValueError("No sentences were extracted from the document.")

    # 2) Encode under no_grad, detach, move to CPU & numpy
    with torch.no_grad():
        text_tokens = clip.tokenize(sentences).to(device)        # [N, token_len]
        emb = model.encode_text(text_tokens)                     # torch.Tensor [N,512]
        emb = emb.detach().cpu().numpy()                         # ndarray [N,512]

    # 3) L2‐normalize row‐wise
    emb = emb / np.linalg.norm(emb, axis=1, keepdims=True)

    # 4) Print (optional) & determine dim
    dim = 512
    print(f"[encode_text] embeddings shape: {emb.shape}")

    # 5) Build unique IDs for each sentence
    flag = 0
    ids = np.array([(doc_id * offset + i) << 1 | flag for i in range(len(sentences))], dtype=np.int64)

    # 6) Load or create FAISS index, add embeddings
    index = _load_or_create_index(index_path, dim)
    index.add_with_ids(emb, ids)
    faiss.write_index(index, index_path)

    print(f"Indexed text DocID {doc_id} ({len(sentences)} segments) → {index_path}")


def encode_and_index_image(image_input, doc_id: int, index_path: str = "faiss_index.idx"):
    """
    Read an image file path or PIL Image, encode with CLIP vision encoder,
    normalize embeddings, and add to the shared FAISS index.
    """
    if isinstance(image_input, str):
        if not os.path.exists(image_input):
            raise FileNotFoundError(f"The image {image_input} does not exist.")
        try:
            image = Image.open(image_input).convert("RGB")
        except UnidentifiedImageError:
            raise ValueError(f"File at {image_input} is not a valid image.")
    elif isinstance(image_input, Image.Image):
        image = image_input.convert("RGB")
    else:
        raise ValueError("image_input must be a file path or PIL.Image object.")
    
    img_input = preprocess(image).unsqueeze(0).to(device)
    with torch.no_grad():
        emb = model.encode_image(img_input).detach().cpu().numpy()

    # — normalize! —
    emb = emb / np.linalg.norm(emb, axis=1, keepdims=True)

    dim = 512
    flag = 1
    id = np.array([(doc_id * offset) << 1 | flag], dtype=np.int64)

    idx = _load_or_create_index(index_path, dim)
    idx.add_with_ids(emb, id)
    faiss.write_index(idx, index_path)
    print(f"Indexed image DocID {doc_id} to {index_path}.")


def retrieve_closest_doc(query, index_path: str = "faiss_index.idx", k: int = 1, balance_factor: float = 2.7):
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
        flag = idx & 1
        idx >>= 1
        doc_id = idx // offset

        if (doc_id, flag) not in seen:
            if doc_id in results:
                score = float(dist)
                if (is_image and flag == 0) or (not is_image and flag == 1):
                    score *= balance_factor
                
                seen.add((doc_id, flag))                
                results[doc_id] = max(results[doc_id], score)
            else:
                score = float(dist)
                if (is_image and flag == 0) or (not is_image and flag == 1):
                    score *= balance_factor
                results[doc_id] = score
        
        if len(results) == k:
            break

    if not results:
        raise ValueError("No results found for the given query.")
    
    results = list(map(lambda x : (int(x[0]), x[1]), results.items()))

    return results

def delete_doc_vectors_batch(
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

from pprint import pprint
index = _load_or_create_index("faiss_index.idx", 512)
stored_ids = faiss.vector_to_array(index.id_map)
stored_ids >>= 1
ids = list(set(map(lambda x : int(x) // 10**5, stored_ids)))
pprint(ids)

# tokens = clip.tokenize(["black cat playing with red ball in white background"]).to(device)
# with torch.no_grad():
#     q_emb = model.encode_text(tokens).cpu().numpy()
# q_emb = q_emb / np.linalg.norm(q_emb, axis=1, keepdims=True)

# # Encode image
# img_input = preprocess(Image.open("data/images2.jpg").convert("RGB")).unsqueeze(0).to(device)
# with torch.no_grad():
#     img_emb = model.encode_image(img_input).cpu().numpy()
# img_emb = img_emb / np.linalg.norm(img_emb, axis=1, keepdims=True)

# similarity = float(np.dot(q_emb, img_emb.T)[0][0])
# print("Direct similarity:", similarity)