
#!/usr/bin/env python3
"""Configure lifecycle policy for provenance snapshots (S3/S3-compatible).

Usage:
  AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... AWS_REGION=us-east-1 \  S3_BUCKET=your-bucket python scripts/s3_lifecycle.py --prefix provenance/ --days 90
"""
import os, json, argparse, sys
import boto3

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--bucket", default=os.environ.get("S3_BUCKET"))
    p.add_argument("--prefix", default=os.environ.get("S3_PREFIX", "provenance/"))
    p.add_argument("--days", type=int, default=90)
    args = p.parse_args()
    if not args.bucket:
        print("S3_BUCKET is required (or pass --bucket)"); sys.exit(1)
    s3 = boto3.client("s3",
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        region_name=os.environ.get("AWS_REGION","us-east-1"))
    rules = {
      "Rules": [{
        "ID": "otp-provenance-expire",
        "Status": "Enabled",
        "Filter": {"Prefix": args.prefix},
        "Expiration": {"Days": args.days},
        "NoncurrentVersionExpiration": {"NoncurrentDays": args.days}
      }]
    }
    s3.put_bucket_lifecycle_configuration(Bucket=args.bucket, LifecycleConfiguration=rules)
    print(f"Applied lifecycle: prefix={args.prefix} expire={args.days}d on bucket {args.bucket}")
if __name__ == "__main__":
    main()
