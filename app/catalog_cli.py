import argparse
import asyncio
import json
import re
import sys
from pathlib import Path

from app.catalog import (
    AGENT_PROMPTS,
    ROOT,
    ItemError,
    activation,
    apply_bulk,
    check,
    configured_channels,
    discover,
    execute,
)

TEMPLATES = ROOT / "templates" / "catalog"


def scaffold(kind: str, item_id: str, title: str, root: Path = ROOT, prompts: Path = AGENT_PROMPTS) -> list[Path]:
    """Create a new item from app/templates/catalog/<kind>/."""
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", item_id):
        raise ValueError("The id must be snake_case: lowercase letters, digits and _.")
    if not title or len(title) > 40 or any(char in title for char in '"\\\n'):
        raise ValueError("The title must have 1 to 40 characters, without quotes or backslashes.")
    folder = root / f"{kind}s" / item_id
    targets = {folder / name: TEMPLATES / kind / name for name in ("item.toml", "handler.py", "README.md")}
    if kind == "agent":
        targets[prompts / f"{item_id}.md"] = TEMPLATES / kind / "prompt.md"
    existing = [str(path) for path in targets if path.exists()]
    if existing:
        raise ValueError("Already exists: " + ", ".join(existing))
    for target, template in targets.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        text = template.read_text(encoding="utf-8").replace("__ID__", item_id).replace("__TITLE__", title)
        target.write_text(text, encoding="utf-8")
    return list(targets)


def main():
    parser = argparse.ArgumentParser(description="Catalog of agents and tools")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="List items and their state")
    commands.add_parser("check", help="Validate every item against the catalog standard")
    new = commands.add_parser("new", help="Create an item from the standard template")
    new.add_argument("type", choices=("agent", "tool"))
    new.add_argument("id", help="snake_case identifier, same as the folder name")
    new.add_argument("--title", required=True, help="Name shown in the dashboard (up to 40 characters)")
    run = commands.add_parser("run", help="Run an item")
    run.add_argument("id")
    run.add_argument("--input", help="JSON object, or - to read stdin")
    run.add_argument("--example", type=int, help="Run example N (starting at 1) from item.toml")
    for name, verb in (("enable", "Enable"), ("disable", "Disable")):
        command = commands.add_parser(
            name, help=f"{verb} items, or turn a channel {'on' if name == 'enable' else 'off'} for them")
        command.add_argument("ids", nargs="*", metavar="id", help="Item ids (or use --all / --type)")
        command.add_argument("--all", action="store_true", help="Every item")
        command.add_argument("--type", choices=("agent", "tool"), help="Every item of this type")
        command.add_argument("--channel", choices=("api", "cli", "mcp"),
                             help=f"{verb} this channel instead of the item itself")
    args = parser.parse_args()

    if args.command == "new":
        try:
            created = scaffold(args.type, args.id, args.title)
        except ValueError as exc:
            parser.error(str(exc))
        for path in created:
            print(path.relative_to(ROOT.parent))
        print("Next: fill in the files (see docs/catalog-standards.md), then run: uv run --locked python -m app catalog check")
        return

    items = discover()
    if args.command == "check":
        failed = False
        for item in items.values():
            problems = check(item)
            failed |= bool(problems)
            print(("FAIL  " if problems else "OK    ") + item.id)
            for problem in problems:
                print("  - " + problem)
        sys.exit(1 if failed else 0)

    if args.command == "list":
        state = activation()
        result = [
            dict(
                item.model_dump(mode="json", exclude={"examples"}),
                channels=sorted(configured_channels(item)),
                active=bool(state.get(item.id, True)),
            )
            for item in items.values()
        ]
    elif args.command in ("enable", "disable"):
        if args.ids and (args.all or args.type):
            parser.error("Give item ids, or --all / --type, not both.")
        if args.all or args.type:
            selected = [item for item in items.values() if not args.type or item.type == args.type]
        elif args.ids:
            unknown = [item_id for item_id in args.ids if item_id not in items]
            if unknown:
                parser.error("Unknown item: " + ", ".join(unknown))
            selected = [items[item_id] for item_id in dict.fromkeys(args.ids)]
        else:
            parser.error("Give one or more item ids, --all or --type.")
        on = args.command == "enable"
        if args.channel:
            result = apply_bulk(selected, enable_channels={args.channel} if on else set(),
                                disable_channels=set() if on else {args.channel})
        else:
            result = apply_bulk(selected, active=on)
        if len(args.ids) == 1 and not (args.all or args.type):
            result = result[0]
    else:
        item = items.get(args.id)
        if item is None:
            parser.error("Unknown item.")
        if args.command == "run":
            if (args.input is None) == (args.example is None):
                parser.error("Provide --input or --example.")
            try:
                if args.example is not None:
                    if not 1 <= args.example <= len(item.examples):
                        parser.error(f"The item has {len(item.examples)} example(s).")
                    payload = item.examples[args.example - 1].input
                else:
                    payload = json.loads(sys.stdin.read() if args.input == "-" else args.input)
                if not isinstance(payload, dict):
                    parser.error("The input must be a JSON object.")
                result = asyncio.run(execute(item, "cli", payload)).model_dump(mode="json")
            except (ValueError, ItemError) as exc:
                parser.error(str(exc))
            except Exception as exc:
                parser.exit(1, f"Execution failed ({type(exc).__name__}).\n")
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
