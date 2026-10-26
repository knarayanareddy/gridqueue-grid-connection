import copy
import json
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "schemas" / "core-schemas.json"


@pytest.fixture(scope="session")
def core_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def validator_for(core_schema):
    """Return a Draft 2020-12 validator for one $defs type, with format checking enabled."""

    def make(def_name: str) -> jsonschema.Draft202012Validator:
        schema = copy.deepcopy(core_schema)
        schema["$ref"] = f"#/$defs/{def_name}"
        return jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())

    return make
