from kestrel.risk.rules import evaluate
from kestrel.terraform.parser import parse_plan


def test_public_ssh_is_critical_and_secrets_are_redacted() -> None:
    plan = parse_plan({"resource_changes": [{"address": "aws_security_group_rule.ssh", "type": "aws_security_group_rule", "change": {"actions": ["create"], "after": {"from_port": 22, "cidr_blocks": ["0.0.0.0/0"], "password": "secret"}}}]})
    report = evaluate(plan)
    assert report.verdict == "BLOCK"
    assert report.findings[0].evidence["after"]["password"] == "[REDACTED]"


def test_root_volume_deletion_is_critical() -> None:
    plan = parse_plan({"resource_changes": [{
        "address": "aws_volume_attachment.root", "type": "aws_volume_attachment",
        "change": {"actions": ["delete"], "before": {"device_name": "/dev/sda1"}}
    }]})
    report = evaluate(plan)
    assert report.findings[0].rule_id == "ROOT-VOLUME-DELETED"
    assert report.findings[0].severity.name == "CRITICAL"


def test_s3_public_acl_and_rds_exposure_are_detected() -> None:
    plan = parse_plan({"resource_changes": [
        {"address": "aws_s3_bucket.data", "type": "aws_s3_bucket",
         "change": {"actions": ["create"], "after": {"acl": "public-read"}}},
        {"address": "aws_db_instance.db", "type": "aws_db_instance",
         "change": {"actions": ["create"], "after": {
             "storage_encrypted": False, "publicly_accessible": True}}}
    ]})
    report = evaluate(plan)
    rule_ids = {finding.rule_id for finding in report.findings}
    assert {"S3-PUBLIC", "RDS-UNENCRYPTED", "RDS-PUBLIC"} <= rule_ids
    assert next(finding for finding in report.findings if finding.rule_id == "S3-PUBLIC").severity.name == "CRITICAL"
    assert report.verdict == "BLOCK"


def test_ec2_public_ip_and_s3_block_public_access_are_detected() -> None:
    plan = parse_plan({"resource_changes": [
        {"address": "aws_instance.web", "type": "aws_instance",
         "change": {"actions": ["create"], "after": {
             "associate_public_ip_address": True}}},
        {"address": "aws_s3_bucket_public_access_block.data",
         "type": "aws_s3_bucket_public_access_block",
         "change": {"actions": ["update"], "before": {
             "block_public_acls": True, "block_public_policy": True}, "after": {
             "block_public_acls": False, "block_public_policy": False}}}
    ]})
    report = evaluate(plan)
    findings = {finding.rule_id: finding for finding in report.findings}
    assert findings["EC2-PUBLIC-IP"].severity.name == "HIGH"
    assert findings["S3-PUBLIC"].severity.name == "CRITICAL"
    assert report.verdict == "BLOCK"


def test_allowlisted_ssh_is_not_reported_as_world_open() -> None:
    plan = parse_plan({"resource_changes": [{
        "address": "aws_security_group.this", "type": "aws_security_group",
        "change": {"actions": ["create"], "after": {"ingress": [{
            "from_port": 22, "to_port": 22, "cidr_blocks": ["203.0.113.25/32"]
        }]}}
    }]})
    report = evaluate(plan)
    assert "NET-PUBLIC-ADMIN" not in {finding.rule_id for finding in report.findings}