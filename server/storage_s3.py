
import os, json, time, hashlib
from typing import Dict, Any, Optional
import boto3

S3_BUCKET = os.environ.get("S3_BUCKET", "")
S3_PREFIX = os.environ.get("S3_PREFIX", "provenance/")

def _client():
    return boto3.client("s3",
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        region_name=os.environ.get("AWS_REGION", "us-east-1"))

def put_json(obj: Dict[str, Any], key_hint: str = "row") -> Optional[str]:
    if not S3_BUCKET:
        return None
    b = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    sha = hashlib.sha256(b).hexdigest()[:16]
    key = f"{S3_PREFIX}{key_hint}-{int(time.time())}-{sha}.json"
    _client().put_object(Bucket=S3_BUCKET, Key=key, Body=b, ContentType="application/json")
    return key

def presign(key: str, expires: int = 86400) -> Optional[str]:
    if not S3_BUCKET: return None
    return _client().generate_presigned_url("get_object", Params={"Bucket": S3_BUCKET, "Key": key}, ExpiresIn=expires)
