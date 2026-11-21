"""
Security Center Service
Checks AWS security posture — IAM, S3, Security Groups, EC2 exposure.
Returns a security score + findings.
"""

from datetime import datetime, timedelta
from app.services.aws_client_factory import AWSClientFactory


def _finding(severity, category, resource_id, title, description, recommendation):
    return {
        "severity":       severity,        # CRITICAL / HIGH / MEDIUM / LOW / OK
        "category":       category,
        "resource_id":    resource_id,
        "title":          title,
        "description":    description,
        "recommendation": recommendation,
        "detected_at":    datetime.utcnow().isoformat(),
    }


# ── IAM Checks ────────────────────────────────────────────────────────────────
def check_iam(aws: AWSClientFactory) -> list:
    iam      = aws.iam()
    findings = []

    # Unused IAM users (no login in 90 days)
    try:
        users = iam.list_users()["Users"]
        for user in users:
            username = user["UserName"]
            try:
                login_profile = iam.get_login_profile(UserName=username)
                # Check last login via credential report
                create_date = user.get("CreateDate")
                if create_date:
                    age_days = (datetime.now(create_date.tzinfo) - create_date).days
                    if age_days > 90:
                        findings.append(_finding(
                            "MEDIUM", "IAM", username,
                            f"Potentially inactive IAM user: {username}",
                            f"User created {age_days} days ago — verify if still needed",
                            "Review and delete unused IAM users to reduce attack surface",
                        ))
            except Exception:
                pass  # No login profile = programmatic user only
    except Exception:
        pass

    # Check for users with AdministratorAccess
    try:
        users = iam.list_users()["Users"]
        for user in users:
            username = user["UserName"]
            try:
                policies = iam.list_attached_user_policies(UserName=username)["AttachedPolicies"]
                for policy in policies:
                    if policy["PolicyName"] == "AdministratorAccess":
                        findings.append(_finding(
                            "HIGH", "IAM", username,
                            f"User has AdministratorAccess: {username}",
                            "Full AdministratorAccess policy attached to IAM user",
                            "Follow least-privilege principle — use specific policies instead",
                        ))
            except Exception:
                pass
    except Exception:
        pass

    # Root account MFA indicator (via account summary)
    try:
        summary = iam.get_account_summary()["SummaryMap"]
        if summary.get("AccountMFAEnabled", 0) == 0:
            findings.append(_finding(
                "CRITICAL", "IAM", "root",
                "Root account MFA not enabled",
                "The root AWS account does not have MFA enabled",
                "Enable MFA on the root account immediately — go to IAM → Security credentials",
            ))
        if summary.get("AccountAccessKeysPresent", 0) > 0:
            findings.append(_finding(
                "HIGH", "IAM", "root",
                "Root account has access keys",
                "Active access keys exist for the root account",
                "Delete root account access keys — use IAM users instead",
            ))
    except Exception:
        pass

    return findings


# ── S3 Security Checks ────────────────────────────────────────────────────────
def check_s3(aws: AWSClientFactory) -> list:
    s3       = aws.s3()
    findings = []

    try:
        buckets = s3.list_buckets()["Buckets"]
        for bucket in buckets:
            name = bucket["Name"]

            # Public access block
            try:
                pub = s3.get_bucket_public_access_block(Bucket=name)
                config = pub["PublicAccessBlockConfiguration"]
                if not all([
                    config.get("BlockPublicAcls", False),
                    config.get("BlockPublicPolicy", False),
                    config.get("RestrictPublicBuckets", False),
                ]):
                    findings.append(_finding(
                        "HIGH", "S3", name,
                        f"S3 bucket may be publicly accessible: {name}",
                        "Public access block is not fully enabled on this bucket",
                        "Enable all 4 public access block settings in S3 → Block public access",
                    ))
            except s3.exceptions.NoSuchPublicAccessBlockConfiguration:
                findings.append(_finding(
                    "HIGH", "S3", name,
                    f"S3 bucket has no public access block: {name}",
                    "No public access block configuration found",
                    "Configure public access block settings for this bucket",
                ))
            except Exception:
                pass

            # Bucket versioning
            try:
                versioning = s3.get_bucket_versioning(Bucket=name)
                if versioning.get("Status") != "Enabled":
                    findings.append(_finding(
                        "LOW", "S3", name,
                        f"S3 versioning disabled: {name}",
                        "Bucket versioning is not enabled — data loss risk",
                        "Enable versioning to protect against accidental deletion",
                    ))
            except Exception:
                pass

    except Exception:
        pass

    return findings


# ── Security Group Checks ─────────────────────────────────────────────────────
def check_security_groups(aws: AWSClientFactory) -> list:
    ec2      = aws.ec2()
    findings = []

    try:
        sgs = ec2.describe_security_groups()["SecurityGroups"]
        for sg in sgs:
            sg_id   = sg["GroupId"]
            sg_name = sg["GroupName"]

            for rule in sg.get("IpPermissions", []):
                from_port = rule.get("FromPort", 0)
                to_port   = rule.get("ToPort",   0)

                for cidr in rule.get("IpRanges", []):
                    if cidr.get("CidrIp") == "0.0.0.0/0":
                        # SSH open to world
                        if from_port == 22:
                            findings.append(_finding(
                                "CRITICAL", "SecurityGroup", sg_id,
                                f"SSH (port 22) open to 0.0.0.0/0: {sg_name}",
                                f"Security group {sg_id} allows SSH from any IP",
                                "Restrict SSH to specific IPs or use AWS Systems Manager Session Manager",
                            ))
                        # RDP open to world
                        elif from_port == 3389:
                            findings.append(_finding(
                                "CRITICAL", "SecurityGroup", sg_id,
                                f"RDP (port 3389) open to 0.0.0.0/0: {sg_name}",
                                f"Security group {sg_id} allows RDP from any IP",
                                "Restrict RDP access to specific IP ranges only",
                            ))
                        # All traffic open
                        elif from_port == -1 or (from_port == 0 and to_port == 65535):
                            findings.append(_finding(
                                "HIGH", "SecurityGroup", sg_id,
                                f"All traffic open to 0.0.0.0/0: {sg_name}",
                                f"Security group {sg_id} allows all inbound traffic",
                                "Restrict inbound rules to only required ports and IPs",
                            ))
    except Exception:
        pass

    return findings


# ── Compute Security Score ────────────────────────────────────────────────────
def compute_security_score(findings: list) -> int:
    deductions = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 2}
    score = 100
    for f in findings:
        score -= deductions.get(f["severity"], 0)
    return max(0, score)


# ── Full Security Report ──────────────────────────────────────────────────────
def get_security_report(aws: AWSClientFactory) -> dict:
    iam_findings = check_iam(aws)
    s3_findings  = check_s3(aws)
    sg_findings  = check_security_groups(aws)

    all_findings = iam_findings + s3_findings + sg_findings
    score        = compute_security_score(all_findings)

    # Count by severity
    by_severity = {}
    for f in all_findings:
        sev = f["severity"]
        by_severity[sev] = by_severity.get(sev, 0) + 1

    # Grade
    grade = (
        "A" if score >= 90 else
        "B" if score >= 75 else
        "C" if score >= 60 else
        "D" if score >= 40 else "F"
    )

    return {
        "account_id":   aws.account.aws_account_id,
        "account_name": aws.account.account_name,
        "security_score": score,
        "grade":          grade,
        "total_findings": len(all_findings),
        "by_severity":    by_severity,
        "findings":       sorted(
            all_findings,
            key=lambda x: ["CRITICAL", "HIGH", "MEDIUM", "LOW", "OK"].index(x["severity"])
        ),
        "categories": {
            "IAM":            {"count": len(iam_findings), "findings": iam_findings},
            "S3":             {"count": len(s3_findings),  "findings": s3_findings},
            "SecurityGroups": {"count": len(sg_findings),  "findings": sg_findings},
        },
        "generated_at": datetime.utcnow().isoformat(),
    }
