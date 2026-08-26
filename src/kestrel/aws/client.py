from typing import Any

from .models import (
    AutoScalingMembershipOutput,
    AwsIdentity,
    Ec2InstanceOutput,
    IamRoleOutput,
    InstanceRelationshipOutput,
    RdsInstanceOutput,
    S3BucketOutput,
    SecurityGroupSummary,
)


class AwsUnavailable(RuntimeError):
    pass


class AwsClient:
    def __init__(self, profile: str | None = None, region: str | None = None) -> None:
        try:
            import boto3
        except ImportError as exc:
            raise AwsUnavailable("boto3 is not installed") from exc
        self._session = boto3.Session(profile_name=profile, region_name=region)

    def identity(self) -> AwsIdentity:
        try:
            result: dict[str, Any] = self._session.client("sts").get_caller_identity()
        except Exception as exc:
            raise AwsUnavailable(str(exc)) from exc
        return AwsIdentity(result["Account"], result["Arn"], result["UserId"])

    def describe_ec2_instance(self, instance_id: str) -> Ec2InstanceOutput:
        try:
            instances = self._session.client("ec2").describe_instances(
                InstanceIds=[instance_id]).get("Reservations", [])
            instance_list = [item for reservation in instances
                             for item in reservation.get("Instances", [])]
            if not instance_list:
                raise AwsUnavailable(f"EC2 instance not found: {instance_id}")
            instance = instance_list[0]
        except AwsUnavailable:
            raise
        except Exception as exc:
            raise AwsUnavailable(str(exc)) from exc
        return Ec2InstanceOutput(
            instance_id=instance.get("InstanceId", instance_id),
            state=instance.get("State", {}).get("Name", "unknown"),
            instance_type=instance.get("InstanceType"),
            availability_zone=instance.get("Placement", {}).get("AvailabilityZone"),
            subnet_id=instance.get("SubnetId"), vpc_id=instance.get("VpcId"),
            public_ip=instance.get("PublicIpAddress"),
            private_ip=instance.get("PrivateIpAddress"),
            security_group_ids=[group.get("GroupId", "") for group in instance.get(
                "SecurityGroups", []) if group.get("GroupId")],
            monitoring_state=instance.get("Monitoring", {}).get("State"))

    def describe_instance_relationships(self, instance_id: str) -> InstanceRelationshipOutput:
        try:
            elb = self._session.client("elbv2")
            groups = elb.describe_target_groups().get("TargetGroups", [])
            registered: list[str] = []
            healthy = 0
            for group in groups:
                arn = group["TargetGroupArn"]
                health = elb.describe_target_health(
                    TargetGroupArn=arn, Targets=[{"Id": instance_id}]
                ).get("TargetHealthDescriptions", [])
                if health:
                    registered.append(group.get("TargetGroupName", arn))
                    healthy += sum(item.get("TargetHealth", {}).get("State") == "healthy"
                                   for item in health)
        except Exception as exc:
            raise AwsUnavailable(str(exc)) from exc
        return InstanceRelationshipOutput(instance_id=instance_id,
                                          registered_target_groups=registered,
                                          healthy_target_count=healthy)

    def describe_auto_scaling_membership(self, instance_id: str) -> AutoScalingMembershipOutput:
        try:
            autoscaling = self._session.client("autoscaling")
            groups = autoscaling.describe_auto_scaling_groups().get("AutoScalingGroups", [])
            matches = [group for group in groups if any(
                item.get("InstanceId") == instance_id for item in group.get("Instances", []))]
        except Exception as exc:
            raise AwsUnavailable(str(exc)) from exc
        group_names = [group.get("AutoScalingGroupName", "") for group in matches]
        first = matches[0] if matches else {}
        return AutoScalingMembershipOutput(
            instance_id=instance_id, managed=bool(matches), auto_scaling_groups=group_names,
            desired_capacity=first.get("DesiredCapacity"), min_size=first.get("MinSize"),
            max_size=first.get("MaxSize"))

    def describe_security_groups(self, group_ids: list[str], instance_id: str | None = None) -> list[SecurityGroupSummary]:
        try:
            ec2 = self._session.client("ec2")
            ids = list(group_ids)
            if instance_id and not ids:
                reservations = ec2.describe_instances(InstanceIds=[instance_id]).get("Reservations", [])
                ids = [group["GroupId"] for instance in reservations[0].get("Instances", [])
                       for group in instance.get("SecurityGroups", [])] if reservations else []
            response = ec2.describe_security_groups(GroupIds=ids) if ids else ec2.describe_security_groups()
        except Exception as exc:
            raise AwsUnavailable(str(exc)) from exc
        return [SecurityGroupSummary(group_id=group.get("GroupId", ""), name=group.get("GroupName", ""),
                                     description=group.get("Description", ""), vpc_id=group.get("VpcId"),
                                     ingress_rule_count=len(group.get("IpPermissions", [])))
                for group in response.get("SecurityGroups", [])]

    def describe_rds_instance(self, identifier: str) -> RdsInstanceOutput:
        try:
            instances = self._session.client("rds").describe_db_instances(
                DBInstanceIdentifier=identifier).get("DBInstances", [])
            if not instances:
                raise AwsUnavailable(f"RDS instance not found: {identifier}")
            instance = instances[0]
        except AwsUnavailable:
            raise
        except Exception as exc:
            raise AwsUnavailable(str(exc)) from exc
        return RdsInstanceOutput(identifier=instance.get("DBInstanceIdentifier", identifier),
                                 status=instance.get("DBInstanceStatus", "unknown"),
                                 multi_az=instance.get("MultiAZ", False),
                                 deletion_protection=instance.get("DeletionProtection", False),
                                 backup_retention_period=instance.get("BackupRetentionPeriod", 0),
                                 storage_encrypted=instance.get("StorageEncrypted", False))

    def describe_s3_bucket(self, bucket: str) -> S3BucketOutput:
        try:
            s3 = self._session.client("s3")
            try:
                public = s3.get_public_access_block(Bucket=bucket).get(
                    "PublicAccessBlockConfiguration", {})
            except Exception as exc:
                if "NoSuchPublicAccessBlockConfiguration" not in str(exc):
                    raise
                public = {}
            try:
                rules = s3.get_bucket_encryption(Bucket=bucket).get(
                    "ServerSideEncryptionConfiguration", {}).get("Rules", [])
                encryption = rules[0].get("ApplyServerSideEncryptionByDefault", {}).get(
                    "SSEAlgorithm") if rules else None
            except Exception as exc:
                if "ServerSideEncryptionConfigurationNotFoundError" not in str(exc):
                    raise
                encryption = None
            versioning = s3.get_bucket_versioning(Bucket=bucket).get("Status", "Disabled")
        except Exception as exc:
            raise AwsUnavailable(str(exc)) from exc
        return S3BucketOutput(
            bucket=bucket,
            public_access_blocked=all(public.get(key, False) for key in (
                "BlockPublicAcls", "BlockPublicPolicy", "IgnorePublicAcls",
                "RestrictPublicBuckets")),
            default_encryption=encryption, versioning=versioning)

    def describe_iam_role(self, role_name: str) -> IamRoleOutput:
        try:
            iam = self._session.client("iam")
            role = iam.get_role(RoleName=role_name).get("Role", {})
            attached = iam.list_attached_role_policies(RoleName=role_name).get(
                "AttachedPolicies", [])
            inline = iam.list_role_policies(RoleName=role_name).get("PolicyNames", [])
        except Exception as exc:
            raise AwsUnavailable(str(exc)) from exc
        return IamRoleOutput(
            role_name=role.get("RoleName", role_name), arn=role.get("Arn", ""),
            max_session_duration=role.get("MaxSessionDuration", 3600),
            attached_policy_names=[item.get("PolicyName", "") for item in attached
                                   if item.get("PolicyName")],
            inline_policy_count=len(inline))