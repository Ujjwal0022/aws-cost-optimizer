"""
Account-Aware Lambda + EKS Service
"""

from datetime import datetime, timedelta
from app.services.aws_client_factory import AWSClientFactory


# ── Lambda ────────────────────────────────────────────────────────────────────
def get_lambda_functions(aws: AWSClientFactory) -> list:
    lmb = aws.lambda_client()
    cw  = aws.cloudwatch()

    paginator = lmb.get_paginator("list_functions")
    functions = []
    end   = datetime.utcnow()
    start = end - timedelta(days=30)

    for page in paginator.paginate():
        for fn in page.get("Functions", []):
            fn_name = fn["FunctionName"]
            runtime = fn.get("Runtime", "unknown")
            memory  = fn.get("MemorySize", 128)
            timeout = fn.get("Timeout", 3)

            # Get invocation count
            invocations = 0
            try:
                metrics = cw.get_metric_statistics(
                    Namespace="AWS/Lambda",
                    MetricName="Invocations",
                    Dimensions=[{"Name": "FunctionName", "Value": fn_name}],
                    StartTime=start, EndTime=end,
                    Period=2592000, Statistics=["Sum"],
                )
                if metrics["Datapoints"]:
                    invocations = int(metrics["Datapoints"][0]["Sum"])
            except Exception:
                pass

            functions.append({
                "function_name": fn_name,
                "runtime":       runtime,
                "memory_mb":     memory,
                "timeout_s":     timeout,
                "invocations_30d": invocations,
                "is_idle":       invocations == 0,
                "region":        aws.account.default_region,
                "last_modified": fn.get("LastModified"),
                "code_size_mb":  round(fn.get("CodeSize", 0) / 1024 / 1024, 2),
                "issue":         "No invocations in 30 days — consider removing" if invocations == 0 else None,
                "severity":      "LOW" if invocations == 0 else "OK",
            })

    return functions


# ── EKS ───────────────────────────────────────────────────────────────────────
def get_eks_clusters(aws: AWSClientFactory) -> list:
    eks = aws.eks()

    try:
        cluster_names = eks.list_clusters().get("clusters", [])
    except Exception:
        return []

    clusters = []
    for name in cluster_names:
        try:
            detail = eks.describe_cluster(name=name)["cluster"]
            node_groups = []

            try:
                ng_names = eks.list_nodegroups(clusterName=name).get("nodegroups", [])
                for ng_name in ng_names:
                    ng = eks.describe_nodegroup(
                        clusterName=name, nodegroupName=ng_name
                    )["nodegroup"]
                    node_groups.append({
                        "name":          ng_name,
                        "status":        ng["status"],
                        "instance_type": ng.get("instanceTypes", []),
                        "desired":       ng.get("scalingConfig", {}).get("desiredSize", 0),
                        "min":           ng.get("scalingConfig", {}).get("minSize", 0),
                        "max":           ng.get("scalingConfig", {}).get("maxSize", 0),
                        "capacity_type": ng.get("capacityType", "ON_DEMAND"),
                    })
            except Exception:
                pass

            clusters.append({
                "name":        name,
                "status":      detail["status"],
                "version":     detail["version"],
                "region":      aws.account.default_region,
                "endpoint":    detail.get("endpoint"),
                "node_groups": node_groups,
                "created_at":  detail.get("createdAt", "").isoformat() if hasattr(detail.get("createdAt", ""), "isoformat") else str(detail.get("createdAt", "")),
            })
        except Exception:
            clusters.append({"name": name, "status": "unknown", "region": aws.account.default_region})

    return clusters
