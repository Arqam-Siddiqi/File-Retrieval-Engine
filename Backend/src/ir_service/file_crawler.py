import os
import json
from src.ir_service.embeddings import (
    retrieve_closest_doc, 
    delete_doc_embeddings,
    display_document_ids_in_vector_db
)
from src.ir_service.content_extractor import (
    extract_and_embed
)

DOCUMENT_DIR = "../data/"

# Global variables for virtual file system
index: int = 0
vfs_by_docId: dict[str, dict] = {}
vfs_by_path: dict[str, str] = {}

class FileMetadata:
    filename: str
    path: str
    last_modified: float
    size: float
    extension: str

def get_vfs():
    return vfs_by_docId, vfs_by_path

def build_virtual_file_system(root: str, whitelist: set[str] = None):
    global index, vfs_by_docId, vfs_by_path
    if whitelist is None:
        whitelist = set([".jpg", ".jpeg", ".png", ".txt", ".pdf", ".doc", ".docx"])

    # Reset globals
    vfs_by_docId.clear()
    vfs_by_path.clear()

    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            _, ext = os.path.splitext(filename)
            if ext not in whitelist:
                continue

            file_path = os.path.join(dirpath, filename)
            file_stat = os.stat(file_path)
            
            extract_and_embed(file_path, index)

            str_index = str(index)
            vfs_by_path[file_path] = str_index
            vfs_by_docId[str_index] = {
                "filename": filename,
                "path": file_path,
                "last_modified": file_stat.st_mtime,
                "size": file_stat.st_size,
                "extension": ext
            }
            
            index += 1


def save_virtual_file_system():
    global index, vfs_by_docId, vfs_by_path
    with open("virtual_file_system.json", "w") as f:
        json.dump((index, vfs_by_docId, vfs_by_path), f, indent=4)


def load_virtual_file_system():
    global index, vfs_by_docId, vfs_by_path

    if os.path.exists("virtual_file_system.json"):
        with open("virtual_file_system.json", "r") as f:
            index, vfs_by_docId, vfs_by_path = json.load(f)
    else:
        vfs_by_docId = {}
        vfs_by_path = {}
        index = 0


def update_virtual_file_system(root: str = DOCUMENT_DIR, whitelist: set[str] = None):
    global index, vfs_by_docId, vfs_by_path

    if whitelist is None:
        whitelist = set([".jpg", ".jpeg", ".png", ".txt", ".pdf", ".doc", ".docx"])

    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:

            _, ext = os.path.splitext(filename)
            if ext not in whitelist:
                continue

            file_path: str = os.path.join(dirpath, filename)
            file_stat = os.stat(file_path)

            if file_path not in vfs_by_path:
                extract_and_embed(file_path, index)
                
                str_index = str(index)
                vfs_by_path[file_path] = str_index
                vfs_by_docId[str_index] = {
                    "filename": filename,
                    "path": file_path,
                    "last_modified": file_stat.st_mtime,
                    "size": file_stat.st_size,
                    "extension": ext
                }
                index += 1
                
            elif file_stat.st_mtime != vfs_by_docId[vfs_by_path[file_path]]["last_modified"]:
                str_index = vfs_by_path[file_path]

                index = int(str_index)

                delete_doc_embeddings([index])
                extract_and_embed(file_path, index)

                vfs_by_docId[str_index] = {
                    "filename": filename,
                    "path": file_path,
                    "last_modified": file_stat.st_mtime,
                    "size": file_stat.st_size,
                    "extension": os.path.splitext(filename)[1]
                }
    
    docIds_to_delete = []
    for path, doc_id in list(vfs_by_path.items()):
        if not os.path.exists(path):
            docIds_to_delete.append(int(doc_id))
            del vfs_by_docId[doc_id]
            del vfs_by_path[path]

    if docIds_to_delete:
        delete_doc_embeddings(docIds_to_delete)


if __name__ == "__main__":

    load_virtual_file_system()
    update_virtual_file_system(DOCUMENT_DIR)
    save_virtual_file_system()

    result = retrieve_closest_doc("Pakistan", k=10)
    output = []
    for id, score in result:
        output.append((id, score))
    output.sort(key=lambda x: x[1], reverse=True)

    for id, score in output:
        print(vfs_by_docId[id]["filename"], " - ", score)

    display_document_ids_in_vector_db()
