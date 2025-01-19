import json
import os
import shutil
from typing import List, Dict, Optional

class SweContext:
    def __init__(self):
        self.swe_dir = os.path.join(os.path.expanduser("~"), ".swe")
        self.context_path = os.path.join(self.swe_dir, "context.json")
        self.ignore_path = os.path.join(self.swe_dir, ".sweignore")
        self.default_ignores = [
            ".git/",
            "__pycache__/",
            "*.pyc",
            ".DS_Store",
            "node_modules/",
            "venv/",
            ".env/",
            ".idea/",
            ".vscode/",
            "dist/",
            ".gitignore",
            "poetry.lock",
            ".pytest_cache/",
        ]

    def init(self) -> None:
        os.makedirs(self.swe_dir, exist_ok=True)
        if not os.path.exists(self.context_path):
            with open(self.context_path, "w") as f:
                json.dump({"context": []}, f)
        if not os.path.exists(self.ignore_path):
            with open(self.ignore_path, "w") as f:
                f.write("\n".join(self.default_ignores))
        print(f"🎉 Initialized SWE coding agent.")

    def _load_context(self) -> Optional[Dict[str, List[str]]]:
        if not os.path.exists(self.context_path):
            self.init()
        with open(self.context_path, "r") as f:
            return json.load(f)

    def _save_context(self, data: Dict[str, List[str]]) -> None:
        with open(self.context_path, "w") as f:
            json.dump(data, f)
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read(1024)
                return True
        except (UnicodeDecodeError, IOError, OSError):
    def _is_readable_file(self, file_path: str) -> bool:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read(1024)
                return True
        except (UnicodeDecodeError, IOError, OSError):
            return False

    def _should_ignore(self, path: str) -> bool:
        try:
            with open(self.ignore_path, 'r') as f:
                ignore_patterns = [p.strip() for p in f.readlines() if p.strip() and not p.startswith('#')]
        except FileNotFoundError:
            ignore_patterns = self.default_ignores

        norm_path = os.path.normpath(path)
        
        for pattern in ignore_patterns:
            if pattern.endswith('/'):
                pattern = pattern[:-1]
            
            if pattern.startswith('*'):
                if norm_path.endswith(pattern[1:]):
                    return True
            elif pattern in norm_path:
                return True
        
        return False

    def add(self, path: str) -> None:
        if not os.path.exists(path):
            print(f"Path {path} does not exist.")
            return
        
        data = self._load_context()
        if data is None:
            return
            
        if os.path.isfile(path):
            rel_path = os.path.relpath(path)
            if rel_path not in data["context"] and self._is_readable_file(path):
                data["context"].append(rel_path)
                self._save_context(data)
                print(f"Added {rel_path} to context.")
        else:
            added_files = 0
            for root, _, files in os.walk(path):
                if self._should_ignore(root):
                    continue
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path)
                    if not self._should_ignore(rel_path):
                        if rel_path not in data["context"] and self._is_readable_file(file_path):
                            data["context"].append(rel_path)
                            added_files += 1
            if added_files > 0:
                self._save_context(data)
                print(f"Added {added_files} files from {path} to context.")
            else:
                print(f"No new files found in {path}.")

    def remove(self, path: str) -> None:
        data = self._load_context()
        if data is None:
            return
            
        norm_path = os.path.normpath(path)
        
        if os.path.isfile(norm_path):
            if norm_path in data["context"]:
                data["context"].remove(norm_path)
                self._save_context(data)
                print(f"Removed {norm_path} from context.")
            else:
                print(f"File {norm_path} not in context.")
        else:
            original_count = len(data["context"])
            data["context"] = [f for f in data["context"] 
                             if not os.path.normpath(f).startswith(norm_path)]
            removed_files = original_count - len(data["context"])
            self._save_context(data)
            
            if removed_files > 0:
                print(f"Removed {removed_files} files from {norm_path} and its subdirectories.")
            else:
                print(f"No files from {norm_path} were in context.")

    def forget_all(self) -> None:
        data = self._load_context()
        if data is None:
            return
        data["context"] = []
        self._save_context(data)
        print("All files removed from context.")

    def list_context(self) -> None:
        data = self._load_context()
        if data is None:
            return
        for file in data["context"]:
            print(f"    +  {file}")

    def uninstall(self) -> None:
        if os.path.exists(self.swe_dir):
            shutil.rmtree(self.swe_dir)
            print(f"✅ Uninstalled SWE coding agent.")
        else:
            print("SWE coding agent is not installed.")
    def clear_conversation(self) -> None:
        try:
            if os.path.exists(self.chat_file):
                os.remove(self.chat_file)
            print("Conversation history cleared.")
        except IOError as e:
            print(f"Error clearing conversation history: {e}")

    def print_chat(self) -> None:
        chat_history = self._load_chat_history()
        for msg in chat_history:
            print(f'{msg["role"].capitalize()}: {msg["content"]}')
