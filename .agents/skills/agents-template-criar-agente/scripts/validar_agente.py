"""Validate authoring conventions and loading, without invoking an LLM.

Run from the repository root; accepts agent files outside app/assets/agents too.
"""

import argparse
import importlib
import re
import sys
from pathlib import Path
from unittest.mock import patch


def validate(path: Path, project_root: Path) -> list[str]:
    sys.path.insert(0, str(project_root.resolve()))
    util = importlib.import_module("app.orchestration.util")
    errors = []
    with patch.object(util, "DEFAULT_AGENTS_FOLDER", path.resolve().parent):
        try:
            parsed = util.load_agent_markdown(path.stem)
            metadata = parsed["metadata"]
            sections = parsed["sections"]
            if not isinstance(metadata, dict):
                return ["O frontmatter precisa ser um mapeamento YAML."]
            if metadata.get("id") != path.stem:
                errors.append("O id deve coincidir com o nome do arquivo.")
            if not re.fullmatch(r"[a-z0-9]+(?:_[a-z0-9]+)*", path.stem):
                errors.append("Use letras minúsculas, números e underscores no id.")
            for field in ("role", "goal"):
                value = metadata.get(field)
                if not isinstance(value, str) or not value.strip():
                    errors.append(f"Preencha {field} com texto.")
            for section in ("input", "output", "instructions", "knowledge"):
                if not sections.get(section, "").strip():
                    errors.append(f"Preencha a seção {section.upper()}.")
            tokens = metadata.get("max_tokens", 2048)
            if type(tokens) is not int or tokens <= 0:
                errors.append("max_tokens deve ser um inteiro positivo ou ser omitido.")
            model = metadata.get("model")
            if model is not None and not isinstance(model, str):
                errors.append("model deve ser texto ou ser omitido.")
            config = util.load_agent_config(path.stem, fallback_model="validation-model")
            if not isinstance(config["model"], str):
                errors.append("O modelo resolvido precisa ser texto.")
        except Exception as exc:
            errors.append(f"Falha no carregamento: {type(exc).__name__}: {exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    if not (args.project_root / "app/orchestration/util.py").is_file():
        parser.error("Execute na raiz do projeto ou informe --project-root.")
    failed = False
    for path in args.files:
        errors = validate(path, args.project_root)
        failed = failed or bool(errors)
        print(f"{'ERRO' if errors else 'OK'}: {path}")
        for error in errors:
            print(f"  - {error}")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
