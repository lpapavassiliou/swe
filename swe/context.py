import json
import os
import shutil
from typing import List, Dict, Optional
import tiktoken
from swe.paths import PathHandler

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
        self.chat_file = os.path.join(os.path.expanduser("~"), ".swe", "chat.json")
        os.makedirs(os.path.dirname(self.chat_file), exist_ok=True)

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

    def _get_context_content(self, verbose: bool = False) -> str:
        data = self._load_context()
        if data is None or not data.get("context"):
            print("No context files available. Use 'swe add <file>' to add files.")
            return ""

        context_content = ""
        for file in data["context"]:
            try:
                if verbose:
                    print(f"Reading file: {file}")
                with open(file, "r") as f:
                    file_content = f.read()
                    file_title = PathHandler.get_path_to_display(file)
                    context_content += f"\n\n### File: {file_title}\n\n{file_content}\n"
            except Exception as e:
                print(f"Warning: Could not read {file}, removed from context.")
                self.remove_file(file)
        return context_content

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
    
    def _load_chat_history(self) -> List[Dict[str, str]]:
        if os.path.exists(self.chat_file):
            try:
                with open(self.chat_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                print("Warning: Could not read or parse chat history. Starting fresh.")
        return []

    def _save_chat_history(self, chat_history: List[Dict[str, str]]) -> None:
        try:
            with open(self.chat_file, 'w') as f:
                json.dump(chat_history, f, indent=4)
        except IOError as e:
            print(f"Error saving chat history: {e}")

    def add_file(self, path: str) -> None:
        if not os.path.exists(path):
            print(f"Path {path} does not exist.")
            return
        
        data = self._load_context()
        if data is None:
            return
            
        if os.path.isfile(path):
            abs_path = os.path.abspath(path)
            if abs_path not in data["context"] and self._is_readable_file(path):
                data["context"].append(abs_path)
                self._save_context(data)
                path_to_display = PathHandler.get_path_to_display(abs_path)
                print(f"Added {path_to_display} to context.")
        else:
            added_files = 0
            for root, _, files in os.walk(path):
                if self._should_ignore(root):
                    continue
                for file in files:
                    file_path = os.path.join(root, file)
                    abs_path = os.path.abspath(file_path)
                    if not self._should_ignore(abs_path):
                        if abs_path not in data["context"] and self._is_readable_file(file_path):
                            data["context"].append(abs_path)
                            added_files += 1
            if added_files > 0:
                self._save_context(data)
                print(f"Added {added_files} files from {path} to context.")
            else:
                print(f"No new files found in {path}.")

    def remove_file(self, path: str) -> None:
        data = self._load_context()
        if data is None:
            return
        
        absolute_path = os.path.abspath(path)
        path_to_display = PathHandler.get_path_to_display(absolute_path)
        
        if os.path.isfile(absolute_path):
            if absolute_path in data["context"]:
                data["context"].remove(absolute_path)
                self._save_context(data)
                print(f"Removed {path_to_display} from context.")
            else:
                print(f"File {path_to_display} not in context.")
        else:
            original_count = len(data["context"])
            data["context"] = [f for f in data["context"] 
                             if not os.path.normpath(f).startswith(absolute_path)]
            removed_files = original_count - len(data["context"])
            self._save_context(data)
            
            if removed_files > 0:
                print(f"Removed {removed_files} files from {absolute_path} and its subdirectories.")
            else:
                print(f"No files from {absolute_path} were in context.")

    def remove_all_files(self) -> None:
        data = self._load_context()
        if data is None:
            return
        data["context"] = []
        self._save_context(data)
        print("All files removed from context.")

    def show_context(self) -> None:
        self._display_token_usage()
        data = self._load_context()
        if data is None:
            return
        for file in data["context"]:
            print(f"    +  {PathHandler.get_path_to_display(file)}")

    def delete_configuration_folder(self) -> None:
        if os.path.exists(self.swe_dir):
            shutil.rmtree(self.swe_dir)
            print(f"✅ Deleted configuration folder.")
        else:
            print("There is no configuration folder to delete.")

    @staticmethod
    def _count_tokens(text, model='gpt-4o'):
        # Load the appropriate tokenizer for the specified model
        encoding = tiktoken.encoding_for_model(model)
        # Encode the text to get tokens
        tokens = encoding.encode(text)
        # Return the number of tokens
        return len(tokens)
    
    def _display_token_usage(self, model='gpt-4o'):
        # Get terminal width for dynamic bar size
        terminal_width, _ = shutil.get_terminal_size()
        bar_width = max(30, terminal_width - 40)  # Adjust bar width based on terminal size

        # Get token usage
        context_content = self._get_context_content()
        context_tokens = self._count_tokens(context_content, model)
        chat_history = self._load_chat_history()
        formatted_history = "\n".join([f'{msg["role"].capitalize()}: {msg["content"]}' for msg in chat_history])
        chat_tokens = self._count_tokens(formatted_history, model)

        # Total tokens and max tokens
        total_tokens = context_tokens + chat_tokens
        max_tokens = 30000000

        # Calculate bar splits
        context_ratio = context_tokens / max_tokens
        chat_ratio = chat_tokens / max_tokens

        context_fill = int(context_ratio * bar_width)
        chat_fill = int(chat_ratio * bar_width)
        empty_fill = bar_width - (context_fill + chat_fill)

        # Construct the bar
        context_bar = '█' * context_fill
        chat_bar = '█' * chat_fill
        empty_bar = '░' * empty_fill
        divider = '|'

        # Combine the sections
        loading_bar = f"[{context_bar}{divider}{chat_bar}{divider}{empty_bar}]"

        # Display output
        print(f"Token Usage: {(total_tokens / max_tokens) * 100:.2f}%")
        print(f"{loading_bar}")
        
    def clear_conversation(self) -> None:
        try:
            if os.path.exists(self.chat_file):
                os.remove(self.chat_file)
            print("🎉 Start a new chat.")
        except IOError as e:
            print(f"Error clearing conversation history: {e}")

    def print_chat(self) -> None:
        chat_history = self._load_chat_history()
        for msg in chat_history:
            print(f'{msg["role"].capitalize()}: {msg["content"]}')
