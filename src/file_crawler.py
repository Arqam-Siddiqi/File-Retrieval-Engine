import os
import json
from queue import PriorityQueue

leftover_indices = PriorityQueue()
index = 0

def build_virtual_file_system(root: str):
    vfs_by_docId = {}
    vfs_by_path = {}
    global index

    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            file_stat = os.stat(file_path)
            
            new_index = str(index)

            vfs_by_path[file_path] = new_index

            vfs_by_docId[new_index] = {
                "filename": filename,
                "path": file_path,
                "last-modified": file_stat.st_mtime,
                "size": file_stat.st_size,
                "extension": os.path.splitext(filename)[1]
            }
            
            index += 1

    return vfs_by_docId, vfs_by_path

def save_virtual_file_system(vfs):
    global index
    with open("virtual_file_system.json", "w") as f:
        json.dump((index, vfs[0], vfs[1]), f, indent=4)

def load_virtual_file_system():
    global index
    with open("virtual_file_system.json", "r") as f:
        index, vfs_by_docId, vfs_by_path = json.load(f)

    return vfs_by_docId, vfs_by_path

def update_virtual_file_system(root, vfs_by_docId, vfs_by_path):
    global index
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            file_stat = os.stat(file_path)

            if file_stat.st_mtime != vfs_by_docId[vfs_by_path[file_path]]["last-modified"]:
                # status = leftover_indices.empty()
                # new_index = str(leftover_indices.get() if not status else index)
                new_index = vfs_by_path[file_path]

                vfs_by_path[file_path] = new_index

                vfs_by_docId[new_index] = {
                    "filename": filename,
                    "path": file_path,
                    "last-modified": file_stat.st_mtime,
                    "size": file_stat.st_size,
                    "extension": os.path.splitext(filename)[1]
                }
                
                # if not status:
                #     index += 1


vfs_by_docId, vfs_by_path = build_virtual_file_system("data")
save_virtual_file_system((vfs_by_docId, vfs_by_path))

vfs_by_docId, vfs_by_path = load_virtual_file_system()
update_virtual_file_system("data", vfs_by_docId, vfs_by_path)

# from pprint import pprint
# pprint(vfs_by_docId)
# print()
# pprint(vfs_by_path)
# print(index)