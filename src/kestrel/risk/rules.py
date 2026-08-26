from typing import Any

from kestrel.terraform.evidence import change_evidence
from kestrel.terraform.models import TerraformPlan

from .models import Finding, RiskReport, Severity


def _text(value: Any) -> str:
    return repr(value).lower()


def _bool_field(value: Any, names: set[str], expected: bool) -> bool:
    if isinstance(value, dict):
        return any((key.lower() in names and child is expected) or _bool_field(child, names, expected)
                   for key, child in value.items())
    if isinstance(value, (list, tuple)):
        return any(_bool_field(child, names, expected) for child in value)
    return False


def _root_volume_change(change: Any, before: str, after: str) -> bool:
    if change.resource_type not in {"aws_ebs_volume", "aws_volume_attachment"}:
        return False
    volume_text = before + after
    return "root" in change.address.lower() or "/dev/sda1" in volume_text or \
        "/dev/xvda" in volume_text


def _public_network(after: str) -> bool:
    return "0.0.0.0/0" in after or "::/0" in after


def _public_admin_port(value: Any) -> str | None:
    if isinstance(value, dict):
        cidrs = value.get("cidr_blocks", []) + value.get("ipv6_cidr_blocks", [])
        public = any(cidr in {"0.0.0.0/0", "::/0"} for cidr in cidrs if isinstance(cidr, str))
        ports = {value.get("from_port"), value.get("to_port"), value.get("port")}
        if public and (22 in ports or "22" in ports):
            return "SSH"
        if public and (3389 in ports or "3389" in ports):
            return "RDP"
        return next((result for child in value.values() if
                     (result := _public_admin_port(child)) is not None), None)
    if isinstance(value, (list, tuple)):
        return next((result for child in value if
                     (result := _public_admin_port(child)) is not None), None)
    return None


def evaluate(plan: TerraformPlan) -> RiskReport:
    findings: list[Finding] = []
    for change in plan.resource_changes:
        after = _text(change.after)
        evidence = change_evidence(change)
        admin_port = _public_admin_port(change.after)
        if change.resource_type in {"aws_security_group_rule", "aws_security_group"} and admin_port:
            port = admin_port
            findings.append(Finding("NET-PUBLIC-ADMIN", f"Public {port} access", Severity.CRITICAL,
                f"{change.address} permits administrative access from the internet.", evidence,
                "Restrict the source CIDR to a trusted network or VPN.", confidence=99,
                resource=change.address))
        if change.resource_type in {"aws_security_group_rule", "aws_security_group"} and \
                _public_network(after) and any(port in after for port in ("3306", "5432", "1433")):
            findings.append(Finding("NET-PUBLIC-DATABASE", "Public database access", Severity.CRITICAL,
                f"{change.address} exposes a database port to the internet.", evidence,
                "Restrict database ingress to application security groups or private networks.",
                confidence=99, resource=change.address))
        if change.resource_type in {"aws_security_group_rule", "aws_security_group"} and \
                _public_network(after) and ("0" in after and "65535" in after or '"-1"' in after):
            findings.append(Finding("NET-PUBLIC-ALL", "Unrestricted inbound network access", Severity.CRITICAL,
                f"{change.address} allows unrestricted inbound traffic from the internet.", evidence,
                "Limit ports, protocols, and source networks.", confidence=99, resource=change.address))
        if change.resource_type == "aws_instance" and \
                _bool_field(change.after, {"associate_public_ip_address"}, True):
            findings.append(Finding("EC2-PUBLIC-IP", "EC2 instance has a public IPv4 address", Severity.HIGH,
                f"{change.address} requests a public IPv4 address.", evidence,
                "Keep workloads private unless public addressing is required.", resource=change.address))
        if change.resource_type == "aws_instance" and "http_tokens" in after and \
                "optional" in after:
            findings.append(Finding("EC2-IMDSV1", "EC2 allows IMDSv1", Severity.HIGH,
                f"{change.address} does not require IMDSv2 tokens.", evidence,
                "Set metadata_options.http_tokens = \"required\".", resource=change.address))
        if change.resource_type == "aws_instance" and \
                _bool_field(change.after, {"monitoring"}, False):
            findings.append(Finding("EC2-MONITORING", "EC2 detailed monitoring is disabled", Severity.MEDIUM,
                f"{change.address} does not enable detailed monitoring.", evidence,
                "Enable detailed monitoring for critical workloads.", resource=change.address))
        if "*" in after and change.resource_type.startswith("aws_iam"):
            findings.append(Finding("IAM-WILDCARD", "Wildcard IAM permission", Severity.HIGH,
                f"{change.address} contains a wildcard IAM action or resource.", evidence,
                "Use least-privilege actions and resource ARNs.", resource=change.address))
        if change.resource_type in {"aws_s3_bucket", "aws_s3_bucket_public_access_block"} and \
                (_bool_field(change.after, {"block_public_acls", "block_public_policy",
                                             "ignore_public_acls", "restrict_public_buckets"}, False)
                 or ("false" in after and "true" in _text(change.before))
                 or "public-read" in after or "public-read-write" in after
                 or ("principal" in after and '"*"' in after)):
            findings.append(Finding("S3-PUBLIC", "S3 public access weakening", Severity.CRITICAL,
                f"{change.address} weakens S3 public access controls.", evidence,
                "Keep all public access block settings enabled.", confidence=99 if
                ("public-read" in after or "public-read-write" in after or
                 ("principal" in after and '"*"' in after)) else 90,
                resource=change.address))
            if change.resource_type == "aws_s3_bucket" and \
                ("force_destroy" in after and "true" in after or
                 "versioning" in after and "enabled" not in after):
                findings.append(Finding("S3-DATA-LOSS", "S3 data-protection control weakened", Severity.HIGH,
                f"{change.address} permits destructive deletion or lacks versioning.", evidence,
                "Retain versioning and disable force_destroy for protected buckets.", resource=change.address))
            if change.resource_type == "aws_s3_bucket_lifecycle_configuration" and \
                any(value in after for value in ("days': 1", "days': 0", "days\": 1", "days\": 0")):
                findings.append(Finding("S3-LIFECYCLE-DATA-LOSS", "S3 lifecycle may delete data immediately", Severity.CRITICAL,
                f"{change.address} contains a one-day-or-less expiration rule.", evidence,
                "Review lifecycle expiration against retention requirements.", resource=change.address))
        if change.resource_type == "aws_db_instance" and isinstance(change.after, dict) and \
                change.after.get("storage_encrypted") is not True:
            findings.append(Finding("RDS-UNENCRYPTED", "RDS storage is not encrypted", Severity.HIGH,
                f"{change.address} does not enable storage encryption.", evidence,
                "Set storage_encrypted = true and verify the recovery plan.", resource=change.address))
        if change.resource_type == "aws_db_instance" and \
                _bool_field(change.after, {"publicly_accessible"}, True):
            findings.append(Finding("RDS-PUBLIC", "RDS instance is publicly accessible", Severity.CRITICAL,
                f"{change.address} is configured for public network access.", evidence,
                "Keep publicly_accessible = false and use private subnets.", resource=change.address))
        if change.resource_type == "aws_db_instance" and \
                _bool_field(change.after, {"multi_az"}, False):
            findings.append(Finding("RDS-NOT-MULTI-AZ", "RDS Multi-AZ is disabled", Severity.HIGH,
                f"{change.address} is not configured for Multi-AZ resilience.", evidence,
                "Enable Multi-AZ for production databases.", resource=change.address))
        if change.resource_type == "aws_db_instance" and isinstance(change.after, dict) and \
                change.after.get("backup_retention_period") == 0:
            findings.append(Finding("RDS-NO-BACKUPS", "RDS automated backups are disabled", Severity.MEDIUM,
                f"{change.address} has zero days of backup retention.", evidence,
                "Configure automated backup retention for recovery.", resource=change.address))
        if change.resource_type == "aws_db_instance" and change.destructive and \
                isinstance(change.after, dict) and not change.after.get("final_snapshot_identifier"):
            findings.append(Finding("RDS-NO-FINAL-SNAPSHOT", "RDS deletion has no final snapshot", Severity.HIGH,
                f"{change.address} is deleted without a final snapshot identifier.", evidence,
                "Require a final snapshot before deleting production data.", resource=change.address))
        if change.resource_type.startswith("aws_") and "encrypt" in _text(change.before) and \
                ("encrypt" not in after or _bool_field(change.after, {"storage_encrypted", "encrypted"}, False)):
            findings.append(Finding("ENCRYPTION-REMOVED", "Encryption configuration removed", Severity.HIGH,
                f"{change.address} removes an encryption setting.", evidence,
                "Retain provider-managed or customer-managed encryption.", resource=change.address))
        if change.destructive:
            root_volume = _root_volume_change(change, _text(change.before), after)
            severity = Severity.CRITICAL if root_volume or change.resource_type in {
                "aws_db_instance", "aws_kms_key"} else Severity.HIGH
            rule_id = "ROOT-VOLUME-DELETED" if root_volume else "DESTRUCTIVE-CHANGE"
            title = "Root volume deletion" if root_volume else "Destructive infrastructure change"
            description = (f"{change.address} deletes a root volume." if root_volume else
                           f"{change.address} includes a delete action.")
            findings.append(Finding(rule_id, title, severity, description, evidence,
                "Confirm the replacement and backup or recovery path.", resource=change.address))
        if change.resource_type in {"aws_kms_key", "aws_s3_bucket"} and "encrypt" in after:
            findings.append(Finding("ENCRYPTION-ENABLED", "Encryption is configured", Severity.INFO,
                f"{change.address} contains encryption configuration.", evidence,
                positive=True, resource=change.address))
    if not findings:
        findings.append(Finding("PLAN-CLEAN", "No risky patterns detected", Severity.INFO,
            "The deterministic rule set found no known high-impact patterns.", positive=True))
    return RiskReport.from_findings(findings)
