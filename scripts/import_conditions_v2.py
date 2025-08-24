
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app_v2.database import SessionLocal
from app_v2.models.patient import PatientV2
from app_v2.models.condition import ConditionV2

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

def patient_identifier_from_resource(p: Dict[str, Any]) -> Optional[str]:
    ident = first_or_none(p.get("identifier", []) or [])
    if ident and isinstance(ident, dict):
        return ident.get("value")
    return None

def ref_id(ref: Optional[str]) -> Optional[str]:
    if not ref or not isinstance(ref, str):
        return None
    # Handle both formats: "Patient/123" and "urn:uuid:123"
    if ref.startswith("urn:uuid:"):
        return ref.split(":")[-1]
    return ref.split("/")[-1]

def coding0(resource: Dict[str, Any], *path):
    cur = resource
    for p in path:
        cur = (cur or {}).get(p)
    # now expect CodeableConcept -> coding[0]
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

# -----------------------------
# Core: upsert one Patient from a resource (minimal fields)
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
        # Update minimal fields if missing
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

# -----------------------------
# Import Conditions from a single Bundle
# -----------------------------
def import_conditions_from_bundle(bundle_path: Path):
    print(f"[conditions] Reading: {bundle_path}")
    with open(bundle_path, "r", encoding="utf-8") as f:
        bundle = json.load(f)

    if bundle.get("resourceType") != "Bundle":
        print("[skip] Not a FHIR Bundle")
        return

    db = SessionLocal()
    pat_map: Dict[str, int] = {}

    try:
        # Pass 1: ensure Patient exists (and build FHIR id -> DB id map)
        for entry in bundle.get("entry", []) or []:
            res = entry.get("resource") or {}
            if res.get("resourceType") == "Patient":
                upsert_patient_min(db, res, pat_map)
        db.commit()

        # Pass 2: insert Conditions
        inserted = 0
        for entry in bundle.get("entry", []) or []:
            res = entry.get("resource") or {}
            if res.get("resourceType") != "Condition":
                continue

            patient_ref = ref_id(((res.get("subject") or {}).get("reference")))
            patient_id = pat_map.get(patient_ref)
            if not patient_id:
                # If patient wasn't in this bundle, skip (or you could look up by identifier)
                continue

            sys, code, disp = coding0(res, "code")
            # statuses
            clin = first_or_none((res.get("clinicalStatus") or {}).get("coding", []) or [])
            ver  = first_or_none((res.get("verificationStatus") or {}).get("coding", []) or [])
            clinical_status = (clin or {}).get("code")
            verification_status = (ver or {}).get("code")

            onset = res.get("onsetDateTime") or res.get("onsetDate")
            abate = res.get("abatementDateTime") or res.get("abatementDate")
            recorded = res.get("recordedDate")

            cond = ConditionV2(
                patient_id=patient_id,
                encounter_id=None,  # You can link later if you import encounters and keep a map
                code=code or "unknown",
                system=sys,
                display=disp,
                category_code=None,
                clinical_status=clinical_status,
                verification_status=verification_status,
                onset_time=parse_iso_dt(onset),
                abatement_time=parse_iso_dt(abate),
                recorded_date=parse_iso_dt(recorded),
            )
            db.add(cond)
            inserted += 1

        db.commit()
        print(f"[conditions] Inserted {inserted} condition(s) from {bundle_path.name}")
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
        import_conditions_from_bundle(path)
    elif path.is_dir():
        files = list(path.glob("*.json"))
        if not files:
            print(f"No JSON files found in {path}")
            return
        for f in files:
            import_conditions_from_bundle(f)
    else:
        print("Path not found:", path)

if __name__ == "__main__":
    # Default: read every *.json in ./data/bundles
    import_path(Path("./data/bundles"))
