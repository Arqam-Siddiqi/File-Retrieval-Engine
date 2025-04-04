import os
from pathlib import Path

file = Path("data/file1.txt")
print(os.getcwd())
print(f"Modified: {file.stat().st_mtime}")


virtual_file_system = {}
