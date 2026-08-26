from dataclasses import asdict

import typer

from . import __version__
from .agent.agent import analyze_with_agent
from .aws.client import AwsClient, AwsUnavailable
from .config import Settings
from .llm.base import AgentContext
from .llm.providers import provider_for
from .reporting.console import render_console
from .reporting.json import render_json
from .risk.models import RiskReport
from .risk.rules import evaluate
from .terraform.parser import load_plan
from .tools.aws_tools import register_aws_tools
from .tools.registry import ToolRegistry
from .tools.terraform_tools import register_terraform_tools

app = typer.Typer(no_args_is_help=True)


@app.command()
def version() -> None:
    typer.echo(__version__)


@app.command()
def doctor() -> None:
    typer.echo(f"kestrel {__version__}: deterministic engine ready")
    try:
        import boto3  # noqa: F401
        typer.echo("AWS adapter: available")
    except ImportError:
        typer.echo("AWS adapter: unavailable (optional boto3 not installed)")


@app.command()
def analyze(path: str, json_output: bool = typer.Option(False, "--json"), no_aws: bool = False,
            mock: bool = False, aws_profile: str | None = None, region: str | None = None,
            verbose: bool = False, provider: str | None = typer.Option(None, "--provider")) -> None:
    base_settings = Settings.from_environment()
    settings = Settings(aws_profile or base_settings.aws_profile,
                        region or base_settings.region,
                        base_settings.max_tool_rounds,
                        "mock" if mock else (provider or base_settings.llm_provider))
    plan = load_plan(path)
    report = evaluate(plan)
    registry = ToolRegistry()
    register_terraform_tools(registry, plan)
    client = None
    if not no_aws:
        try:
            client = AwsClient(settings.aws_profile, settings.region)
        except AwsUnavailable:
            pass
    register_aws_tools(registry, client)
    context = AgentContext(
        observations=[],
        available_tools=[{"name": name, "description": registry.get(name).description}
                         for name in registry.names()],
        deterministic_findings=[asdict(f) | {"severity": f.severity.name} for f in report.findings],
        plan_summary={"resource_count": len(plan.resource_changes),
                      "addresses": [change.address for change in plan.resource_changes]},
    )
    state = analyze_with_agent(provider_for(settings.llm_provider), registry,
                               settings.max_tool_rounds, context)
    report = RiskReport(report.findings, report.verdict, tuple(state.observations))
    if verbose and not json_output:
        typer.echo(f"Resources: {len(plan.resource_changes)} | Tools: {', '.join(registry.names())}")
    typer.echo(render_json(report) if json_output else render_console(report))