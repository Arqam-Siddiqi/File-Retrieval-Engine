import os
import json
import time
from embeddings import (
    retrieve_closest_doc, 
    delete_doc_embeddings,
    display_document_ids_in_vector_db
)
from content_extractor import (
    extract_and_embed
)
import sys

index: int = 0

class FileMetadata():
    filename: str
    path: str
    last_modified: float
    size: float
    extension: str

def build_virtual_file_system(root: str, whitelist: set[str] = None):
    if whitelist is None:
        whitelist = set([".jpg", ".jpeg", ".png", ".txt", ".pdf", ".doc", ".docx"])

    vfs_by_docId: dict[int, FileMetadata] = {}
    vfs_by_path: dict[str, int] = {}
    global index

    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            _, ext = os.path.splitext(filename)
            if ext not in whitelist:
                continue

            file_path = os.path.join(dirpath, filename)
            file_stat = os.stat(file_path)
            
            extract_and_embed(file_path, index)

            new_index = str(index)

            vfs_by_path[file_path] = new_index

            vfs_by_docId[new_index] = {
                "filename": filename,
                "path": file_path,
                "last_modified": file_stat.st_mtime,
                "size": file_stat.st_size,
                "extension": os.path.splitext(filename)[1]
            }
            
            index += 1

    return vfs_by_docId, vfs_by_path

def save_virtual_file_system(vfs: tuple):
    global index
    with open("virtual_file_system.json", "w") as f:
        json.dump((index, vfs[0], vfs[1]), f, indent=4)

def load_virtual_file_system():
    global index
    global vfs_by_docId
    global vfs_by_path

    if os.path.exists("virtual_file_system.json"):
        with open("virtual_file_system.json", "r") as f:
            index, vfs_by_docId, vfs_by_path = json.load(f)
    else:
        vfs_by_docId = {}
        vfs_by_path = {}
        index = 0

def update_virtual_file_system(
        root: str, 
        vfs_by_docId: dict[int, FileMetadata], 
        vfs_by_path: dict[str, int | str], 
        whitelist: set[str] = None
):
    if whitelist is None:
        whitelist = set([".jpg", ".jpeg", ".png", ".txt", ".pdf", ".doc", ".docx"])

    global index
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:

            _, ext = os.path.splitext(filename)
            if ext not in whitelist:
                continue

            file_path: str = os.path.join(dirpath, filename)
            file_stat = os.stat(file_path)

            if file_path not in vfs_by_path:
                
                extract_and_embed(file_path, index)

                new_index = str(index)

                vfs_by_path[file_path] = new_index

                vfs_by_docId[new_index] = {
                    "filename": filename,
                    "path": file_path,
                    "last_modified": file_stat.st_mtime,
                    "size": file_stat.st_size,
                    "extension": os.path.splitext(filename)[1]
                }
                
                index += 1
            elif file_stat.st_mtime != vfs_by_docId[vfs_by_path[file_path]]["last_modified"]:
                new_index = vfs_by_path[file_path]
                index = int(new_index)

                delete_doc_embeddings([index])
                extract_and_embed(file_path, index)

                vfs_by_docId[new_index] = {
                    "filename": filename,
                    "path": file_path,
                    "last_modified": file_stat.st_mtime,
                    "size": file_stat.st_size,
                    "extension": os.path.splitext(filename)[1]
                }
    
    docIds_to_delete = []
    for k in list(vfs_by_path.keys()):
        if not os.path.exists(k):
            docIds_to_delete.append(int(vfs_by_path[k]))
            del vfs_by_docId[vfs_by_path[k]]
            del vfs_by_path[k]

    if docIds_to_delete:
        delete_doc_embeddings(docIds_to_delete)


if __name__ == "__main__":

    # vfs_by_docId, vfs_by_path = build_virtual_file_system("data")
    # save_virtual_file_system((vfs_by_docId, vfs_by_path))

    load_virtual_file_system()
    update_virtual_file_system("data", vfs_by_docId, vfs_by_path)
    save_virtual_file_system((vfs_by_docId, vfs_by_path))

    result = retrieve_closest_doc("Pakistan", k=10)
    output = []
    for id, score in result:
        id = str(id)
        output.append((str(id), score))
    output.sort(key=lambda x: x[1], reverse=True)

    for id, score in output:
        print(vfs_by_docId[id]["filename"], " - ", score)

    display_document_ids_in_vector_db()