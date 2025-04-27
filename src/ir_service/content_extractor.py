import os
from src.ir_service.embeddings import (
    embed_text,
    embed_image
)
from PIL import Image
import fitz
import io
from docx import Document

def extract_and_embed_txt(file_path: str, doc_id: int):
    embed_text(file_path, doc_id)

def extract_and_embed_image(file_path: str, doc_id: int):
    embed_image(file_path, doc_id)

def extract_and_embed_pdf(file_path: str, doc_id: int):
    doc = fitz.open(file_path)
    all_text = ""
    images = []

    for page in doc:
        all_text += page.get_text()

        for img in page.get_images(full=True):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]

            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            images.append(image)

    embed_text(all_text, doc_id)
    embed_image(images, doc_id)


def extract_and_embed_doc(file_path: str, doc_id: int):
    doc = Document(file_path)
    all_text = ""
    images = []

    for para in doc.paragraphs:
        all_text += para.text + "\n"

    for rel in doc.part.rels.values():
        if "image" in rel.reltype:
            image_data = rel.target_part.blob
            image = Image.open(io.BytesIO(image_data)).convert("RGB")
            images.append(image)
    
    embed_text(all_text, doc_id)
    embed_image(images, doc_id)


def extract_and_embed(file_path: str, doc_id: int):
    _, ext = os.path.splitext(file_path)

    if ext == ".txt":
        extract_and_embed_txt(file_path, doc_id)
    elif ext == ".png" or ext == ".jpg" or ext == ".jpeg":
        extract_and_embed_image(file_path, doc_id)
    elif ext == ".doc" or ext == ".docx":
        extract_and_embed_doc(file_path, doc_id)
    elif ext == ".pdf":
        extract_and_embed_pdf(file_path, doc_id)
    else:
        raise Exception("Invalid file type.")
