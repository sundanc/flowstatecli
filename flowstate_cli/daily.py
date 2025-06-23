# flowstate_cli/daily.py

from pathlib import Path
from datetime import datetime
from typing import List, Dict
import json

class DailyTaskBuffer:
    def __init__(self):
        self.buffer_file = Path.home() / ".flowstate-daily.json"

    def _load_tasks(self) -> List[Dict]:
        if self.buffer_file.exists():
            try:
                with self.buffer_file.open("r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return []
        return []

    def _save_tasks(self, tasks: List[Dict]) -> None:
        with self.buffer_file.open("w") as f:
            json.dump(tasks, f, indent=2)

    def add_task(self, description: str) -> None:
        tasks = self._load_tasks()
        tasks.append({
            "description": description,
            "created_at": datetime.now().isoformat()
        })
        self._save_tasks(tasks)

    def get_tasks(self) -> List[Dict]:
        return self._load_tasks()

    def clear_tasks(self) -> None:
        if self.buffer_file.exists():
            self.buffer_file.unlink()

# Important: global instance
daily = DailyTaskBuffer()
