import os
import shutil

# Path to /root
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Paths to map folders
map_dirs = [
    os.path.join(ROOT_DIR, "log", "custom"),
    os.path.join(ROOT_DIR, "log", "procedural"),
    os.path.join(ROOT_DIR, "log", "string"),
]

def clean_folder(folder):
    if not os.path.exists(folder):
        print(f"Folder not found: {folder}")
        return

    for item in os.listdir(folder):
        item_path = os.path.join(folder, item)

        if os.path.isfile(item_path) or os.path.islink(item_path):
            os.remove(item_path)  # remove file
        elif os.path.isdir(item_path):
            shutil.rmtree(item_path)  # remove subfolder

    print(f"Cleaned: {folder}")

if __name__ == "__main__":
    for folder in map_dirs:
        clean_folder(folder)
