from dataclasses import dataclass

from pydantic import BaseModel, Field


@dataclass(frozen=True)
class AwsIdentity:
    account: str
    arn: str
    user_id: str


class EmptyInput(BaseModel):
    pass


class AwsIdentityOutput(BaseModel):
    available: bool
    account: str | None = None
    arn: str | None = None
    reason: str | None = None


class Ec2InstanceInput(BaseModel):
    instance_id: str = Field(min_length=1, max_length=64)


class Ec2InstanceOutput(BaseModel):
    instance_id: str
    state: str
    instance_type: str | None = None
    availability_zone: str | None = None
    subnet_id: str | None = None
    vpc_id: str | None = None
    public_ip: str | None = None
    private_ip: str | None = None
    security_group_ids: list[str]
    monitoring_state: str | None = None


class InstanceRelationshipInput(BaseModel):
    instance_id: str = Field(min_length=1)


class InstanceRelationshipOutput(BaseModel):
    instance_id: str
    registered_target_groups: list[str]
    healthy_target_count: int


class AutoScalingMembershipInput(BaseModel):
    instance_id: str = Field(min_length=1)


class AutoScalingMembershipOutput(BaseModel):
    instance_id: str
    managed: bool
    auto_scaling_groups: list[str]
    desired_capacity: int | None = None
    min_size: int | None = None
    max_size: int | None = None


class SecurityGroupsInput(BaseModel):
    group_ids: list[str] = Field(default_factory=list)
    instance_id: str | None = None


class SecurityGroupSummary(BaseModel):
    group_id: str
    name: str
    description: str
    vpc_id: str | None = None
    ingress_rule_count: int


class SecurityGroupsOutput(BaseModel):
    groups: list[SecurityGroupSummary]


class RdsInstanceInput(BaseModel):
    identifier: str = Field(min_length=1)


class RdsInstanceOutput(BaseModel):
    identifier: str
    status: str
    multi_az: bool
    deletion_protection: bool
    backup_retention_period: int
    storage_encrypted: bool


class S3BucketInput(BaseModel):
    bucket: str = Field(min_length=3, max_length=63)


class S3BucketOutput(BaseModel):
    bucket: str
    public_access_blocked: bool
    default_encryption: str | None = None
    versioning: str


class IamRoleInput(BaseModel):
    role_name: str = Field(min_length=1, max_length=64)


class IamRoleOutput(BaseModel):
    role_name: str
    arn: str
    max_session_duration: int
    attached_policy_names: list[str]
    inline_policy_count: int