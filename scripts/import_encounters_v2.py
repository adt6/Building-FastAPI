import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app_v2.database import SessionLocal
from app_v2.models.patient import PatientV2
from app_v2.models.practitioner import PractitionerV2
from app_v2.models.organization import OrganizationV2
from app_v2.models.encounter import EncounterV2

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

def human_name(resource: Dict[str, Any]):
    nm = first_or_none(resource.get("name", []) or [])
    if not nm:
        return None, None, None
    family = nm.get("family")
    given0 = first_or_none(nm.get("given", []) or [])
    text = nm.get("text")
    return given0, family, text

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

def parse_iso_dt(v: Optional[str]) -> Optional[datetime]:
    if not v:
        return None
    v = v.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(v)
    except Exception:
        return None

def ref_id(ref: Optional[str]) -> Optional[str]:
    if not ref or not isinstance(ref, str):
        return None
    # Handle both formats: "Patient/123" and "urn:uuid:123"
    if ref.startswith("urn:uuid:"):
        return ref.split(":")[-1]
    return ref.split("/")[-1]

def patient_identifier_from_resource(p: Dict[str, Any]) -> Optional[str]:
    ident = first_or_none(p.get("identifier", []) or [])
    if ident and isinstance(ident, dict):
        return ident.get("value")
    return None

# -----------------------------
# Minimal upserts to resolve FKs
# -----------------------------
def upsert_patient_min(db, res: Dict[str, Any], pat_map: Dict[str, int]):
    fid = res.get("id")
    identifier = patient_identifier_from_resource(res) or fid
    given, family, text = human_name(res)
    birth = res.get("birthDate")
    gender = res.get("gender")
    phone = telecom_value(res, "phone")
    email = telecom_value(res, "email")
    line, city, state, postal = address_fields(res)
    active = res.get("active", True)

    obj = None
    if identifier:
        obj = db.execute(select(PatientV2).where(PatientV2.identifier == identifier)).scalar_one_or_none()

    if obj:
        # fill missing fields only
        obj.first_name = obj.first_name or (given or (text or "").split(" ")[0] if text else "Unknown")
        obj.last_name  = obj.last_name  or (family or (text or "").split(" ")[-1] if text else "Unknown")
        obj.birth_date = obj.birth_date or birth
        if not obj.gender and gender:
            obj.gender = gender
        obj.phone = obj.phone or phone
        obj.email = obj.email or email
        obj.address_line = obj.address_line or line
        obj.city = obj.city or city
        obj.state = obj.state or state
        obj.postal_code = obj.postal_code or postal
        obj.active = active if obj.active is None else obj.active
    else:
        obj = PatientV2(
            identifier=identifier,
            first_name=given or (text or "").split(" ")[0] if text else "Unknown",
            last_name=family or (text or "").split(" ")[-1] if text else "Unknown",
            birth_date=birth,
            gender=gender,
            phone=phone,
            email=email,
            address_line=line,
            city=city,
            state=state,
            postal_code=postal,
            active=active,
        )
        db.add(obj)
        db.flush()

    if fid:
        pat_map[fid] = obj.id

def upsert_practitioner_min(db, res: Dict[str, Any], prac_map: Dict[str, int]):
    fid = res.get("id")
    ident = first_or_none(res.get("identifier", []) or [])
    identifier = (ident or {}).get("value")
    given, family, text = human_name(res)
    name = text or " ".join([part for part in [given, family] if part]) or "Unknown"
    phone = telecom_value(res, "phone")
    email = telecom_value(res, "email")
    gender = res.get("gender")

    obj = None
    if identifier:
        obj = db.execute(select(PractitionerV2).where(PractitionerV2.identifier == identifier)).scalar_one_or_none()
    if not obj:
        # try by name (not guaranteed unique)
        obj = db.execute(select(PractitionerV2).where(PractitionerV2.name == name)).scalar_one_or_none()

    if obj:
        obj.gender = obj.gender or gender
        obj.phone = obj.phone or phone
        obj.email = obj.email or email
    else:
        obj = PractitionerV2(
            identifier=identifier,
            name=name,
            gender=gender,
            phone=phone,
            email=email,
            organization_id=None,
        )
        db.add(obj)
        db.flush()

    if fid:
        prac_map[fid] = obj.id

def upsert_organization_min(db, res: Dict[str, Any], org_map: Dict[str, int]):
    fid = res.get("id")
    ident = first_or_none(res.get("identifier", []) or [])
    identifier = (ident or {}).get("value")
    name = res.get("name")
    sys, code, disp = coding0(res, "type")
    phone = telecom_value(res, "phone")
    email = telecom_value(res, "email")
    line, city, state, postal = address_fields(res)

    obj = None
    if identifier:
        obj = db.execute(select(OrganizationV2).where(OrganizationV2.identifier == identifier)).scalar_one_or_none()
    if not obj and name:
        obj = db.execute(select(OrganizationV2).where(OrganizationV2.name == name)).scalar_one_or_none()

    if obj:
        obj.type_code = obj.type_code or code
        obj.type_display = obj.type_display or disp
        obj.phone = obj.phone or phone
        obj.email = obj.email or email
        obj.address_line = obj.address_line or line
        obj.city = obj.city or city
        obj.state = obj.state or state
        obj.postal_code = obj.postal_code or postal
    else:
        obj = OrganizationV2(
            identifier=identifier,
            name=name or identifier or fid or "Unknown",
            type_code=code,
            type_display=disp,
            phone=phone,
            email=email,
            address_line=line,
            city=city,
            state=state,
            postal_code=postal,
        )
        db.add(obj)
        db.flush()

    if fid:
        org_map[fid] = obj.id

# -----------------------------
# Import Encounters from a single Bundle
# -----------------------------
def import_encounters_from_bundle(bundle_path: Path):
    print(f"[encounters] Reading: {bundle_path}")
    with open(bundle_path, "r", encoding="utf-8") as f:
        bundle = json.load(f)

    if bundle.get("resourceType") != "Bundle":
        print("[skip] Not a FHIR Bundle")
        return

    db = SessionLocal()
    pat_map: Dict[str, int] = {}
    prac_map: Dict[str, int] = {}
    org_map: Dict[str, int] = {}

    try:
        # Pass 1: ensure referenced entities exist and build maps
        for entry in bundle.get("entry", []) or []:
            res = entry.get("resource") or {}
            rt = res.get("resourceType")
            if rt == "Patient":
                upsert_patient_min(db, res, pat_map)
            elif rt == "Practitioner":
                upsert_practitioner_min(db, res, prac_map)
            elif rt == "Organization":
                upsert_organization_min(db, res, org_map)
        db.commit()

        # Pass 2: create Encounters
        inserted = 0
        for entry in bundle.get("entry", []) or []:
            res = entry.get("resource") or {}
            if res.get("resourceType") != "Encounter":
                continue

            status = res.get("status")
            class_code = (res.get("class") or {}).get("code")
            tsys, tcode, tdisp = coding0(res, "type")

            reason_code = None
            rc = first_or_none(res.get("reasonCode", []) or [])
            if rc:
                _, reason_code, _ = coding0(rc)

            start = parse_iso_dt(((res.get("period") or {}).get("start")))
            end = parse_iso_dt(((res.get("period") or {}).get("end")))

            patient_ref = ref_id(((res.get("subject") or {}).get("reference")))
            practitioner_ref = None
            part = first_or_none(res.get("participant", []) or [])
            if part:
                practitioner_ref = ref_id(((part.get("individual") or {}).get("reference")))
            org_ref = ref_id(((res.get("serviceProvider") or {}).get("reference")))

            patient_id = pat_map.get(patient_ref)
            practitioner_id = prac_map.get(practitioner_ref) if practitioner_ref else None
            organization_id = org_map.get(org_ref) if org_ref else None

            # must have at least patient + start
            if not patient_id or not start:
                continue

            enc = EncounterV2(
                patient_id=patient_id,
                practitioner_id=practitioner_id,
                organization_id=organization_id,
                status=status,
                class_code=class_code,
                class_display=None,  # Could extract from class if needed
                start_time=start,
                end_time=end,
                reason_code=reason_code,
                reason_display=None,  # Could extract from reasonCode if needed
                identifier=None,  # Could use encounter ID if needed
            )
            db.add(enc)
            inserted += 1

        db.commit()
        print(f"[encounters] Inserted {inserted} encounter(s) from {bundle_path.name}")
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
        import_encounters_from_bundle(path)
    elif path.is_dir():
        files = list(path.glob("*.json"))
        if not files:
            print(f"No JSON files found in {path}")
            return
        for f in files:
            import_encounters_from_bundle(f)
    else:
        print("Path not found:", path)

if __name__ == "__main__":
    # Default: import all bundles in this folder
    import_path(Path("./data/bundles"))
