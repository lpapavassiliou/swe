# Swe

Swe is a coding agent that manages context and answers questions using Language Learning Models (LLMs). It uses the OpenAI GPT-4 model to generate responses based on the context provided.

## Features

- Manage context by adding and removing files or directories.
- Ask questions using the current context.
- Initialize a global .swe folder in the user's home directory.
- List all files in the current context.
- Clear all files from the current context.

## Installation

To install Swe, follow these steps:

```bash
conda create -n swe python=3.11
poetry install
poetry build
pipx install dist/swe-0.1.0.tar.gz
```

## Usage

Here are some commands you can use with Swe:

- Initialize the global .swe folder in the user's home directory:

```bash
swe init
```

- Add a file or directory to the context:

```bash
swe add <path>
```

- Remove a file or directory from the context:

```bash
swe remove <path>
```

- Answer a question using the context:

```bash
swe ask <question>
```

- List all files in the current context:

```bash
swe list
```

- Clear all files from the current context:

```bash
swe clear
```

## Testing

To run the tests, use the following command:

```bash
poetry run pytest tests/
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.