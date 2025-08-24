import json
from pathlib import Path
from typing import Dict, Any, Optional, List

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app_v2.database import SessionLocal
from app_v2.models.practitioner import PractitionerV2
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

def name_fields(resource: Dict[str, Any]):
    name = first_or_none(resource.get("name", []) or [])
    if not name:
        return None, None, None
    
    prefix = first_or_none(name.get("prefix", []) or [])
    given = first_or_none(name.get("given", []) or [])
    family = name.get("family")
    
    # Combine prefix, given, and family into full name
    name_parts = []
    if prefix:
        name_parts.append(prefix)
    if given:
        name_parts.append(given)
    if family:
        name_parts.append(family)
    
    full_name = " ".join(name_parts) if name_parts else None
    return full_name, given, family

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

def get_organization_id(db, organization_identifier: Optional[str]) -> Optional[int]:
    """Get organization ID from identifier"""
    if not organization_identifier:
        return None
    
    org = db.execute(
        select(OrganizationV2).where(OrganizationV2.identifier == organization_identifier)
    ).scalar_one_or_none()
    
    return org.id if org else None

# -----------------------------
# Upsert one Practitioner
# -----------------------------
def upsert_practitioner(db, res: Dict[str, Any]):
    fid = res.get("id")
    ident = first_or_none(res.get("identifier", []) or [])
    identifier = (ident or {}).get("value")
    
    full_name, given_name, family_name = name_fields(res)
    gender = res.get("gender")
    
    # Get specialty from qualification
    qualifications = res.get("qualification", []) or []
    specialty_code = None
    specialty_display = None
    if qualifications:
        qual = first_or_none(qualifications)
        if qual:
            sys, code, display = coding0(qual, "code")
            specialty_code = code
            specialty_display = display
    
    phone = telecom_value(res, "phone")
    email = telecom_value(res, "email")
    
    # Get organization from practitioner role
    organization_identifier = None
    practitioner_roles = res.get("practitionerRole", []) or []
    if practitioner_roles:
        role = first_or_none(practitioner_roles)
        if role and isinstance(role, dict):
            org_ref = role.get("organization", {}).get("reference")
            if org_ref:
                organization_identifier = ref_id(org_ref)
    
    organization_id = get_organization_id(db, organization_identifier)

    # Try existing rows
    obj = None
    if identifier:
        obj = db.execute(
            select(PractitionerV2).where(PractitionerV2.identifier == identifier)
        ).scalar_one_or_none()

    if not obj and full_name:
        obj = db.execute(
            select(PractitionerV2).where(PractitionerV2.name == full_name)
        ).scalar_one_or_none()

    if obj:
        # Update only if empty (avoid clobbering)
        obj.gender = obj.gender or gender
        obj.specialty_code = obj.specialty_code or specialty_code
        obj.specialty_display = obj.specialty_display or specialty_display
        obj.phone = obj.phone or phone
        obj.email = obj.email or email
        if organization_id and not obj.organization_id:
            obj.organization_id = organization_id
    else:
        obj = PractitionerV2(
            identifier=identifier,
            name=full_name or identifier or fid or "Unknown",
            gender=gender,
            specialty_code=specialty_code,
            specialty_display=specialty_display,
            phone=phone,
            email=email,
            organization_id=organization_id,
        )
        db.add(obj)
        # db.flush() not required unless you need obj.id immediately

# -----------------------------
# Import Practitioners from a single Bundle
# -----------------------------
def import_practitioners_from_bundle(bundle_path: Path):
    print(f"[practitioners] Reading: {bundle_path}")
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
            if res.get("resourceType") != "Practitioner":
                continue
            upsert_practitioner(db, res)
            inserted_or_upserted += 1

        db.commit()
        print(f"[practitioners] Upserted {inserted_or_upserted} practitioner(s) from {bundle_path.name}")
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
        import_practitioners_from_bundle(path)
    elif path.is_dir():
        files = list(path.glob("*.json"))
        if not files:
            print(f"No JSON files found in {path}")
            return
        for f in files:
            import_practitioners_from_bundle(f)
    else:
        print("Path not found:", path)

if __name__ == "__main__":
    # Default: import all bundles from this folder
    import_path(Path("./data/bundles"))
