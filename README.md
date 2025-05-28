# Swe

Swe is a coding agent that manages context and answers questions using Language Learning Models (LLMs). It uses the OpenAI GPT-4o-mini model to generate responses based on the context provided.

## Features

- Manage context by adding and removing files or directories.
- Ask questions using the current context.
- Initialize a global .swe folder in the user's home directory.
- List all files in the current context.
- Clear all files from the current context.
- Uninstall the SWE coding agent.

## Installation

To install Swe, follow these steps:

```bash
conda create -n swe-venv python=3.11
conda activate swe-venv
install-swe
```

## Usage

Here are some commands you can use with Swe:

- Add a file or directory to the context:

```bash
swe add <path>
```

- Remove a file or directory from the context:

```bash
swe rm <path>
```

- Remove all files from the context:

```bash
swe rm --all
```

- Start a new session (clear context and start a new chat):

```bash
swe new
```

- Start a new conversation:

```bash
swe newchat
```

- Answer a question using the context:

```bash
swe ask <question>
```

- List all files in the current context:

```bash
swe ctx
```

- Clear all files from the current context:

```bash
swe clear
```

- Update the SWE coding agent:

```bash
update-swe
```

- Uninstall the SWE coding agent:

```bash
uninstall-swe
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