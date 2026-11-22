import argparse
import asyncio
import json
import re
import sys
from pathlib import Path

from app.catalog import (
    AGENT_PROMPTS,
    ROOT,
    activation,
    check,
    configured_channels,
    discover,
    execute,
    set_active,
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
    for name in ("run", "enable", "disable"):
        command = commands.add_parser(name)
        command.add_argument("id")
        if name == "run":
            command.add_argument("--input", help="JSON object, or - to read stdin")
            command.add_argument("--example", type=int, help="Run example N (starting at 1) from item.toml")
    args = parser.parse_args()

    if args.command == "new":
        try:
            created = scaffold(args.type, args.id, args.title)
        except ValueError as exc:
            parser.error(str(exc))
        for path in created:
            print(path.relative_to(ROOT.parent))
        print("Fill in the files, then run: uv run --locked python -m app.catalog_cli check")
        return

    items = discover()
    if args.command == "check":
        failed = False
        for item in items.values():
            problems = check(item)
            failed |= bool(problems)
            print(("FALHA " if problems else "OK    ") + item.id)
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
            except ValueError as exc:
                parser.error(str(exc))
            except Exception as exc:
                parser.exit(1, f"Execution failed ({type(exc).__name__}).\n")
        else:
            active = args.command == "enable"
            set_active(item.id, active)
            result = {"id": item.id, "active": active}
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
