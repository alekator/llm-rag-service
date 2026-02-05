from __future__ import annotations

import os
import uuid
from pathlib import Path


class LocalStorage:
    def __init__(self, base_dir: str = "data/uploads") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_bytes(self, *, document_id: uuid.UUID, filename: str, data: bytes) -> Path:
        safe_name = os.path.basename(filename)
        path = self.base_dir / f"{document_id}_{safe_name}"
        path.write_bytes(data)
        return path
