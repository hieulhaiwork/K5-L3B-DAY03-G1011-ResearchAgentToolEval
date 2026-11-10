"""Contract tests: tools.yaml (what the MODEL sees) must match the Python code (what RUNS).

These pass on the starter code. Keep them green every time you rename, add, or change a tool.
"""
from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest
import yaml

from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools

ROOT = Path(__file__).resolve().parents[1]
DECLARATIONS = load_tool_declarations(ROOT / "artifacts" / "tools.yaml")
DECLARED = {item["name"]: item for item in DECLARATIONS}
EVAL_FILES = ["eval_base.json", "eval_group.json", "eval_research_extension.json"]


def test_tool_names_are_unique() -> None:
    names = [item["name"] for item in DECLARATIONS]
    assert len(names) == len(set(names))


@pytest.mark.parametrize("name", sorted(DECLARED))
def test_every_declared_tool_has_implementation(name: str) -> None:
    assert name in TOOL_FUNCTIONS, f"'{name}' is in tools.yaml but not registered in tools/__init__.py"


@pytest.mark.parametrize("name", sorted(DECLARED))
def test_declared_params_exist_in_function_signature(name: str) -> None:
    """If the model sends an arg the function does not accept, the call crashes with TypeError."""
    func = TOOL_FUNCTIONS[name]
    accepted = set(inspect.signature(func).parameters)
    declared = set(DECLARED[name].get("parameters", {}).get("properties", {}))
    assert declared <= accepted, f"{name}: declared but not accepted by {func.__name__}: {declared - accepted}"


@pytest.mark.parametrize("name", sorted(DECLARED))
def test_required_params_are_declared(name: str) -> None:
    params = DECLARED[name].get("parameters", {})
    missing = set(params.get("required", [])) - set(params.get("properties", {}))
    assert not missing, f"{name}: required but not in properties: {missing}"


@pytest.mark.parametrize("name", sorted(DECLARED))
def test_description_is_not_empty(name: str) -> None:
    assert DECLARED[name].get("description", "").strip(), f"{name}: empty description - the model cannot route to it"


def test_openai_tool_schema_shape() -> None:
    for tool in to_openai_tools(DECLARATIONS):
        assert tool["type"] == "function"
        assert tool["function"]["parameters"]["type"] == "object"


@pytest.mark.parametrize("name", sorted(DECLARED))
def test_tool_folder_has_tool_md_with_matching_name(name: str) -> None:
    matches = []
    for tool_md in (ROOT / "tools").glob("*/TOOL.md"):
        front = tool_md.read_text(encoding="utf-8").split("---")[1]
        if (yaml.safe_load(front) or {}).get("name") == name:
            matches.append(tool_md)
    assert matches, f"No tools/<folder>/TOOL.md with 'name: {name}' in its frontmatter"


@pytest.mark.parametrize("eval_file", EVAL_FILES)
def test_eval_cases_only_expect_declared_tools(eval_file: str) -> None:
    data = json.loads((ROOT / "data" / eval_file).read_text(encoding="utf-8"))
    for case in data.get("cases", []):
        for call in case.get("expect", {}).get("tool_calls", []):
            assert call["name"] in DECLARED, f"{eval_file}:{case['id']} expects undeclared tool '{call['name']}'"
