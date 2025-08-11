import boto3
from botocore.client import Config
import os
import tempfile
from pathlib import Path


# --- Config from environment ---
SPACE_NAME = os.environ["SPACE_NAME"]
REGION = os.environ["REGION"]
ACCESS_KEY = os.environ["ACCESS_KEY"]
SECRET_KEY = os.environ["SECRET_KEY"]

# --- Boto3 Client Setup ---
session = boto3.session.Session()
client = session.client(
    "s3",
    region_name=REGION,
    endpoint_url=f"https://{REGION}.digitaloceanspaces.com",
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    config=Config(signature_version="s3v4")
)

# --- Reusable Functions ---
def list_objects(prefix=""):
    response = client.list_objects_v2(Bucket=SPACE_NAME, Prefix=prefix)
    return [obj["Key"] for obj in response.get("Contents", [])]

def upload_file(local_path, remote_path):
    client.upload_file(local_path, SPACE_NAME, remote_path)

def delete_file(remote_path):
    client.delete_object(Bucket=SPACE_NAME, Key=remote_path)

def generate_signed_url(remote_path, expires_in=3600):
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": SPACE_NAME, "Key": remote_path},
        ExpiresIn=expires_in
    )


def download_from_spaces_to_temp(remote_path):
    """
    Downloads a file from DigitalOcean Spaces to a temporary local file.
    Returns the local path.
    """
    temp_dir = Path(tempfile.gettempdir())
    local_path = temp_dir / Path(remote_path).name

    client.download_file(SPACE_NAME, remote_path, str(local_path))

    return local_path