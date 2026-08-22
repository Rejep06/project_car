"""Не допускает возврат неявных FOR UPDATE рядом с eager LEFT JOIN."""

from __future__ import annotations

import ast
from pathlib import Path


def test_every_with_for_update_has_explicit_target() -> None:
    app_root = Path(__file__).resolve().parents[1] / "app"
    violations: list[str] = []
    for path in app_root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr != "with_for_update":
                continue
            if not any(keyword.arg == "of" for keyword in node.keywords):
                violations.append(f"{path.relative_to(app_root.parent)}:{node.lineno}")
    assert not violations, "Укажите with_for_update(of=Model): " + ", ".join(violations)
