# Swe

Swe is a coding agent to manage context and answer questions using LLMs.

## Commands

- `swe init`: Initialize the global .swe folder in the user's home directory.
- `swe add <path>`: Add a file or directory to the context.
- `swe remove <path>`: Remove a file or directory from the context.
- `swe ask <question>`: Answer a question using the context.

## Installation

```bash
conda create -n swe python=3.11
poetry install
poetry build
pipx install dist/swe-0.1.0.tar.gz
```
