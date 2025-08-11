# seed_router.py

from fastapi import APIRouter, HTTPException, Query, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import os, re
from tools import spaces


router = APIRouter(prefix="/seed", tags=["Seed"])


KEY_PREFIX = os.getenv("SEED_PREFIX", "seed/")
DEFAULT_TTL = int(os.getenv("SEED_SIGN_TTL_SEC", "3600"))
SEED_API_TOKEN = os.getenv("SEED_API_TOKEN")


# ---------- Models ----------
class FileEntry(BaseModel):
    name: str
    size: Optional[int] = None
    sha256: Optional[str] = None
    url: str

class SignedManifest(BaseModel):
    version: str
    generated_at: str
    expires_in: int
    files: List[FileEntry]


# ---------- Helpers ----------
def require_token(authorization: str | None = Header(default=None)):
    if not SEED_API_TOKEN:
        return
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token.")
    token = authorization.split(" ", 1)[1].strip()
    if token != SEED_API_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token.")

def _latest_version() -> str:
    """List version folders under KEY_PREFIX and return the most recent."""
    keys = spaces.list_objects(prefix=KEY_PREFIX)
    versions = set()
    for key in keys:
        parts = key[len(KEY_PREFIX):].split("/", 1)
        if parts and re.fullmatch(r"\d{4}-\d{2}-\d{2}", parts[0]):
            versions.add(parts[0])
    if not versions:
        raise HTTPException(status_code=404, detail="No version folders found in seed prefix.")
    return max(versions)

def _parse_checksums_blob(blob: bytes) -> dict:
    out = {}
    for line in blob.decode("utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([a-fA-F0-9]{64})\s+\*?\s*(.+)$", line)
        if m:
            out[m.group(2).strip()] = m.group(1).lower()
    return out

def _load_checksums(version: str) -> dict:
    try:
        tmp_path = spaces.download_from_spaces_to_temp(f"{KEY_PREFIX}{version}/checksums.sha256")
        with open(tmp_path, "rb") as f:
            return _parse_checksums_blob(f.read())
    except Exception:
        return {}


# ---------- Route ----------
@router.get("/manifest", response_model=SignedManifest)
def get_signed_manifest(
    version: Optional[str] = Query(None, description="YYYY-MM-DD; if omitted uses latest"),
    ttl: int = Query(DEFAULT_TTL, ge=60, le=7*24*3600),
    _auth = Depends(require_token),
):
    try:
        ver = version or _latest_version()
        base_prefix = f"{KEY_PREFIX}{ver}/"

        sha_map = _load_checksums(ver)
        all_keys = spaces.list_objects(prefix=base_prefix)

        files: List[FileEntry] = []
        for key in all_keys:
            if key.endswith("/") or key == base_prefix:
                continue
            name = key[len(base_prefix):]
            size = None
            try:
                # HEAD size via list_objects output (not in your wrapper) – quick workaround:
                from tools.spaces import client, SPACE_NAME
                size = next((obj["Size"] for obj in client.list_objects_v2(Bucket=SPACE_NAME, Prefix=key).get("Contents", []) if obj["Key"] == key), None)
            except Exception:
                pass

            files.append(FileEntry(
                name=name,
                size=size,
                sha256=sha_map.get(name),
                url=spaces.generate_signed_url(key, expires_in=ttl)
            ))

        if not files:
            raise HTTPException(status_code=404, detail=f"No files found under {base_prefix}")

        resp = SignedManifest(
            version=ver,
            generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            expires_in=ttl,
            files=files
        )
        return JSONResponse(content=resp.model_dump())

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {e}")
