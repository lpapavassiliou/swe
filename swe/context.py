import os
import json

class SweContext:
    def __init__(self):
        # Store the .swe folder in the user's home directory
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
        ]

    def init(self):
        if not os.path.exists(self.swe_dir):
            os.makedirs(self.swe_dir)
        if not os.path.exists(self.context_path):
            with open(self.context_path, "w") as f:
                json.dump({"context": []}, f)
        if not os.path.exists(self.ignore_path):
            with open(self.ignore_path, "w") as f:
                f.write("\n".join(self.default_ignores))
        print(f"Initialized global .swe folder at {self.swe_dir}")

    def _load_context(self):
        if not os.path.exists(self.context_path):
            self.init()
        with open(self.context_path, "r") as f:
            return json.load(f)

    def _save_context(self, data):
        with open(self.context_path, "w") as f:
            json.dump(data, f)

    def _is_readable_file(self, file_path):
        """Check if the file exists and is readable."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Try to read a small chunk to verify it's readable text
                f.read(1024)
                return True
        except (UnicodeDecodeError, IOError, OSError):
            return False

    def _should_ignore(self, path):
        """Check if a path should be ignored based on .sweignore rules."""
        try:
            with open(self.ignore_path, 'r') as f:
                ignore_patterns = [p.strip() for p in f.readlines() if p.strip() and not p.startswith('#')]
        except FileNotFoundError:
            ignore_patterns = self.default_ignores

        norm_path = os.path.normpath(path)
        
        for pattern in ignore_patterns:
            # Remove trailing slash for directory patterns
            if pattern.endswith('/'):
                pattern = pattern[:-1]
            
            # Simple wildcard matching
            if pattern.startswith('*'):
                if norm_path.endswith(pattern[1:]):
                    return True
            elif pattern in norm_path:
                return True
        
        return False

    def add(self, path):
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
        else:  # It's a directory
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

    def remove(self, path):
        data = self._load_context()
        if data is None:
            return
            
        # Normalize the input path
        norm_path = os.path.normpath(path)
        
        if os.path.isfile(norm_path):
            # Handle single file removal
            if norm_path in data["context"]:
                data["context"].remove(norm_path)
                self._save_context(data)
                print(f"Removed {norm_path} from context.")
            else:
                print(f"File {norm_path} not in context.")
        else:  # It's a directory
            # Remove all files that start with this directory path
            original_count = len(data["context"])
            # Normalize all paths in context for comparison
            data["context"] = [f for f in data["context"] 
                             if not os.path.normpath(f).startswith(norm_path)]
            removed_files = original_count - len(data["context"])
            self._save_context(data)
            
            if removed_files > 0:
                print(f"Removed {removed_files} files from {norm_path} and its subdirectories.")
            else:
                print(f"No files from {norm_path} were in context.")

    def forget_all(self):
        data = self._load_context()
        if data is None:
            return
        data["context"] = []
        self._save_context(data)
        print("All files removed from context.")

    def list(self):
        data = self._load_context()
        if data is None:
            return
        print("In context:")
        for file in data["context"]:
            print(file)
