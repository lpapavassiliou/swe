import argparse
from swe.context import SweContext
from swe.ask import SweAsk


def main():
    parser = argparse.ArgumentParser(description="SWE coding agent")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("init")
    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("file", help="File to add to context")
    forget_parser = subparsers.add_parser("rm")
    forget_parser.add_argument("file", help="File to remove from context")
    ask_parser = subparsers.add_parser("ask")
    ask_parser.add_argument("question", help="Question to ask using context")
    ask_parser.add_argument("--verbose", action="store_true", help="Print verbose output")
    subparsers.add_parser("context", help="List all files in context")
    subparsers.add_parser("clear", help="Remove all files from context")
    subparsers.add_parser("uninstall", help="Uninstall the SWE coding agent")
    subparsers.add_parser("new", help="Start a new chat")

    args = parser.parse_args()

    swe_context = SweContext()
    swe_ask = SweAsk(swe_context)

    if args.command == "init":
        swe_context.init()
    elif args.command == "add":
        swe_context.add(args.file)
    elif args.command == "rm":
        swe_context.remove(args.file)
    elif args.command == "ask":
        swe_ask.ask(args.question, args.verbose)
    elif args.command == "context":
        swe_context.list_context()
    elif args.command == "clear":
        swe_context.forget_all()
    elif args.command == "uninstall":
        swe_context.uninstall()
    elif args.command == "new":  # Handle new command
        swe_ask.clear_conversation()
    else:
        parser.print_help()