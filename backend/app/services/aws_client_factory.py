"""
Account-Aware AWS Client Factory
All AWS API calls go through this — uses STS AssumeRole per account.

Usage:
    aws = AWSClientFactory(account)
    ec2 = aws.ec2()
    s3  = aws.s3()
    ce  = aws.cost_explorer()
"""

import boto3
from functools import lru_cache
from app.services.aws_assume_role import assume_role
from app.database.models import AWSAccount


class AWSClientFactory:
    """
    Creates boto3 clients using temporary credentials from STS AssumeRole.
    Each factory instance is tied to one AWS account connection.
    """

    def __init__(self, account: AWSAccount):
        self.account = account
        self._session = None

    def _get_session(self) -> boto3.Session:
        """Get or create boto3 session with assumed-role credentials."""
        if self._session is None:
            creds = assume_role(
                role_arn=self.account.role_arn,
                external_id=self.account.external_id,
                session_name=f"FinOps-{self.account.aws_account_id[:8]}",
            )
            self._session = boto3.Session(
                aws_access_key_id=creds["access_key_id"],
                aws_secret_access_key=creds["secret_access_key"],
                aws_session_token=creds["session_token"],
                region_name=self.account.default_region,
            )
        return self._session

    def client(self, service: str, region: str = None):
        """Get a boto3 client for any AWS service."""
        session = self._get_session()
        return session.client(service, region_name=region or self.account.default_region)

    # ── Convenience methods ───────────────────────────────────────────────────
    def ec2(self, region: str = None):
        return self.client("ec2", region)

    def s3(self):
        return self.client("s3", "us-east-1")  # S3 is global

    def rds(self, region: str = None):
        return self.client("rds", region)

    def lambda_client(self, region: str = None):
        return self.client("lambda", region)

    def eks(self, region: str = None):
        return self.client("eks", region)

    def cloudwatch(self, region: str = None):
        return self.client("cloudwatch", region)

    def cost_explorer(self):
        return self.client("ce", "us-east-1")  # CE is always us-east-1

    def iam(self):
        return self.client("iam", "us-east-1")  # IAM is global

    def sts(self):
        return self.client("sts", self.account.default_region)

    def elb(self, region: str = None):
        return self.client("elbv2", region)

    def sns(self, region: str = None):
        return self.client("sns", region)


def get_aws_factory(account: AWSAccount) -> AWSClientFactory:
    """Helper to create AWSClientFactory from an account model."""
    return AWSClientFactory(account)
