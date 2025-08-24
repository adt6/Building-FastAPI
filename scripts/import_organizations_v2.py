import json
from pathlib import Path
from typing import Dict, Any, Optional, List

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app_v2.database import SessionLocal
from app_v2.models.organization import OrganizationV2

# -----------------------------
# Helpers
# -----------------------------
def first_or_none(x):
    return x[0] if isinstance(x, list) and x else None

def telecom_value(resource: Dict[str, Any], system: str) -> Optional[str]:
    for t in resource.get("telecom", []) or []:
        if t.get("system") == system:
            return t.get("value")
    return None

def address_fields(resource: Dict[str, Any]):
    addr = first_or_none(resource.get("address", []) or [])
    if not addr:
        return None, None, None, None
    line0 = first_or_none(addr.get("line", []) or [])
    return line0, addr.get("city"), addr.get("state"), addr.get("postalCode")

def coding0(resource: Dict[str, Any], *path):
    cur = resource
    for p in path:
        cur = (cur or {}).get(p)
    # expect CodeableConcept -> coding[0]
    coding = None
    if isinstance(cur, dict):
        coding = first_or_none(cur.get("coding", []) or [])
    elif isinstance(cur, list):
        cc = first_or_none(cur)
        if isinstance(cc, dict):
            coding = first_or_none(cc.get("coding", []) or [])
    if not coding:
        return None, None, None
    return coding.get("system"), coding.get("code"), coding.get("display")

def ref_id(ref: Optional[str]) -> Optional[str]:
    if not ref or not isinstance(ref, str):
        return None
    # Handle both "Organization/123" and "urn:uuid:123"
    if ref.startswith("urn:uuid:"):
        return ref.split(":")[-1]
    return ref.split("/")[-1]

# -----------------------------
# Upsert one Organization
# -----------------------------
def upsert_organization(db, res: Dict[str, Any]):
    fid = res.get("id")
    ident = first_or_none(res.get("identifier", []) or [])
    identifier = (ident or {}).get("value")
    name = res.get("name")

    sys, type_code, type_display = coding0(res, "type")
    phone = telecom_value(res, "phone")
    email = telecom_value(res, "email")
    line, city, state, postal = address_fields(res)
    part_of_identifier = ref_id(((res.get("partOf") or {}).get("reference")))

    # Try existing rows
    obj = None
    if identifier:
        obj = db.execute(
            select(OrganizationV2).where(OrganizationV2.identifier == identifier)
        ).scalar_one_or_none()

    if not obj and name:
        obj = db.execute(
            select(OrganizationV2).where(OrganizationV2.name == name)
        ).scalar_one_or_none()

    if obj:
        # Update only if empty (avoid clobbering)
        obj.type_code = obj.type_code or type_code
        obj.type_display = obj.type_display or type_display
        obj.phone = obj.phone or phone
        obj.email = obj.email or email
        obj.address_line = obj.address_line or line
        obj.city = obj.city or city
        obj.state = obj.state or state
        obj.postal_code = obj.postal_code or postal
        if part_of_identifier and not obj.part_of_identifier:
            obj.part_of_identifier = part_of_identifier
    else:
        obj = OrganizationV2(
            identifier=identifier,
            name=name or identifier or fid or "Unknown",
            type_code=type_code,
            type_display=type_display,
            phone=phone,
            email=email,
            address_line=line,
            city=city,
            state=state,
            postal_code=postal,
            part_of_identifier=part_of_identifier,
        )
        db.add(obj)
        # db.flush() not required unless you need obj.id immediately

# -----------------------------
# Import Organizations from a single Bundle
# -----------------------------
def import_organizations_from_bundle(bundle_path: Path):
    print(f"[organizations] Reading: {bundle_path}")
    with open(bundle_path, "r", encoding="utf-8") as f:
        bundle = json.load(f)

    if bundle.get("resourceType") != "Bundle":
        print("[skip] Not a FHIR Bundle")
        return

    db = SessionLocal()
    inserted_or_upserted = 0
    try:
        for entry in bundle.get("entry", []) or []:
            res = entry.get("resource") or {}
            if res.get("resourceType") != "Organization":
                continue
            upsert_organization(db, res)
            inserted_or_upserted += 1

        db.commit()
        print(f"[organizations] Upserted {inserted_or_upserted} org(s) from {bundle_path.name}")
    except IntegrityError as ie:
        db.rollback()
        print(f"[warn] IntegrityError in {bundle_path.name}: {ie}")
    except Exception as e:
        db.rollback()
        print(f"[error] Failed on {bundle_path.name}: {e}")
    finally:
        db.close()

# -----------------------------
# Entry point: folder or single file
# -----------------------------
def import_path(path: Path):
    if path.is_file():
        import_organizations_from_bundle(path)
    elif path.is_dir():
        files = list(path.glob("*.json"))
        if not files:
            print(f"No JSON files found in {path}")
            return
        for f in files:
            import_organizations_from_bundle(f)
    else:
        print("Path not found:", path)

if __name__ == "__main__":
    # Default: import all bundles from this folder
    import_path(Path("./data/bundles"))
