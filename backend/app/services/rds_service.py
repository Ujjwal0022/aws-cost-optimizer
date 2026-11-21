"""
Account-Aware RDS Service
"""

from datetime import datetime, timedelta
from app.services.aws_client_factory import AWSClientFactory


def get_rds_instances(aws: AWSClientFactory) -> list:
    rds = aws.rds()
    cw  = aws.cloudwatch()

    response  = rds.describe_db_instances()
    instances = []
    end   = datetime.utcnow()
    start = end - timedelta(days=7)

    for db in response.get("DBInstances", []):
        db_id    = db["DBInstanceIdentifier"]
        db_class = db["DBInstanceClass"]
        engine   = db["Engine"]
        status   = db["DBInstanceStatus"]

        # Check connections
        avg_connections = None
        try:
            metrics = cw.get_metric_statistics(
                Namespace="AWS/RDS",
                MetricName="DatabaseConnections",
                Dimensions=[{"Name": "DBInstanceIdentifier", "Value": db_id}],
                StartTime=start, EndTime=end,
                Period=604800, Statistics=["Average"],
            )
            if metrics["Datapoints"]:
                avg_connections = round(metrics["Datapoints"][0]["Average"], 2)
        except Exception:
            pass

        instances.append({
            "db_id":           db_id,
            "db_class":        db_class,
            "engine":          f"{engine} {db.get('EngineVersion', '')}",
            "status":          status,
            "multi_az":        db.get("MultiAZ", False),
            "avg_connections": avg_connections,
            "is_idle":         avg_connections is not None and avg_connections < 1,
            "region":          aws.account.default_region,
            "endpoint":        db.get("Endpoint", {}).get("Address"),
            "issue":           "Idle database — no connections for 7 days" if avg_connections == 0 else None,
            "severity":        "HIGH" if avg_connections == 0 else "OK",
        })

    return instances
