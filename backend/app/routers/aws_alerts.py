import boto3
from app.config import settings

# ── Thresholds ────────────────────────────────────────────────
EC2_CPU_THRESHOLD      = 5.0    # % — below this = idle
EC2_EVAL_PERIODS       = 3      # 3 consecutive periods
EC2_PERIOD_SECONDS     = 1800   # 30 min each → 1.5 hrs total

EBS_CHECK_DAYS         = 7      # days unattached before alert
EIP_ALERT_IMMEDIATE    = True   # alert as soon as unused EIP found

SNS_TOPIC_NAME         = "finops-idle-resource-alerts"


def _sns(region=None):
    return boto3.client(
        "sns",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=region or settings.AWS_DEFAULT_REGION,
    )


def _cw(region=None):
    return boto3.client(
        "cloudwatch",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=region or settings.AWS_DEFAULT_REGION,
    )


def _ec2(region=None):
    return boto3.client(
        "ec2",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=region or settings.AWS_DEFAULT_REGION,
    )


# ── SNS Topic ─────────────────────────────────────────────────

def get_or_create_sns_topic() -> str:
    """Create SNS topic if not exists, return ARN."""
    sns = _sns()
    response = sns.create_topic(
        Name=SNS_TOPIC_NAME,
        Tags=[{"Key": "Project", "Value": "finops"}]
    )
    return response["TopicArn"]


def subscribe_email(email: str) -> dict:
    """Subscribe an email to the SNS topic."""
    topic_arn = get_or_create_sns_topic()
    sns = _sns()
    resp = sns.subscribe(
        TopicArn=topic_arn,
        Protocol="email",
        Endpoint=email,
        ReturnSubscriptionArn=True,
    )
    return {
        "topic_arn": topic_arn,
        "subscription_arn": resp["SubscriptionArn"],
        "message": f"Confirmation email sent to {email}. Please confirm to activate alerts.",
    }


def list_subscriptions() -> list:
    """List all email subscriptions for the finops topic."""
    try:
        topic_arn = get_or_create_sns_topic()
        sns = _sns()
        resp = sns.list_subscriptions_by_topic(TopicArn=topic_arn)
        return [
            {
                "email": s["Endpoint"],
                "status": "confirmed" if s["SubscriptionArn"] != "PendingConfirmation" else "pending",
                "arn": s["SubscriptionArn"],
            }
            for s in resp["Subscriptions"]
            if s["Protocol"] == "email"
        ]
    except Exception:
        return []


def unsubscribe_email(subscription_arn: str) -> dict:
    """Unsubscribe an email from the SNS topic."""
    sns = _sns()
    sns.unsubscribe(SubscriptionArn=subscription_arn)
    return {"message": "Unsubscribed successfully."}


# ── EC2 Alarms ────────────────────────────────────────────────

def create_ec2_idle_alarm(instance_id: str) -> dict:
    """Create CloudWatch alarm for idle EC2 instance."""
    topic_arn = get_or_create_sns_topic()
    cw = _cw()
    alarm_name = f"finops-idle-ec2-{instance_id}"

    cw.put_metric_alarm(
        AlarmName=alarm_name,
        AlarmDescription=(
            f"FinOps Alert: EC2 instance {instance_id} has been idle "
            f"(CPU < {EC2_CPU_THRESHOLD}%) for over 1.5 hours. "
            f"Consider stopping or rightsizing to save costs."
        ),
        ActionsEnabled=True,
        AlarmActions=[topic_arn],
        OKActions=[topic_arn],
        MetricName="CPUUtilization",
        Namespace="AWS/EC2",
        Statistic="Average",
        Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
        Period=EC2_PERIOD_SECONDS,
        EvaluationPeriods=EC2_EVAL_PERIODS,
        Threshold=EC2_CPU_THRESHOLD,
        ComparisonOperator="LessThanThreshold",
        TreatMissingData="missing",
        Tags=[{"Key": "Project", "Value": "finops"}],
    )
    return {
        "alarm_name": alarm_name,
        "resource_id": instance_id,
        "resource_type": "EC2",
        "message": f"Alarm created: alert fires if CPU < {EC2_CPU_THRESHOLD}% for 1.5 hrs",
    }


def delete_ec2_idle_alarm(instance_id: str) -> dict:
    """Delete CloudWatch alarm for EC2 instance."""
    cw = _cw()
    alarm_name = f"finops-idle-ec2-{instance_id}"
    cw.delete_alarms(AlarmNames=[alarm_name])
    return {"alarm_name": alarm_name, "message": "Alarm deleted successfully."}


# ── EBS Alarms ────────────────────────────────────────────────

def create_ebs_unattached_alert(volume_id: str) -> dict:
    """
    EBS doesn't have CloudWatch metrics for attachment status,
    so we publish a manual SNS notification immediately.
    """
    topic_arn = get_or_create_sns_topic()
    sns = _sns()
    sns.publish(
        TopicArn=topic_arn,
        Subject="FinOps Alert: Unattached EBS Volume Detected",
        Message=(
            f"FinOps Cost Optimizer detected an unattached EBS volume:\n\n"
            f"Volume ID : {volume_id}\n"
            f"Region    : {settings.AWS_DEFAULT_REGION}\n"
            f"Issue     : Volume is unattached and incurring storage costs\n"
            f"Action    : Delete the volume if not needed to save costs\n\n"
            f"AWS Console: https://console.aws.amazon.com/ec2/v2/home#Volumes:volumeId={volume_id}\n\n"
            f"-- FinOps Cost Optimizer"
        ),
    )
    return {
        "resource_id": volume_id,
        "resource_type": "EBS",
        "message": f"SNS notification sent for unattached EBS volume {volume_id}",
    }


# ── EIP Alarms ────────────────────────────────────────────────

def create_eip_unused_alert(allocation_id: str, public_ip: str) -> dict:
    """Publish SNS notification for unused Elastic IP."""
    topic_arn = get_or_create_sns_topic()
    sns = _sns()
    sns.publish(
        TopicArn=topic_arn,
        Subject="FinOps Alert: Unused Elastic IP Detected",
        Message=(
            f"FinOps Cost Optimizer detected an unused Elastic IP:\n\n"
            f"Allocation ID : {allocation_id}\n"
            f"Public IP     : {public_ip}\n"
            f"Region        : {settings.AWS_DEFAULT_REGION}\n"
            f"Issue         : Elastic IP not associated with any instance\n"
            f"Cost          : ~$3.60/month while unused\n"
            f"Action        : Release the Elastic IP if not needed\n\n"
            f"AWS Console: https://console.aws.amazon.com/ec2/v2/home#Addresses:\n\n"
            f"-- FinOps Cost Optimizer"
        ),
    )
    return {
        "resource_id": allocation_id,
        "resource_type": "EIP",
        "message": f"SNS notification sent for unused EIP {public_ip}",
    }


# ── Scan All & Alert ──────────────────────────────────────────

def scan_and_alert_all() -> dict:
    """
    Scan all resource types and send SNS alerts for detected waste.
    Also creates CloudWatch alarms for EC2 instances.
    Called manually or on a schedule.
    """
    region = settings.AWS_DEFAULT_REGION
    results = {"ec2": [], "ebs": [], "eip": [], "errors": []}

    # EC2
    try:
        ec2 = _ec2(region)
        cw  = _cw(region)
        instances = ec2.describe_instances(
            Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
        )
        for r in instances["Reservations"]:
            for inst in r["Instances"]:
                iid = inst["InstanceId"]
                # Check avg CPU over last 24h
                import datetime, pytz
                end   = datetime.datetime.now(pytz.utc)
                start = end - datetime.timedelta(hours=24)
                resp  = cw.get_metric_statistics(
                    Namespace="AWS/EC2",
                    MetricName="CPUUtilization",
                    Dimensions=[{"Name": "InstanceId", "Value": iid}],
                    StartTime=start, EndTime=end,
                    Period=3600, Statistics=["Average"],
                )
                pts = resp["Datapoints"]
                avg = sum(d["Average"] for d in pts) / len(pts) if pts else 0.0
                if avg < EC2_CPU_THRESHOLD:
                    alarm_result = create_ec2_idle_alarm(iid)
                    results["ec2"].append({**alarm_result, "avg_cpu": round(avg, 2)})
    except Exception as e:
        results["errors"].append(f"EC2 scan error: {str(e)}")

    # EBS
    try:
        ec2 = _ec2(region)
        vols = ec2.describe_volumes(
            Filters=[{"Name": "status", "Values": ["available"]}]
        )
        for vol in vols["Volumes"]:
            result = create_ebs_unattached_alert(vol["VolumeId"])
            results["ebs"].append(result)
    except Exception as e:
        results["errors"].append(f"EBS scan error: {str(e)}")

    # EIP
    try:
        ec2 = _ec2(region)
        addresses = ec2.describe_addresses()
        for addr in addresses["Addresses"]:
            if "AssociationId" not in addr:
                result = create_eip_unused_alert(
                    addr.get("AllocationId", "unknown"),
                    addr.get("PublicIp", "unknown"),
                )
                results["eip"].append(result)
    except Exception as e:
        results["errors"].append(f"EIP scan error: {str(e)}")

    return {
        "total_alerts_sent": len(results["ec2"]) + len(results["ebs"]) + len(results["eip"]),
        "ec2_alarms_created": len(results["ec2"]),
        "ebs_alerts_sent": len(results["ebs"]),
        "eip_alerts_sent": len(results["eip"]),
        "details": results,
    }


# ── List Active Alarms ────────────────────────────────────────

def list_active_alarms() -> list:
    """List all finops CloudWatch alarms and their state."""
    try:
        cw = _cw()
        resp = cw.describe_alarms(AlarmNamePrefix="finops-")
        alarms = []
        for a in resp["MetricAlarms"]:
            alarms.append({
                "alarm_name":   a["AlarmName"],
                "state":        a["StateValue"],        # OK / ALARM / INSUFFICIENT_DATA
                "description":  a["AlarmDescription"],
                "threshold":    a["Threshold"],
                "last_updated": a["StateUpdatedTimestamp"].isoformat(),
            })
        return alarms
    except Exception:
        return []
