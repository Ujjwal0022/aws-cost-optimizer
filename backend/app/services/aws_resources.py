import boto3
from datetime import datetime, timezone, timedelta
from app.config import settings
from app.models.schemas import ResourceRecommendation, ResourceSummaryResponse

def _ec2(region=None):
    return boto3.client("ec2", aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=region or settings.AWS_DEFAULT_REGION)

def _cw(region=None):
    return boto3.client("cloudwatch", aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=region or settings.AWS_DEFAULT_REGION)

def _rds(region=None):
    return boto3.client("rds", aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=region or settings.AWS_DEFAULT_REGION)

def _cpu_avg(instance_id, region, days=7):
    resp = _cw(region).get_metric_statistics(
        Namespace="AWS/EC2", MetricName="CPUUtilization",
        Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
        StartTime=datetime.now(timezone.utc) - timedelta(days=days),
        EndTime=datetime.now(timezone.utc), Period=86400, Statistics=["Average"])
    pts = resp["Datapoints"]
    return sum(d["Average"] for d in pts) / len(pts) if pts else 0.0

def check_idle_ec2(region):
    recs = []
    try:
        insts = _ec2(region).describe_instances(Filters=[{"Name":"instance-state-name","Values":["running"]}])
        for r in insts["Reservations"]:
            for i in r["Instances"]:
                iid = i["InstanceId"]
                cpu = _cpu_avg(iid, region)
                if cpu < 5.0:
                    recs.append(ResourceRecommendation(
                        resource_id=iid, resource_type="EC2", region=region, issue="idle",
                        estimated_monthly_savings=15.0,
                        recommendation=f"Instance {iid} ({i['InstanceType']}) avg CPU {cpu:.1f}% over 7 days. Stop or rightsize.",
                        severity="HIGH" if cpu < 1.0 else "MEDIUM"))
    except Exception:
        pass
    return recs

def check_unattached_ebs(region):
    recs = []
    try:
        vols = _ec2(region).describe_volumes(Filters=[{"Name":"status","Values":["available"]}])
        for v in vols["Volumes"]:
            recs.append(ResourceRecommendation(
                resource_id=v["VolumeId"], resource_type="EBS", region=region, issue="unattached",
                estimated_monthly_savings=round(v["Size"] * 0.10, 2),
                recommendation=f"EBS {v['VolumeId']} ({v['Size']}GB) unattached. Delete if not needed.",
                severity="MEDIUM"))
    except Exception:
        pass
    return recs

def check_unused_eips(region):
    recs = []
    try:
        for addr in _ec2(region).describe_addresses()["Addresses"]:
            if "AssociationId" not in addr:
                recs.append(ResourceRecommendation(
                    resource_id=addr.get("AllocationId", addr.get("PublicIp","unknown")),
                    resource_type="EIP", region=region, issue="unused",
                    estimated_monthly_savings=3.6,
                    recommendation=f"Elastic IP {addr.get('PublicIp')} is unassociated. Release it.",
                    severity="LOW"))
    except Exception:
        pass
    return recs

def check_old_snapshots(region):
    recs = []
    try:
        owner = settings.AWS_ACCOUNT_ID or "self"
        snaps = _ec2(region).describe_snapshots(OwnerIds=[owner])
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        for s in snaps["Snapshots"]:
            if s["StartTime"] < cutoff:
                recs.append(ResourceRecommendation(
                    resource_id=s["SnapshotId"], resource_type="Snapshot", region=region, issue="old",
                    estimated_monthly_savings=round(s["VolumeSize"] * 0.05, 2),
                    recommendation=f"Snapshot {s['SnapshotId']} ({s['VolumeSize']}GB) is {(datetime.now(timezone.utc)-s['StartTime']).days}d old.",
                    severity="LOW"))
    except Exception:
        pass
    return recs

def check_idle_rds(region):
    recs = []
    try:
        dbs = _rds(region).describe_db_instances()
        for db in dbs["DBInstances"]:
            if db["DBInstanceStatus"] != "available":
                continue
            db_id = db["DBInstanceIdentifier"]
            resp = _cw(region).get_metric_statistics(
                Namespace="AWS/RDS", MetricName="DatabaseConnections",
                Dimensions=[{"Name":"DBInstanceIdentifier","Value":db_id}],
                StartTime=datetime.now(timezone.utc)-timedelta(days=7),
                EndTime=datetime.now(timezone.utc), Period=86400, Statistics=["Average"])
            avg = sum(d["Average"] for d in resp["Datapoints"])/len(resp["Datapoints"]) if resp["Datapoints"] else 0.0
            if avg < 1.0:
                recs.append(ResourceRecommendation(
                    resource_id=db_id, resource_type="RDS", region=region, issue="idle",
                    estimated_monthly_savings=25.0,
                    recommendation=f"RDS {db_id} avg {avg:.1f} connections/day. Consider stopping.",
                    severity="HIGH"))
    except Exception:
        pass
    return recs

def fetch_all_recommendations():
    region = settings.AWS_DEFAULT_REGION
    all_recs = []
    all_recs.extend(check_idle_ec2(region))
    all_recs.extend(check_unattached_ebs(region))
    all_recs.extend(check_unused_eips(region))
    all_recs.extend(check_old_snapshots(region))
    all_recs.extend(check_idle_rds(region))
    order = {"HIGH":0,"MEDIUM":1,"LOW":2}
    all_recs.sort(key=lambda x: order.get(x.severity, 3))
    return ResourceSummaryResponse(
        total_estimated_savings=round(sum(r.estimated_monthly_savings for r in all_recs), 2),
        recommendations=all_recs)
