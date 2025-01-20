import argparse
from swe.context import SweContext
from swe.ask import SweAsk
from swe.implement import SweImplement


def main():
    parser = argparse.ArgumentParser(description="SWE coding agent")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("init")
    add_parser = subparsers.add_parser("add")  # Renamed from "add"
    add_parser.add_argument("file", help="File to add to context")
    remove_parser = subparsers.add_parser("rm")  # Renamed from "rm"
    remove_parser.add_argument("file", nargs='?', default=None, help="File to remove from context")
    remove_parser.add_argument("--all", action="store_true", help="Remove all files from context")
    ask_parser = subparsers.add_parser("ask")
    ask_parser.add_argument("question", help="Question to ask the agent")
    ask_parser.add_argument("--verbose", action="store_true", help="Print verbose output")
    subparsers.add_parser("context", help="List all files in context")
    subparsers.add_parser("ls", help="List all files in context")
    subparsers.add_parser("ctx", help="List all files in context")
    subparsers.add_parser("new", help="Start a new chat")
    subparsers.add_parser("clear_config", help="Delete the SWE coding agent configuration")
    subparsers.add_parser("chat", help="Print the chat history")
    implement_parser = subparsers.add_parser("implement")
    implement_parser.add_argument("question", help="Implementation request")
    implement_parser.add_argument("--verbose", action="store_true", help="Print verbose output")

    args = parser.parse_args()

    swe_context = SweContext()
    swe_ask = SweAsk(swe_context)
    swe_implement = SweImplement(swe_context)

    if args.command == "init":
        swe_context.init()
    elif args.command == "add":
        swe_context.add_file(args.file)
    elif args.command == "rm":
        if args.all:
            swe_context.remove_all_files()
        elif args.file:
            swe_context.remove_file(args.file)
        else:
            print("Please specify a file to remove or use --all to remove all files.")
    elif args.command == "ask":
        swe_ask.ask(args.question, args.verbose)
    elif args.command in ["context", "ls", "ctx"]:
        swe_context.show_context()
    elif args.command == "clear_config":
        swe_context.delete_configuration_folder()
    elif args.command == "new":  # Handle new command
        swe_context.clear_conversation()
    elif args.command == "implement":
        swe_implement.implement(args.question, args.verbose)
    elif args.command == "chat":
        swe_context.print_chat()
    else:
        parser.print_help()