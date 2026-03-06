from pathlib import Path
from typing import Iterable, List

CPP_EXTS = {".c", ".cc", ".cpp", ".cxx"}

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def list_source_files(root: Path) -> List[Path]:
    files: List[Path] = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in CPP_EXTS:
            files.append(p)
    return files

def relpath(p: Path, base: Path) -> str:
    try:
        return str(p.relative_to(base))
    except Exception:
        return str(p)