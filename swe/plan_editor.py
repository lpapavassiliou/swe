import os


class PlanEditor:

    def __init__(self):
        self.file_path = os.path.join(os.path.expanduser('~'), '.swe', 'planner.txt')
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

    def set_content(self, content: str) -> None:
        with open(self.file_path, 'w') as f:
            f.write(content)

    def append_content(self, content: str) -> None:
        with open(self.file_path, 'a') as f:
            f.write(content + '\n')

    def get_content(self) -> str:
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as f:
                return f.read()
        else:
            return ''

    def empty_content(self) -> None:
        if os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                f.write('')