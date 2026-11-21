"""
Account-Aware EC2 Service
All calls use the selected account's temporary credentials.
"""

from datetime import datetime, timedelta
from app.services.aws_client_factory import AWSClientFactory


def get_ec2_instances(aws: AWSClientFactory) -> list:
    ec2 = aws.ec2()
    cw  = aws.cloudwatch()

    response = ec2.describe_instances()
    instances = []

    end   = datetime.utcnow()
    start = end - timedelta(days=7)

    for reservation in response.get("Reservations", []):
        for inst in reservation.get("Instances", []):
            instance_id   = inst["InstanceId"]
            instance_type = inst["InstanceType"]
            state         = inst["State"]["Name"]
            launch_time   = inst.get("LaunchTime")

            name = next(
                (t["Value"] for t in inst.get("Tags", []) if t["Key"] == "Name"),
                instance_id,
            )

            # Get CPU utilization
            avg_cpu = None
            try:
                metrics = cw.get_metric_statistics(
                    Namespace="AWS/EC2",
                    MetricName="CPUUtilization",
                    Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                    StartTime=start,
                    EndTime=end,
                    Period=604800,
                    Statistics=["Average"],
                )
                if metrics["Datapoints"]:
                    avg_cpu = round(metrics["Datapoints"][0]["Average"], 2)
            except Exception:
                pass

            instances.append({
                "instance_id":   instance_id,
                "name":          name,
                "instance_type": instance_type,
                "state":         state,
                "region":        aws.account.default_region,
                "launch_time":   launch_time.isoformat() if launch_time else None,
                "avg_cpu_7d":    avg_cpu,
                "is_idle":       avg_cpu is not None and avg_cpu < 5 and state == "running",
                "az":            inst.get("Placement", {}).get("AvailabilityZone", ""),
                "public_ip":     inst.get("PublicIpAddress"),
                "private_ip":    inst.get("PrivateIpAddress"),
            })

    return instances


def get_unattached_ebs_volumes(aws: AWSClientFactory) -> list:
    ec2 = aws.ec2()
    response = ec2.describe_volumes(
        Filters=[{"Name": "status", "Values": ["available"]}]
    )
    volumes = []
    for vol in response.get("Volumes", []):
        create_time = vol["CreateTime"]
        age_days    = (datetime.now(create_time.tzinfo) - create_time).days
        size_gb     = vol["Size"]
        monthly_cost = round(size_gb * 0.10, 2)

        volumes.append({
            "volume_id":    vol["VolumeId"],
            "size_gb":      size_gb,
            "volume_type":  vol["VolumeType"],
            "age_days":     age_days,
            "monthly_cost": monthly_cost,
            "region":       aws.account.default_region,
            "severity":     "HIGH" if monthly_cost > 10 else "MEDIUM",
            "issue":        "Unattached EBS volume",
        })
    return volumes


def get_unassociated_eips(aws: AWSClientFactory) -> list:
    ec2  = aws.ec2()
    resp = ec2.describe_addresses()
    eips = []
    for addr in resp.get("Addresses", []):
        if not addr.get("AssociationId"):
            eips.append({
                "allocation_id": addr.get("AllocationId"),
                "public_ip":     addr.get("PublicIp"),
                "region":        aws.account.default_region,
                "monthly_cost":  3.60,
                "severity":      "MEDIUM",
                "issue":         "Unassociated Elastic IP",
            })
    return eips


def get_security_groups_open_ssh(aws: AWSClientFactory) -> list:
    ec2   = aws.ec2()
    resp  = ec2.describe_security_groups()
    risky = []
    for sg in resp.get("SecurityGroups", []):
        for rule in sg.get("IpPermissions", []):
            if rule.get("FromPort") in (22, 3389):
                for cidr in rule.get("IpRanges", []):
                    if cidr.get("CidrIp") == "0.0.0.0/0":
                        risky.append({
                            "group_id":   sg["GroupId"],
                            "group_name": sg["GroupName"],
                            "port":       rule["FromPort"],
                            "protocol":   "SSH" if rule["FromPort"] == 22 else "RDP",
                            "severity":   "HIGH",
                            "issue":      f"{'SSH' if rule['FromPort'] == 22 else 'RDP'} open to 0.0.0.0/0",
                        })
    return risky
