import argparse
from swe.context import SweContext
from swe.ask import SweAsk
from swe.implement import SweImplement


def main():
    parser = argparse.ArgumentParser(description="SWE coding agent")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("init")
    look_parser = subparsers.add_parser("look")  # Renamed from "add"
    look_parser.add_argument("file", help="File to add to context")
    forget_parser = subparsers.add_parser("forget")  # Renamed from "rm"
    forget_parser.add_argument("file", help="File to remove from context")
    ask_parser = subparsers.add_parser("ask")
    ask_parser.add_argument("question", help="Question to ask using context")
    ask_parser.add_argument("--verbose", action="store_true", help="Print verbose output")
    subparsers.add_parser("context", help="List all files in context")
    subparsers.add_parser("clear", help="Remove all files from context")
    subparsers.add_parser("uninstall", help="Uninstall the SWE coding agent")
    subparsers.add_parser("new", help="Start a new chat")
    implement_parser = subparsers.add_parser("implement")
    implement_parser.add_argument("question", help="Implementation request")
    implement_parser.add_argument("--verbose", action="store_true", help="Print verbose output")
    chat_parser = subparsers.add_parser("chat", help="Print the chat history")

    args = parser.parse_args()

    swe_context = SweContext()
    swe_ask = SweAsk(swe_context)
    swe_implement = SweImplement(swe_context)

    if args.command == "init":
        swe_context.init()
    elif args.command == "look":  # Changed from "add"
        swe_context.add_file(args.file)
    elif args.command == "forget":  # Changed from "rm"
        swe_context.remove_file(args.file)
    elif args.command == "ask":
        swe_ask.ask(args.question, args.verbose)
    elif args.command == "context":
        swe_context.show_context()
    elif args.command == "forget_all":
        swe_context.remove_all_files()
    elif args.command == "uninstall":
        swe_context.uninstall()
    elif args.command == "clear":  # Handle new command
        swe_context.clear_conversation()
    elif args.command == "implement":
        swe_implement.implement(args.question, args.verbose)
    elif args.command == "chat":
        swe_ask.print_chat()
    else:
        parser.print_help()