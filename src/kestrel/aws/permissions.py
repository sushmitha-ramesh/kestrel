READ_ONLY_ACTIONS = (
    "sts:GetCallerIdentity",
    "iam:SimulatePrincipalPolicy",
)


def custom_policy() -> dict[str, object]:
    return {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": list(READ_ONLY_ACTIONS), "Resource": "*"}]}