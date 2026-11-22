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
    """Cria um item novo a partir de app/templates/catalog/<kind>/."""
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", item_id):
        raise ValueError("O id deve usar snake_case: letras minúsculas, números e _.")
    if not title or len(title) > 40 or any(char in title for char in '"\\\n'):
        raise ValueError("O título deve ter de 1 a 40 caracteres, sem aspas ou barras.")
    folder = root / f"{kind}s" / item_id
    targets = {folder / name: TEMPLATES / kind / name for name in ("item.toml", "handler.py", "README.md")}
    if kind == "agent":
        targets[prompts / f"{item_id}.md"] = TEMPLATES / kind / "prompt.md"
    existing = [str(path) for path in targets if path.exists()]
    if existing:
        raise ValueError("Já existe: " + ", ".join(existing))
    for target, template in targets.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        text = template.read_text(encoding="utf-8").replace("__ID__", item_id).replace("__TITLE__", title)
        target.write_text(text, encoding="utf-8")
    return list(targets)


def main():
    parser = argparse.ArgumentParser(description="Catálogo de agentes e ferramentas")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="Lista os itens e seu estado")
    commands.add_parser("check", help="Valida todos os itens contra o padrão do catálogo")
    new = commands.add_parser("new", help="Cria um item a partir do modelo padrão")
    new.add_argument("type", choices=("agent", "tool"))
    new.add_argument("id", help="Identificador em snake_case, igual ao nome da pasta")
    new.add_argument("--title", required=True, help="Nome exibido na interface (até 40 caracteres)")
    for name in ("run", "enable", "disable"):
        command = commands.add_parser(name)
        command.add_argument("id")
        if name == "run":
            command.add_argument("--input", help="Objeto JSON ou - para stdin")
            command.add_argument("--example", type=int, help="Executa o exemplo N (a partir de 1) do item.toml")
    args = parser.parse_args()

    if args.command == "new":
        try:
            created = scaffold(args.type, args.id, args.title)
        except ValueError as exc:
            parser.error(str(exc))
        for path in created:
            print(path.relative_to(ROOT.parent))
        print("Preencha os arquivos e rode: uv run --locked python -m app.catalog_cli check")
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
            parser.error("Item desconhecido.")
        if args.command == "run":
            if (args.input is None) == (args.example is None):
                parser.error("Informe --input ou --example.")
            try:
                if args.example is not None:
                    if not 1 <= args.example <= len(item.examples):
                        parser.error(f"O item tem {len(item.examples)} exemplo(s).")
                    payload = item.examples[args.example - 1].input
                else:
                    payload = json.loads(sys.stdin.read() if args.input == "-" else args.input)
                if not isinstance(payload, dict):
                    parser.error("A entrada deve ser um objeto JSON.")
                result = asyncio.run(execute(item, "cli", payload)).model_dump(mode="json")
            except ValueError as exc:
                parser.error(str(exc))
            except Exception as exc:
                parser.exit(1, f"Falha de execução ({type(exc).__name__}).\n")
        else:
            active = args.command == "enable"
            set_active(item.id, active)
            result = {"id": item.id, "active": active}
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
