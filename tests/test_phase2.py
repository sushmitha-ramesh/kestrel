import json
from typing import Any

import httpx
import pytest
from pydantic import ValidationError

from kestrel.agent.planner import run_loop
from kestrel.aws.client import AwsClient
from kestrel.llm.base import AgentContext, Decision
from kestrel.llm.ollama import OllamaProvider
from kestrel.llm.openai import OpenAIProvider
from kestrel.llm.providers import provider_for
from kestrel.risk.rules import evaluate
from kestrel.terraform.parser import parse_plan
from kestrel.tools.aws_tools import register_aws_tools
from kestrel.tools.base import Tool
from kestrel.tools.registry import ToolRegistry


def change(address: str, resource_type: str, actions: list[str], before: Any = None,
           after: Any = None) -> dict[str, Any]:
    return {"address": address, "type": resource_type,
            "change": {"actions": actions, "before": before, "after": after}}


def test_parser_extracts_create_update_delete_and_replacement() -> None:
    plan = parse_plan({"resource_changes": [
        change("aws_instance.create", "aws_instance", ["create"], after={"name": "a"}),
        change("aws_instance.update", "aws_instance", ["update"], {"size": 1}, {"size": 2}),
        change("aws_instance.delete", "aws_instance", ["delete"], {"name": "a"}),
        change("aws_instance.replace", "aws_instance", ["delete", "create"], {"subnet": "a"}, {"subnet": "b"}),
    ]})
    assert [item.actions for item in plan.resource_changes] == [("create",), ("update",), ("delete",), ("delete", "create")]
    assert plan.resource_changes[1].changed_attributes == ("size",)
    assert plan.resource_changes[3].replacement


def test_parser_redacts_common_secret_fields() -> None:
    plan = parse_plan({"resource_changes": [change("x", "aws_db_instance", ["create"],
        after={"password": "p", "api_key": "k", "private_key": "key", "safe": "v"})]})
    after = plan.resource_changes[0].after
    assert after["password"] == after["api_key"] == after["private_key"] == "[REDACTED]"
    assert after["safe"] == "v"


@pytest.mark.parametrize(("port", "title"), [(22, "Public SSH access"), (3389, "Public RDP access")])
def test_public_management_ports_are_critical(port: int, title: str) -> None:
    report = evaluate(parse_plan({"resource_changes": [change(
        "aws_security_group_rule.admin", "aws_security_group_rule", ["create"],
        after={"from_port": port, "to_port": port, "cidr_blocks": ["0.0.0.0/0"]})]}))
    assert report.findings[0].title == title
    assert report.findings[0].confidence == 99
    assert report.verdict == "BLOCK"


def test_risk_rules_cover_iam_s3_encryption_and_destroy() -> None:
    plan = parse_plan({"resource_changes": [
        change("aws_iam_policy.admin", "aws_iam_policy", ["create"], after={"Action": "*", "Resource": "*"}),
        change("aws_s3_bucket_public_access_block.data", "aws_s3_bucket_public_access_block", ["update"],
               {"block_public_acls": True}, {"block_public_acls": False}),
        change("aws_db_instance.db", "aws_db_instance", ["update"], {"storage_encrypted": True}, {"storage_encrypted": False}),
        change("aws_db_instance.old", "aws_db_instance", ["delete"]),
    ]})
    rule_ids = {finding.rule_id for finding in evaluate(plan).findings}
    assert {"IAM-WILDCARD", "S3-PUBLIC", "ENCRYPTION-REMOVED", "DESTRUCTIVE-CHANGE"} <= rule_ids


class FinalProvider:
    def decide(self, context: AgentContext) -> Decision:
        return Decision("final", rationale="No further evidence")


def test_agent_rejects_invalid_tool_and_bounds_steps() -> None:
    class InvalidProvider:
        def decide(self, context: AgentContext) -> Decision:
            return Decision("tool", "not-registered", {}, "Need evidence")

    state = run_loop(InvalidProvider(), ToolRegistry(), max_rounds=8)
    assert state.rounds == 1
    assert "unregistered tool" in state.observations[0]["error"]

    registry = ToolRegistry()
    registry.register(Tool("read", "read-only", lambda _: {"ok": True}))

    class RepeatingProvider:
        def decide(self, context: AgentContext) -> Decision:
            return Decision("tool", "read", {}, "Check evidence")

    state = run_loop(RepeatingProvider(), registry, max_rounds=2)
    assert state.rounds == 2
    assert len(state.observations) == 2
    assert state.observations[1]["error"].startswith("duplicate")


def test_registry_rejects_mutating_tool() -> None:
    with pytest.raises(ValueError):
        ToolRegistry().register(Tool("write", "mutation", lambda _: {}, read_only=False))


def test_critical_finding_cannot_be_downgraded_by_final_agent() -> None:
    plan = parse_plan({"resource_changes": [change(
        "aws_security_group_rule.ssh", "aws_security_group_rule", ["create"],
        after={"from_port": 22, "cidr_blocks": ["0.0.0.0/0"]})]})
    report = evaluate(plan)
    state = run_loop(FinalProvider(), ToolRegistry(), max_rounds=8)
    assert state.final
    assert report.verdict == "BLOCK"


def test_ollama_provider_parses_structured_decision(monkeypatch: pytest.MonkeyPatch) -> None:
    response = httpx.Response(200, request=httpx.Request("POST", "http://test"),
                              json={"message": {"content": json.dumps({
        "kind": "tool", "tool_name": "aws.describe_rds_instance",
        "arguments": {"identifier": "db"}, "rationale": "Check backup evidence"})}})
    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: response)
    decision = OllamaProvider().decide(AgentContext([], [{"name": "aws.describe_rds_instance", "description": "read RDS"}], [], {}))
    assert decision.kind == "tool"
    assert decision.tool_name == "aws.describe_rds_instance"
    assert decision.arguments == {"identifier": "db"}


def test_openai_provider_parses_structured_decision(monkeypatch: pytest.MonkeyPatch) -> None:
    response = httpx.Response(200, request=httpx.Request("POST", "http://test"),
                              json={"choices": [{"message": {"content": json.dumps({
        "kind": "tool", "tool_name": "terraform.summary", "arguments": {},
        "rationale": "Inspect plan scope"})}}]})
    calls: list[tuple[str, dict[str, Any]]] = []

    def post(url: str, **kwargs: Any) -> httpx.Response:
        calls.append((url, kwargs))
        return response

    monkeypatch.setattr(httpx, "post", post)
    decision = OpenAIProvider(base_url="http://test/v1", model="test-model",
                              api_key="test-key").decide(
        AgentContext([], [{"name": "terraform.summary", "description": "read plan"}], [], {}))
    assert decision.kind == "tool"
    assert decision.tool_name == "terraform.summary"
    assert calls[0][0] == "http://test/v1/chat/completions"
    assert calls[0][1]["headers"]["Authorization"] == "Bearer test-key"
    assert calls[0][1]["json"]["model"] == "test-model"
    assert calls[0][1]["json"]["response_format"] == {"type": "json_object"}


def test_provider_for_selects_openai_provider() -> None:
    assert isinstance(provider_for("openai"), OpenAIProvider)


class StubSession:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def client(self, name: str) -> "StubService":
        return StubService(name, self.calls)


class StubService:
    def __init__(self, name: str, calls: list[tuple[str, dict[str, Any]]]) -> None:
        self.name = name
        self.calls = calls

    def describe_db_instances(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("rds.describe_db_instances", kwargs))
        return {"DBInstances": [{"DBInstanceIdentifier": "db", "DBInstanceStatus": "available",
                                  "MultiAZ": True, "DeletionProtection": True,
                                  "BackupRetentionPeriod": 7, "StorageEncrypted": True}]}

    def describe_target_groups(self) -> dict[str, Any]:
        self.calls.append(("elbv2.describe_target_groups", {}))
        return {"TargetGroups": [{"TargetGroupArn": "arn:target", "TargetGroupName": "web"}]}

    def describe_target_health(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("elbv2.describe_target_health", kwargs))
        return {"TargetHealthDescriptions": [{"TargetHealth": {"State": "healthy"}}]}

    def describe_auto_scaling_groups(self) -> dict[str, Any]:
        self.calls.append(("autoscaling.describe_auto_scaling_groups", {}))
        return {"AutoScalingGroups": [{"AutoScalingGroupName": "web-asg", "DesiredCapacity": 2,
                                        "MinSize": 1, "MaxSize": 3,
                                        "Instances": [{"InstanceId": "i-1"}]}]}

    def describe_instances(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("ec2.describe_instances", kwargs))
        return {"Reservations": [{"Instances": [{"SecurityGroups": [{"GroupId": "sg-1"}]}]}]}

    def describe_security_groups(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("ec2.describe_security_groups", kwargs))
        return {"SecurityGroups": [{"GroupId": "sg-1", "GroupName": "web", "Description": "web",
                                     "VpcId": "vpc-1", "IpPermissions": [{}]}]}

    def get_public_access_block(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("s3.get_public_access_block", kwargs))
        return {"PublicAccessBlockConfiguration": {
            "BlockPublicAcls": True, "BlockPublicPolicy": True,
            "IgnorePublicAcls": True, "RestrictPublicBuckets": True}}

    def get_bucket_encryption(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("s3.get_bucket_encryption", kwargs))
        return {"ServerSideEncryptionConfiguration": {"Rules": [{
            "ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "aws:kms"}}]}}

    def get_bucket_versioning(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("s3.get_bucket_versioning", kwargs))
        return {"Status": "Enabled"}

    def get_role(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("iam.get_role", kwargs))
        return {"Role": {"RoleName": "app", "Arn": "arn:aws:iam::1:role/app",
                           "MaxSessionDuration": 3600}}

    def list_attached_role_policies(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("iam.list_attached_role_policies", kwargs))
        return {"AttachedPolicies": [{"PolicyName": "ReadOnlyAccess"}]}

    def list_role_policies(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("iam.list_role_policies", kwargs))
        return {"PolicyNames": ["inline-policy"]}


def test_rds_client_uses_read_only_boto_call(monkeypatch: pytest.MonkeyPatch) -> None:
    client = object.__new__(AwsClient)
    session = StubSession()
    client._session = session
    result = client.describe_rds_instance("db")
    assert result.multi_az and result.storage_encrypted
    assert session.calls == [("rds.describe_db_instances", {"DBInstanceIdentifier": "db"})]


def test_aws_domain_clients_return_safe_summaries() -> None:
    client = object.__new__(AwsClient)
    session = StubSession()
    client._session = session
    ec2 = client.describe_ec2_instance("i-1")
    s3 = client.describe_s3_bucket("bucket")
    iam = client.describe_iam_role("app")
    assert ec2.state == "unknown"
    assert s3.public_access_blocked and s3.default_encryption == "aws:kms"
    assert iam.attached_policy_names == ["ReadOnlyAccess"]
    assert all("describe" in name or name.startswith(("s3.", "iam."))
               for name, _ in session.calls)


def test_other_aws_clients_use_read_only_describe_calls() -> None:
    client = object.__new__(AwsClient)
    session = StubSession()
    client._session = session
    relationships = client.describe_instance_relationships("i-1")
    membership = client.describe_auto_scaling_membership("i-1")
    groups = client.describe_security_groups([], "i-1")
    assert relationships.healthy_target_count == 1
    assert membership.managed and membership.desired_capacity == 2
    assert groups[0].group_id == "sg-1"
    assert all("describe" in name for name, _ in session.calls)


def test_aws_tools_are_offline_safe_and_typed() -> None:
    registry = ToolRegistry()
    register_aws_tools(registry, None)
    assert {"aws.describe_ec2_instance", "aws.describe_s3_bucket", "aws.describe_iam_role",
            "aws.describe_rds_instance"} <= set(registry.names())
    result = registry.invoke("aws.describe_rds_instance", {"identifier": "db"})
    assert result["status"] == "unavailable"
    assert registry.invoke("aws.describe_ec2_instance", {"instance_id": "i-1"})["state"] == "unavailable"
    assert registry.invoke("aws.describe_s3_bucket", {"bucket": "data"})["versioning"] == "unavailable"
    assert registry.invoke("aws.describe_iam_role", {"role_name": "app"})["arn"] == ""
    with pytest.raises(ValidationError):
        registry.invoke("aws.describe_rds_instance", {})