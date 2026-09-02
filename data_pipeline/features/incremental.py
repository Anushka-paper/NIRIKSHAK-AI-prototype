import hashlib
import os

def compute_file_hash(filepath):
    if not os.path.exists(filepath):
        return ""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def compute_row_hash(row_str):
    return hashlib.md5(row_str.encode("utf-8")).hexdigest()
