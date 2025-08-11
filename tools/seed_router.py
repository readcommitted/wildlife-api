# seed_router.py
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
import os, datetime, re
import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError


router = APIRouter(prefix="/seed", tags=["Seed"])


# ---------- Config via env ----------
SPACE          = os.getenv("SPACE_NAME")
REGION         = os.getenv("SPACES_REGION", "nyc3")
ENDPOINT       = os.getenv("SPACES_ENDPOINT", f"https://{REGION}.digitaloceanspaces.com")
ACCESS_KEY     = os.getenv("SPACES_KEY", "")
SECRET_KEY     = os.getenv("SPACES_SECRET", "")
KEY_PREFIX     = os.getenv("SEED_PREFIX", "seed/")              # parent folder
DEFAULT_TTL    = int(os.getenv("SEED_SIGN_TTL_SEC", "3600"))    # 1 hour default
REQUIRED_FILES = [
    "species.csv.gz",
    "species_embeddings.parquet",
    "ecoregions.fgb",
]

# Optional: simple bearer token to protect the endpoint itself
SEED_API_TOKEN = os.getenv("SEED_API_TOKEN")  # if set, client must send Authorization: Bearer <token>


# ---------- Models ----------
class FileEntry(BaseModel):
    name: str
    size: Optional[int] = None
    url: str
    sha256: Optional[str] = None

class SignedManifest(BaseModel):
    version: str = Field(..., description="Version folder name, e.g., 2025-08-10")
    expires_in: int = Field(..., description="Seconds until URLs expire")
    species_csv_gz: str
    embeddings_parquet: str
    ecoregions_fgb: str
    files: List[FileEntry] = []


# ---------- Helpers ----------
def _s3_client():
    if not (ACCESS_KEY and SECRET_KEY):
        raise HTTPException(status_code=500, detail="Spaces credentials not configured.")
    session = boto3.session.Session()
    return session.client(
        "s3",
        region_name=REGION,
        endpoint_url=ENDPOINT,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        config=Config(s3={"addressing_style": "virtual"})
    )

def _latest_version(s3) -> str:
    """
    Lists subfolders under KEY_PREFIX (e.g., 'seed/') and returns the latest
    that looks like YYYY-MM-DD. Falls back to error if none found.
    """
    paginator = s3.get_paginator("list_objects_v2")
    # list top-level prefixes under seed/
    pages = paginator.paginate(Bucket=SPACE, Prefix=KEY_PREFIX, Delimiter="/")
    versions = []
    for page in pages:
        for cp in page.get("CommonPrefixes", []):
            folder = cp["Prefix"].rstrip("/").split("/")[-1]
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", folder):
                versions.append(folder)
    if not versions:
        raise HTTPException(status_code=404, detail="No version folders found in seed prefix.")
    # max by date; if your version has time, adjust parser
    return max(versions)

def _sign(s3, key: str, ttl: int) -> str:
    return s3.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": SPACE, "Key": key},
        ExpiresIn=ttl
    )

def _head_size(s3, key: str) -> Optional[int]:
    try:
        r = s3.head_object(Bucket=SPACE, Key=key)
        return r.get("ContentLength")
    except Exception:
        return None


# ---------- Optional endpoint protection ----------
def require_token(authorization: Optional[str] = None):
    if not SEED_API_TOKEN:
        return
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token.")
    token = authorization.split(" ", 1)[1].strip()
    if token != SEED_API_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token.")


# ---------- Routes ----------
@router.get("/manifest", response_model=SignedManifest)
def get_signed_manifest(
    version: Optional[str] = Query(None, description="Version folder name (YYYY-MM-DD). If omitted, uses latest."),
    ttl: int = Query(DEFAULT_TTL, ge=60, le=7*24*3600, description="URL expiry in seconds"),
    _auth = Depends(require_token)
):
    """
    Returns a manifest with pre-signed URLs for the specified (or latest) seed version in a *private* Spaces bucket.
    """
    try:
        s3 = _s3_client()
        ver = version or _latest_version(s3)
        base = f"{KEY_PREFIX}{ver}/"

        # ensure required files exist and sign them
        files: List[FileEntry] = []
        missing = []
        signed_map = {}
        for name in REQUIRED_FILES:
            key = base + name
            size = _head_size(s3, key)
            if size is None:
                missing.append(name)
                continue
            url = _sign(s3, key, ttl)
            files.append(FileEntry(name=name, size=size, url=url))
            signed_map[name] = url

        if missing:
            raise HTTPException(status_code=500, detail=f"Missing required files in version {ver}: {', '.join(missing)}")

        # Build response
        return SignedManifest(
            version=ver,
            expires_in=ttl,
            species_csv_gz=signed_map["species.csv.gz"],
            embeddings_parquet=signed_map["species_embeddings.parquet"],
            ecoregions_fgb=signed_map["ecoregions.fgb"],
            files=files
        )
    except HTTPException:
        raise
    except (BotoCoreError, ClientError) as e:
        raise HTTPException(status_code=502, detail=f"Spaces error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {e}")
