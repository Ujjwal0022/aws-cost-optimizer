"""
Tests for Security Center and Audit Log service.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestSecurityService:

    def test_iam_root_mfa_not_enabled(self):
        """Root MFA disabled should trigger CRITICAL finding."""
        aws = MagicMock()
        mock_iam = MagicMock()
        mock_iam.list_users.return_value = {"Users": []}
        mock_iam.get_account_summary.return_value = {
            "SummaryMap": {
                "AccountMFAEnabled":         0,    # ← MFA disabled
                "AccountAccessKeysPresent":  0,
            }
        }
        aws.iam.return_value = mock_iam

        from app.services.security_service import check_iam
        findings = check_iam(aws)

        critical = [f for f in findings if f["severity"] == "CRITICAL"]
        assert len(critical) >= 1
        assert any("MFA" in f["title"] for f in critical)

    def test_iam_root_access_keys(self):
        """Root access keys present should trigger HIGH finding."""
        aws = MagicMock()
        mock_iam = MagicMock()
        mock_iam.list_users.return_value = {"Users": []}
        mock_iam.get_account_summary.return_value = {
            "SummaryMap": {
                "AccountMFAEnabled":        1,
                "AccountAccessKeysPresent": 1,   # ← Root has access keys
            }
        }
        aws.iam.return_value = mock_iam

        from app.services.security_service import check_iam
        findings = check_iam(aws)

        high = [f for f in findings if f["severity"] == "HIGH"]
        assert any("access keys" in f["title"].lower() for f in high)

    def test_iam_admin_access_user(self):
        """User with AdministratorAccess should trigger HIGH finding."""
        aws = MagicMock()
        mock_iam = MagicMock()
        mock_iam.list_users.return_value = {
            "Users": [{"UserName": "admin-user", "CreateDate": __import__("datetime").datetime.utcnow()}]
        }
        mock_iam.get_login_profile.return_value = {"LoginProfile": {"UserName": "admin-user"}}
        mock_iam.list_attached_user_policies.return_value = {
            "AttachedPolicies": [{"PolicyName": "AdministratorAccess", "PolicyArn": "arn:aws:iam::aws:policy/AdministratorAccess"}]
        }
        mock_iam.get_account_summary.return_value = {
            "SummaryMap": {"AccountMFAEnabled": 1, "AccountAccessKeysPresent": 0}
        }
        aws.iam.return_value = mock_iam

        from app.services.security_service import check_iam
        findings = check_iam(aws)

        admin_findings = [f for f in findings if "AdministratorAccess" in f["title"]]
        assert len(admin_findings) >= 1
        assert admin_findings[0]["severity"] == "HIGH"

    def test_sg_ssh_open_to_world(self):
        """SSH open to 0.0.0.0/0 should trigger CRITICAL finding."""
        aws = MagicMock()
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.return_value = {
            "SecurityGroups": [{
                "GroupId":   "sg-0abc123",
                "GroupName": "open-ssh-sg",
                "IpPermissions": [{
                    "FromPort": 22,
                    "ToPort":   22,
                    "IpProtocol": "tcp",
                    "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
                }],
            }]
        }
        aws.ec2.return_value = mock_ec2

        from app.services.security_service import check_security_groups
        findings = check_security_groups(aws)

        critical = [f for f in findings if f["severity"] == "CRITICAL"]
        assert len(critical) >= 1
        assert any("SSH" in f["title"] for f in critical)
        assert any("sg-0abc123" in f["resource_id"] for f in critical)

    def test_sg_rdp_open_to_world(self):
        """RDP open to 0.0.0.0/0 should trigger CRITICAL finding."""
        aws = MagicMock()
        mock_ec2 = MagicMock()
        mock_ec2.describe_security_groups.return_value = {
            "SecurityGroups": [{
                "GroupId":   "sg-rdp123",
                "GroupName": "open-rdp-sg",
                "IpPermissions": [{
                    "FromPort":   3389,
                    "ToPort":     3389,
                    "IpProtocol": "tcp",
                    "IpRanges":   [{"CidrIp": "0.0.0.0/0"}],
                }],
            }]
        }
        aws.ec2.return_value = mock_ec2

        from app.services.security_service import check_security_groups
        findings = check_security_groups(aws)

        critical = [f for f in findings if "RDP" in f["title"]]
        assert len(critical) >= 1

    def test_s3_public_bucket(self):
        """Public S3 bucket should trigger HIGH finding."""
        aws = MagicMock()
        mock_s3 = MagicMock()
        mock_s3.list_buckets.return_value = {
            "Buckets": [{"Name": "public-bucket", "CreationDate": __import__("datetime").datetime.utcnow()}]
        }
        mock_s3.get_bucket_public_access_block.return_value = {
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls":       False,
                "BlockPublicPolicy":     False,
                "RestrictPublicBuckets": False,
            }
        }
        mock_s3.get_bucket_location.return_value = {"LocationConstraint": "us-east-1"}
        mock_s3.get_bucket_versioning.return_value = {"Status": "Enabled"}
        aws.s3.return_value = mock_s3

        from app.services.security_service import check_s3
        findings = check_s3(aws)

        high = [f for f in findings if f["severity"] == "HIGH"]
        assert len(high) >= 1
        assert any("public-bucket" in f["resource_id"] for f in high)

    def test_security_score_calculation(self):
        """Score should decrease for each finding."""
        from app.services.security_service import compute_security_score

        # Perfect score
        assert compute_security_score([]) == 100

        # Critical finding = -20
        critical = [{"severity": "CRITICAL", "category": "IAM", "resource_id": "r",
                     "title": "t", "description": "d", "recommendation": "r2",
                     "detected_at": "2024-01-01"}]
        assert compute_security_score(critical) == 80

        # Multiple findings
        findings = [
            {**critical[0], "severity": "CRITICAL"},
            {**critical[0], "severity": "HIGH"},
            {**critical[0], "severity": "MEDIUM"},
        ]
        score = compute_security_score(findings)
        assert score == 100 - 20 - 10 - 5   # = 65

        # Score never goes below 0
        many_critical = [critical[0]] * 10
        assert compute_security_score(many_critical) == 0

    def test_clean_account_grade_a(self):
        """Account with no findings should get grade A."""
        with patch("app.services.security_service.check_iam")              as m_iam, \
             patch("app.services.security_service.check_s3")               as m_s3,  \
             patch("app.services.security_service.check_security_groups")  as m_sg:
            m_iam.return_value = []
            m_s3.return_value  = []
            m_sg.return_value  = []

            aws = MagicMock()
            aws.account.aws_account_id = "123456789012"
            aws.account.account_name    = "Clean"

            from app.services.security_service import get_security_report
            report = get_security_report(aws)

            assert report["security_score"] == 100
            assert report["grade"]          == "A"
            assert report["total_findings"] == 0


class TestAuditService:

    def test_get_audit_logs_own_user(self, test_user, test_account, db):
        """User should only see their own audit logs."""
        from app.database.models import AuditLog
        from app.services.audit_service import get_audit_logs

        # Create log for test_user
        log = AuditLog(
            user_id=test_user.id,
            aws_account_id=test_account.id,
            action="STOP_EC2",
            resource_type="EC2",
            resource_id="i-0abc123",
            description="Test log",
            estimated_saving=25.0,
            status="success",
        )
        db.add(log)
        db.commit()

        result = get_audit_logs(db, test_user.cognito_sub)
        assert result["total"] >= 1

        log_ids = [l["action"] for l in result["logs"]]
        assert "STOP_EC2" in log_ids

    def test_get_audit_stats(self, test_user, test_account, db):
        """Audit stats should sum savings from successful actions."""
        from app.database.models import AuditLog
        from app.services.audit_service import get_audit_stats

        logs = [
            AuditLog(user_id=test_user.id, aws_account_id=test_account.id,
                     action="STOP_EC2", resource_type="EC2", resource_id=f"i-{i}",
                     description="test", estimated_saving=25.0, status="success")
            for i in range(3)
        ]
        for log in logs:
            db.add(log)
        db.commit()

        stats = get_audit_stats(db, test_user.cognito_sub)
        assert stats["total_actions"]  >= 3
        assert stats["total_savings"]  >= 75.0   # 3 * $25

    def test_audit_filter_by_status(self, test_user, test_account, db):
        """Filter by status should work correctly."""
        from app.database.models import AuditLog
        from app.services.audit_service import get_audit_logs

        db.add(AuditLog(
            user_id=test_user.id, aws_account_id=test_account.id,
            action="DELETE_EBS", resource_type="EBS", resource_id="vol-filter",
            description="filtered", estimated_saving=5.0, status="dry_run",
        ))
        db.commit()

        # Filter by dry_run
        result = get_audit_logs(db, test_user.cognito_sub, status="dry_run")
        statuses = [l["status"] for l in result["logs"]]
        assert all(s == "dry_run" for s in statuses)

        # Filter by success — dry_run log should not appear
        result_success = get_audit_logs(db, test_user.cognito_sub, status="success")
        dry_run_ids = [l["resource_id"] for l in result_success["logs"] if l["resource_id"] == "vol-filter"]
        assert len(dry_run_ids) == 0
