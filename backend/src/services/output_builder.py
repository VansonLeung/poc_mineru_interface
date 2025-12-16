from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from src.services.mineru_adapter import MineruOutputPaths
from src.services.storage import StorageManager


class OutputBuilder:
    def __init__(self, storage: StorageManager) -> None:
        self.storage = storage

    def build(self, job_id: str, mineru_outputs: List[MineruOutputPaths]) -> list[dict]:
        expiry = self.storage.expiry_at().isoformat()
        results: list[dict] = []
        for output in mineru_outputs:
            results.append(
                {
                    "filename": output.filename,
                    "markdown": self._read_text(output.markdown),
                    "markdown_url": None,
                    "content_list_json": self._read_json(output.content_list),
                    "content_list_url": None,
                    "middle_json": self._read_json(output.middle_json),
                    "middle_json_url": None,
                    "model_output_json": self._read_json(output.model_output),
                    "model_output_url": None,
                    "storage_expiry": expiry,
                }
            )
        return results

    def _read_text(self, path: Optional[Path]) -> str | None:
        if not path:
            return None
        return Path(path).read_text(encoding="utf-8")

    def _read_json(self, path: Optional[Path]):
        if not path:
            return None
        return json.loads(Path(path).read_text(encoding="utf-8"))
