import os
from typing import Tuple

class PathHandler:
    @staticmethod
    def is_file_in_current_directory(path: str) -> bool:
        abs_file_path = os.path.abspath(path)
        abs_cwd = os.path.abspath(os.getcwd())
        # Check if the file's directory is a subdirectory of the current working directory
        rel_path = os.path.relpath(abs_file_path, abs_cwd)
        return not rel_path.startswith('..')

    @staticmethod
    def get_path_to_display(absolute_path: str) -> str:
        """
        Convert an absolute path to a relative path if the file is in current directory,
        otherwise return absolute path.
        """
        # Get absolute path
        abs_path = os.path.abspath(absolute_path)
        
        # If the file is in current directory, return relative path
        if PathHandler.is_file_in_current_directory(abs_path):
            return os.path.relpath(abs_path)
            
        # Otherwise return absolute path
        return abs_path