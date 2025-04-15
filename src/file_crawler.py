import os
import json
import time
from embeddings import encode_and_index, retrieve_closest_doc

index: int = 0

class FileMetadata():
    filename: str
    file_path: str
    last_modified: float
    size: float
    extension: str

def build_virtual_file_system(root: str):
    vfs_by_docId: dict[int, FileMetadata] = {}
    vfs_by_path: dict[str, int] = {}
    global index

    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            file_stat = os.stat(file_path)
            
            encode_and_index(file_path, index)

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
    with open("virtual_file_system.json", "r") as f:
        index, vfs_by_docId, vfs_by_path = json.load(f)

def update_virtual_file_system(root, vfs_by_docId: dict[int, FileMetadata], vfs_by_path: dict[str, int]):
    global index
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            file_stat = os.stat(file_path)

            if file_path not in vfs_by_path:
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

                vfs_by_path[file_path] = new_index

                vfs_by_docId[new_index] = {
                    "filename": filename,
                    "path": file_path,
                    "last_modified": file_stat.st_mtime,
                    "size": file_stat.st_size,
                    "extension": os.path.splitext(filename)[1]
                }
    
    for k in list(vfs_by_path.keys()):
        if not os.path.exists(k):
            del vfs_by_docId[vfs_by_path[k]]
            del vfs_by_path[k]


# t1 = time.time()
# vfs_by_docId, vfs_by_path = build_virtual_file_system("data")
# t2 = time.time()
# print("Benchmark1:", t2 - t1)

# vfs_by_docId, vfs_by_path = build_virtual_file_system("data")
# save_virtual_file_system((vfs_by_docId, vfs_by_path))


# vfs_by_docId, vfs_by_path = load_virtual_file_system()
# t1 = time.time()
# update_virtual_file_system("data", vfs_by_docId, vfs_by_path)
# t2 = time.time()
# print("Benchmark2:", t2 - t1)

# update_virtual_file_system("data", vfs_by_docId, vfs_by_path)

# from pprint import pprint
# pprint(vfs_by_docId)
# print()
# pprint(vfs_by_path)
# print(index)

vfs_by_docId, vfs_by_path = build_virtual_file_system("data")
# load_virtual_file_system()
t1 = time.time()
result = retrieve_closest_doc("statistics", k=5)
t2 = time.time()
print(result)
print("Benchmark3:", t2 - t1)