import json
from pathlib import Path

from typer.testing import CliRunner

from kestrel.cli import app


def test_mock_json_cli_is_offline() -> None:
    result = CliRunner().invoke(app, ["analyze", str(Path("examples/risky/plan.json")), "--json", "--mock", "--no-aws"])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["verdict"] == "BLOCK"