"""
Tests for Recommendation Engine and Remediation Service.
All AWS calls mocked — no real resources modified.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


class TestRecommendationEngine:

    def test_ec2_rightsizing_recommendation(self):
        """Low CPU instance should trigger rightsizing recommendation."""
        mock_instances = [{
            "instance_id":   "i-0abc123",
            "name":          "test-server",
            "instance_type": "t3.large",
            "state":         "running",
            "avg_cpu_7d":    3.2,
            "is_idle":       False,
            "region":        "us-east-1",
        }]

        with patch("app.services.recommendation_service.get_ec2_instances") as mock_ec2:
            mock_ec2.return_value = mock_instances
            aws = MagicMock()
            aws.account.aws_account_id = "123456789012"
            aws.account.default_region  = "us-east-1"

            from app.services.recommendation_service import get_ec2_recommendations
            recs = get_ec2_recommendations(aws)

            assert len(recs) > 0
            rec = recs[0]
            assert rec["category"]       == "RIGHTSIZING"
            assert rec["resource_type"]  == "EC2"
            assert rec["resource_id"]    == "i-0abc123"
            assert rec["monthly_saving"] > 0
            assert rec["confidence"]     >= 80
            assert rec["risk"]           in ("LOW", "MEDIUM", "HIGH")
            assert "current_config"      in rec
            assert "recommended_config"  in rec
            assert "annual_saving"       in rec

    def test_idle_ec2_recommendation(self):
        """Very low CPU should trigger idle instance recommendation."""
        mock_instances = [{
            "instance_id":   "i-idle123",
            "name":          "idle-server",
            "instance_type": "t3.medium",
            "state":         "running",
            "avg_cpu_7d":    0.5,
            "is_idle":       True,
            "region":        "us-east-1",
        }]

        with patch("app.services.recommendation_service.get_ec2_instances") as mock_ec2:
            mock_ec2.return_value = mock_instances
            aws = MagicMock()
            aws.account.aws_account_id = "123456789012"
            aws.account.default_region  = "us-east-1"

            from app.services.recommendation_service import get_ec2_recommendations
            recs = get_ec2_recommendations(aws)

            idle_recs = [r for r in recs if r["category"] == "IDLE_RESOURCE"]
            assert len(idle_recs) > 0
            assert idle_recs[0]["resource_id"] == "i-idle123"

    def test_ebs_recommendation(self):
        """Unattached EBS volumes should generate recommendations."""
        mock_volumes = [{
            "volume_id":    "vol-0abc123",
            "size_gb":      50,
            "volume_type":  "gp2",
            "age_days":     30,
            "monthly_cost": 5.00,
            "region":       "us-east-1",
            "severity":     "MEDIUM",
            "issue":        "Unattached EBS volume",
        }]

        with patch("app.services.recommendation_service.get_unattached_ebs_volumes") as mock_ebs:
            mock_ebs.return_value = mock_volumes
            aws = MagicMock()

            from app.services.recommendation_service import get_ebs_recommendations
            recs = get_ebs_recommendations(aws)

            assert len(recs) == 1
            rec = recs[0]
            assert rec["resource_type"]  == "EBS"
            assert rec["monthly_saving"] == 5.00
            assert rec["annual_saving"]  == 60.00
            assert rec["confidence"]     == 95

    def test_eip_recommendation(self):
        """Unassociated EIP should generate recommendation."""
        mock_eips = [{
            "allocation_id": "eipalloc-0abc",
            "public_ip":     "52.1.2.3",
            "region":        "us-east-1",
            "monthly_cost":  3.60,
            "severity":      "MEDIUM",
            "issue":         "Unassociated Elastic IP",
        }]

        with patch("app.services.recommendation_service.get_unassociated_eips") as mock_eip:
            mock_eip.return_value = mock_eips
            aws = MagicMock()

            from app.services.recommendation_service import get_eip_recommendations
            recs = get_eip_recommendations(aws)

            assert len(recs) == 1
            assert recs[0]["resource_type"]  == "Elastic IP"
            assert recs[0]["confidence"]     == 99
            assert recs[0]["risk"]           == "LOW"

    def test_all_recommendations_sorted_by_saving(self):
        """All recommendations should be sorted by monthly_saving descending."""
        with patch("app.services.recommendation_service.get_ec2_recommendations") as m_ec2, \
             patch("app.services.recommendation_service.get_ebs_recommendations") as m_ebs, \
             patch("app.services.recommendation_service.get_eip_recommendations") as m_eip, \
             patch("app.services.recommendation_service.get_rds_recommendations") as m_rds, \
             patch("app.services.recommendation_service.get_lambda_recommendations") as m_lmb, \
             patch("app.services.recommendation_service.get_reserved_instance_recommendations") as m_ri:

            m_ec2.return_value = [{"monthly_saving": 45.0, "category": "RIGHTSIZING",
                                   "resource_type": "EC2", "resource_id": "i-1",
                                   "resource_name": "test", "issue": "x", "action": "y",
                                   "current_config": "a", "recommended_config": "b",
                                   "annual_saving": 540.0, "confidence": 90, "risk": "LOW",
                                   "details": {}, "created_at": datetime.utcnow().isoformat(),
                                   "id": "ec2-i-1-RIGHTSIZING"}]
            m_ebs.return_value = [{"monthly_saving": 100.0, "category": "IDLE_RESOURCE",
                                   "resource_type": "EBS", "resource_id": "vol-1",
                                   "resource_name": "vol-1", "issue": "x", "action": "y",
                                   "current_config": "a", "recommended_config": "b",
                                   "annual_saving": 1200.0, "confidence": 95, "risk": "MEDIUM",
                                   "details": {}, "created_at": datetime.utcnow().isoformat(),
                                   "id": "ebs-vol-1-IDLE_RESOURCE"}]
            m_eip.return_value = []
            m_rds.return_value = []
            m_lmb.return_value = []
            m_ri.return_value  = []

            aws = MagicMock()
            aws.account.aws_account_id = "123456789012"
            aws.account.account_name    = "Test"

            from app.services.recommendation_service import get_all_recommendations
            result = get_all_recommendations(aws)

            assert result["total_count"]    == 2
            assert result["monthly_savings"] == 145.0
            assert result["annual_savings"]  == 1740.0

            # Sorted descending
            savings = [r["monthly_saving"] for r in result["recommendations"]]
            assert savings == sorted(savings, reverse=True)

    def test_no_recommendations_for_healthy_account(self):
        """Healthy account should return 0 recommendations."""
        with patch("app.services.recommendation_service.get_ec2_recommendations") as m_ec2, \
             patch("app.services.recommendation_service.get_ebs_recommendations") as m_ebs, \
             patch("app.services.recommendation_service.get_eip_recommendations") as m_eip, \
             patch("app.services.recommendation_service.get_rds_recommendations") as m_rds, \
             patch("app.services.recommendation_service.get_lambda_recommendations") as m_lmb, \
             patch("app.services.recommendation_service.get_reserved_instance_recommendations") as m_ri:

            for m in [m_ec2, m_ebs, m_eip, m_rds, m_lmb, m_ri]:
                m.return_value = []

            aws = MagicMock()
            aws.account.aws_account_id = "123456789012"
            aws.account.account_name    = "Clean Account"

            from app.services.recommendation_service import get_all_recommendations
            result = get_all_recommendations(aws)

            assert result["total_count"]     == 0
            assert result["monthly_savings"] == 0
            assert result["annual_savings"]  == 0


class TestRemediationService:

    def test_stop_ec2_dry_run(self, test_user, test_account, db):
        """Dry run should log action but NOT call AWS stop_instances."""
        aws = MagicMock()
        aws.account.id = test_account.id

        with patch("app.services.remediation_service._log_action") as mock_log:
            mock_log.return_value = MagicMock(id="audit-log-123")

            from app.services.remediation_service import stop_ec2_instance
            result = stop_ec2_instance(
                aws=aws,
                instance_id="i-0abc123",
                db=db,
                user_id=test_user.id,
                account_db_id=test_account.id,
                dry_run=True,
                estimated_saving=25.0,
            )

            assert result["success"]  == True
            assert result["dry_run"]  == True
            assert "DRY RUN"          in result["message"]

            # Verify AWS was NOT called
            aws.ec2.return_value.stop_instances.assert_not_called()

            # Verify audit log was created
            mock_log.assert_called_once()
            call_kwargs = mock_log.call_args[1] if mock_log.call_args[1] else {}
            call_args   = mock_log.call_args[0]
            assert "dry_run" in str(call_args)

    def test_stop_ec2_real_execution(self, test_user, test_account, db):
        """Real execution should call AWS and log success."""
        mock_ec2_client = MagicMock()
        mock_ec2_client.stop_instances.return_value = {
            "StoppingInstances": [{"InstanceId": "i-0abc123", "CurrentState": {"Name": "stopping"}}]
        }

        aws = MagicMock()
        aws.ec2.return_value = mock_ec2_client
        aws.account.id = test_account.id

        from app.services.remediation_service import stop_ec2_instance
        result = stop_ec2_instance(
            aws=aws,
            instance_id="i-0abc123",
            db=db,
            user_id=test_user.id,
            account_db_id=test_account.id,
            dry_run=False,
            estimated_saving=25.0,
        )

        assert result["success"] == True
        assert result["dry_run"] == False
        mock_ec2_client.stop_instances.assert_called_once_with(InstanceIds=["i-0abc123"])

        # Verify audit log saved to DB
        from app.database.models import AuditLog
        logs = db.query(AuditLog).filter(AuditLog.resource_id == "i-0abc123").all()
        assert len(logs) == 1
        assert logs[0].status  == "success"
        assert logs[0].action  == "STOP_EC2"

    def test_delete_ebs_creates_snapshot_first(self, test_user, test_account, db):
        """EBS deletion should create safety snapshot before deleting."""
        mock_ec2_client = MagicMock()
        mock_ec2_client.create_snapshot.return_value = {"SnapshotId": "snap-0abc123"}
        mock_ec2_client.delete_volume.return_value = {}

        aws = MagicMock()
        aws.ec2.return_value = mock_ec2_client

        from app.services.remediation_service import delete_ebs_volume
        result = delete_ebs_volume(
            aws=aws,
            volume_id="vol-0abc123",
            db=db,
            user_id=test_user.id,
            account_db_id=test_account.id,
            dry_run=False,
            create_snapshot=True,
        )

        assert result["success"] == True
        assert result["snapshot_id"] == "snap-0abc123"

        # Snapshot created BEFORE delete
        call_order = mock_ec2_client.method_calls
        methods    = [str(c) for c in call_order]
        snap_idx   = next(i for i, m in enumerate(methods) if "create_snapshot" in m)
        del_idx    = next(i for i, m in enumerate(methods) if "delete_volume"   in m)
        assert snap_idx < del_idx

    def test_delete_ebs_dry_run_no_aws_calls(self, test_user, test_account, db):
        aws = MagicMock()

        from app.services.remediation_service import delete_ebs_volume
        result = delete_ebs_volume(
            aws=aws,
            volume_id="vol-dry123",
            db=db,
            user_id=test_user.id,
            account_db_id=test_account.id,
            dry_run=True,
        )

        assert result["dry_run"] == True
        aws.ec2.return_value.create_snapshot.assert_not_called()
        aws.ec2.return_value.delete_volume.assert_not_called()

    def test_release_eip(self, test_user, test_account, db):
        mock_ec2_client = MagicMock()
        mock_ec2_client.release_address.return_value = {}

        aws = MagicMock()
        aws.ec2.return_value = mock_ec2_client

        from app.services.remediation_service import release_elastic_ip
        result = release_elastic_ip(
            aws=aws,
            allocation_id="eipalloc-0abc123",
            db=db,
            user_id=test_user.id,
            account_db_id=test_account.id,
            dry_run=False,
            estimated_saving=3.60,
        )

        assert result["success"] == True
        mock_ec2_client.release_address.assert_called_once_with(AllocationId="eipalloc-0abc123")

    def test_failed_action_logged(self, test_user, test_account, db):
        """Failed AWS actions should be logged with status=failed."""
        mock_ec2_client = MagicMock()
        from botocore.exceptions import ClientError
        mock_ec2_client.stop_instances.side_effect = ClientError(
            {"Error": {"Code": "InvalidInstanceID.NotFound", "Message": "Instance not found"}},
            "stop_instances"
        )

        aws = MagicMock()
        aws.ec2.return_value = mock_ec2_client

        from app.services.remediation_service import stop_ec2_instance
        with pytest.raises(ValueError):
            stop_ec2_instance(
                aws=aws,
                instance_id="i-nonexistent",
                db=db,
                user_id=test_user.id,
                account_db_id=test_account.id,
                dry_run=False,
            )

        # Failed action should be logged
        from app.database.models import AuditLog
        logs = db.query(AuditLog).filter(
            AuditLog.resource_id == "i-nonexistent",
            AuditLog.status      == "failed",
        ).all()
        assert len(logs) == 1
        assert logs[0].error_message is not None
