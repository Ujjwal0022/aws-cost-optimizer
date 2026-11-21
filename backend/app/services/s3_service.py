"""
Account-Aware S3 Service
"""

from app.services.aws_client_factory import AWSClientFactory


def get_s3_buckets(aws: AWSClientFactory) -> list:
    s3 = aws.s3()
    response = s3.list_buckets()
    buckets = []

    for bucket in response.get("Buckets", []):
        name        = bucket["Name"]
        created     = bucket.get("CreationDate")
        is_public   = False
        size_bytes  = 0
        obj_count   = 0

        # Check public access
        try:
            pub = s3.get_bucket_public_access_block(Bucket=name)
            config = pub.get("PublicAccessBlockConfiguration", {})
            is_public = not all([
                config.get("BlockPublicAcls", True),
                config.get("BlockPublicPolicy", True),
                config.get("RestrictPublicBuckets", True),
            ])
        except Exception:
            is_public = False

        # Get location
        try:
            loc_resp = s3.get_bucket_location(Bucket=name)
            region = loc_resp.get("LocationConstraint") or "us-east-1"
        except Exception:
            region = "unknown"

        buckets.append({
            "name":       name,
            "region":     region,
            "created":    created.isoformat() if created else None,
            "is_public":  is_public,
            "severity":   "HIGH" if is_public else "OK",
            "issue":      "Public bucket — data exposed!" if is_public else None,
        })

    return buckets
