from typing import Any

from kestrel.aws.client import AwsClient, AwsUnavailable
from kestrel.aws.models import (
    AutoScalingMembershipInput,
    AutoScalingMembershipOutput,
    AwsIdentityOutput,
    Ec2InstanceInput,
    Ec2InstanceOutput,
    EmptyInput,
    IamRoleInput,
    IamRoleOutput,
    InstanceRelationshipInput,
    InstanceRelationshipOutput,
    RdsInstanceInput,
    RdsInstanceOutput,
    S3BucketInput,
    S3BucketOutput,
    SecurityGroupsInput,
    SecurityGroupsOutput,
)

from .base import Tool
from .registry import ToolRegistry


def register_aws_tools(registry: ToolRegistry, client: AwsClient | None) -> None:
    def identity(_: dict[str, Any]) -> dict[str, Any]:
        if client is None:
            return {"available": False, "reason": "AWS integration disabled"}
        try:
            value = client.identity()
        except AwsUnavailable as exc:
            return {"available": False, "reason": str(exc)}
        return {"available": True, "account": value.account, "arn": value.arn}

    registry.register(Tool("aws.identity", "Read the current AWS caller identity", identity,
                           input_schema=EmptyInput, output_schema=AwsIdentityOutput))

    def ec2_instance(arguments: dict[str, Any]) -> dict[str, Any]:
        if client is None:
            return {"instance_id": arguments["instance_id"], "state": "unavailable",
                    "security_group_ids": []}
        try:
            return client.describe_ec2_instance(arguments["instance_id"]).model_dump()
        except AwsUnavailable:
            return {"instance_id": arguments["instance_id"], "state": "unavailable",
                    "security_group_ids": []}

    registry.register(Tool("aws.describe_ec2_instance",
                           "Read EC2 instance state, network placement, public IP, and security groups",
                           ec2_instance, input_schema=Ec2InstanceInput,
                           output_schema=Ec2InstanceOutput))

    def instance_relationships(arguments: dict[str, Any]) -> dict[str, Any]:
        if client is None:
            return {"instance_id": arguments["instance_id"], "registered_target_groups": [],
                    "healthy_target_count": 0}
        try:
            return client.describe_instance_relationships(arguments["instance_id"]).model_dump()
        except AwsUnavailable:
            return {"instance_id": arguments["instance_id"], "registered_target_groups": [],
                    "healthy_target_count": 0}

    registry.register(Tool("aws.describe_instance_relationships",
                           "Find ALB/NLB target groups and healthy targets for an EC2 instance",
                           instance_relationships, input_schema=InstanceRelationshipInput,
                           output_schema=InstanceRelationshipOutput))

    def asg_membership(arguments: dict[str, Any]) -> dict[str, Any]:
        if client is None:
            return {"instance_id": arguments["instance_id"], "managed": False,
                    "auto_scaling_groups": []}
        try:
            return client.describe_auto_scaling_membership(arguments["instance_id"]).model_dump()
        except AwsUnavailable:
            return {"instance_id": arguments["instance_id"], "managed": False,
                    "auto_scaling_groups": []}

    registry.register(Tool("aws.describe_auto_scaling_membership",
                           "Determine whether an EC2 instance belongs to an Auto Scaling Group",
                           asg_membership, input_schema=AutoScalingMembershipInput,
                           output_schema=AutoScalingMembershipOutput))

    def security_groups(arguments: dict[str, Any]) -> dict[str, Any]:
        if client is None:
            return {"groups": []}
        try:
            return {"groups": [group.model_dump() for group in client.describe_security_groups(
                arguments.get("group_ids", []), arguments.get("instance_id"))]}
        except AwsUnavailable:
            return {"groups": []}

    registry.register(Tool("aws.describe_security_groups",
                           "Read EC2 security group summaries and ingress rule counts",
                           security_groups, input_schema=SecurityGroupsInput,
                           output_schema=SecurityGroupsOutput))

    def rds_instance(arguments: dict[str, Any]) -> dict[str, Any]:
        if client is None:
            return {"identifier": arguments["identifier"], "status": "unavailable",
                    "multi_az": False, "deletion_protection": False,
                    "backup_retention_period": 0, "storage_encrypted": False}
        try:
            return client.describe_rds_instance(arguments["identifier"]).model_dump()
        except AwsUnavailable:
            return {"identifier": arguments["identifier"], "status": "unavailable",
                    "multi_az": False, "deletion_protection": False,
                    "backup_retention_period": 0, "storage_encrypted": False}

    registry.register(Tool("aws.describe_rds_instance",
                           "Read RDS status, Multi-AZ, deletion protection, backups, and encryption",
                           rds_instance, input_schema=RdsInstanceInput,
                           output_schema=RdsInstanceOutput))

    def s3_bucket(arguments: dict[str, Any]) -> dict[str, Any]:
        if client is None:
            return {"bucket": arguments["bucket"], "public_access_blocked": False,
                    "versioning": "unavailable"}
        try:
            return client.describe_s3_bucket(arguments["bucket"]).model_dump()
        except AwsUnavailable:
            return {"bucket": arguments["bucket"], "public_access_blocked": False,
                    "versioning": "unavailable"}

    registry.register(Tool("aws.describe_s3_bucket",
                           "Read S3 public access block, default encryption, and versioning",
                           s3_bucket, input_schema=S3BucketInput,
                           output_schema=S3BucketOutput))

    def iam_role(arguments: dict[str, Any]) -> dict[str, Any]:
        if client is None:
            return {"role_name": arguments["role_name"], "arn": "",
                    "max_session_duration": 0, "attached_policy_names": [],
                    "inline_policy_count": 0}
        try:
            return client.describe_iam_role(arguments["role_name"]).model_dump()
        except AwsUnavailable:
            return {"role_name": arguments["role_name"], "arn": "",
                    "max_session_duration": 0, "attached_policy_names": [],
                    "inline_policy_count": 0}

    registry.register(Tool("aws.describe_iam_role",
                           "Read IAM role metadata and attached or inline policy counts",
                           iam_role, input_schema=IamRoleInput,
                           output_schema=IamRoleOutput))