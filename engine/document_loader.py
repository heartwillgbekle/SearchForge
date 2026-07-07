from pathlib import Path


def load_documents(folder_path):
    documents = {}

    folder = Path(folder_path)

    for file_path in folder.glob("*.txt"):
        with open(file_path, "r", encoding="utf-8") as file:
            documents[file_path.name] = file.read()

    return documents
