"""
AWS STS AssumeRole Service
Core of multi-account support — assumes cross-account IAM roles
using ExternalId to prevent confused-deputy attacks.
"""

import boto3
from botocore.exceptions import ClientError
import os

PLATFORM_ROLE_ARN = os.getenv("PLATFORM_ROLE_ARN", "")  # Platform's own role (optional)
AWS_REGION        = os.getenv("AWS_REGION", "us-east-1")


def assume_role(role_arn: str, external_id: str, session_name: str = "FinOpsPlatform") -> dict:
    """
    Assume a cross-account IAM role using STS.
    Returns temporary credentials valid for 1 hour.

    Security: ExternalId prevents confused-deputy attacks.
    """
    sts = boto3.client("sts", region_name=AWS_REGION)
    try:
        response = sts.assume_role(
            RoleArn=role_arn,
            RoleSessionName=session_name[:64],  # Max 64 chars
            ExternalId=external_id,
            DurationSeconds=3600,  # 1 hour
        )
        creds = response["Credentials"]
        return {
            "access_key_id":     creds["AccessKeyId"],
            "secret_access_key": creds["SecretAccessKey"],
            "session_token":     creds["SessionToken"],
            "expiration":        creds["Expiration"].isoformat(),
        }
    except ClientError as e:
        code = e.response["Error"]["Code"]
        msg  = e.response["Error"]["Message"]
        if code == "AccessDenied":
            raise ValueError(
                "Access denied. Ensure the IAM role has a trust policy allowing "
                "this platform to assume it, and the ExternalId matches."
            )
        if code == "NoSuchEntity":
            raise ValueError(f"Role not found: {role_arn}")
        if code == "InvalidClientTokenId":
            raise ValueError("Invalid AWS credentials on the platform side.")
        raise ValueError(f"STS AssumeRole failed: {msg}")


def get_aws_session(role_arn: str, external_id: str, region: str = "us-east-1"):
    """
    Returns a boto3 Session using assumed-role credentials.
    Use this for all AWS API calls for a connected account.

    Usage:
        session = get_aws_session(account.role_arn, account.external_id)
        ec2 = session.client("ec2")
        s3  = session.client("s3")
    """
    creds = assume_role(role_arn, external_id)
    session = boto3.Session(
        aws_access_key_id=creds["access_key_id"],
        aws_secret_access_key=creds["secret_access_key"],
        aws_session_token=creds["session_token"],
        region_name=region,
    )
    return session


def validate_account_connection(role_arn: str, external_id: str, region: str = "us-east-1") -> dict:
    """
    Validate that we can successfully assume the role and get account info.
    Called when user connects a new AWS account.
    """
    try:
        session = get_aws_session(role_arn, external_id, region)
        sts = session.client("sts")
        identity = sts.get_caller_identity()
        return {
            "valid":       True,
            "account_id":  identity["Account"],
            "user_id":     identity["UserId"],
            "arn":         identity["Arn"],
        }
    except ValueError as e:
        return {"valid": False, "error": str(e)}
    except Exception as e:
        return {"valid": False, "error": f"Connection validation failed: {str(e)}"}
