import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app_v2.database import SessionLocal
from app_v2.models.patient import PatientV2
from app_v2.models.encounter import EncounterV2
from app_v2.models.observation import ObservationV2

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
    # Handle "Patient/123" and "urn:uuid:123"
    if ref.startswith("urn:uuid:"):
        return ref.split(":")[-1]
    return ref.split("/")[-1]

def parse_iso_dt(v: Optional[str]) -> Optional[datetime]:
    if not v:
        return None
    v = v.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(v)
    except Exception:
        return None

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

# -----------------------------
# Minimal Patient upsert to resolve FK
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
        # fill only missing fields
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
# Encounter resolver (optional)
# -----------------------------
def resolve_encounter_id(db, encounter_reference: Optional[str], patient_id: Optional[int]) -> Optional[int]:
    """
    If your EncounterV2 model has an `identifier` column and you saved the FHIR Encounter.id there,
    this will try to link Observation.encounter -> EncounterV2.id.

    If not available, returns None and keeps observation.encounter_id = None.
    """
    if not encounter_reference:
        return None
    enc_ref = ref_id(encounter_reference)

    # Only attempt if EncounterV2 has an 'identifier' attribute
    if not hasattr(EncounterV2, "identifier"):
        return None

    # Look up by identifier; optionally also filter by patient_id if you want to be strict
    q = select(EncounterV2).where(EncounterV2.identifier == enc_ref)
    if patient_id is not None and hasattr(EncounterV2, "patient_id"):
        q = q.where(EncounterV2.patient_id == patient_id)

    found = db.execute(q).scalar_one_or_none()
    return found.id if found else None

# -----------------------------
# Observation extraction
# -----------------------------
def add_observation_row(db, patient_id: int, encounter_id: Optional[int], status: Optional[str],
                        category_code: Optional[str], code: Optional[str], system: Optional[str],
                        display: Optional[str], value_num: Optional[float], unit: Optional[str],
                        value_text: Optional[str], effective_time: Optional[datetime]):
    obs = ObservationV2(
        patient_id=patient_id,
        encounter_id=encounter_id,
        status=status,
        code=code,
        code_system=system,
        code_display=display,
        value_quantity=value_num,
        value_unit=unit,
        value_string=value_text,
        effective_time=effective_time,
    )
    db.add(obs)

def import_observations_from_bundle(bundle_path: Path):
    print(f"[observations] Reading: {bundle_path}")
    with open(bundle_path, "r", encoding="utf-8") as f:
        bundle = json.load(f)

    if bundle.get("resourceType") != "Bundle":
        print("[skip] Not a FHIR Bundle")
        return

    db = SessionLocal()
    pat_map: Dict[str, int] = {}

    try:
        # Pass 1: ensure Patient exists, build FHIR Patient.id -> DB id map
        for entry in bundle.get("entry", []) or []:
            res = entry.get("resource") or {}
            if res.get("resourceType") == "Patient":
                upsert_patient_min(db, res, pat_map)
        db.commit()

        # Pass 2: Observations
        inserted = 0
        for entry in bundle.get("entry", []) or []:
            res = entry.get("resource") or {}
            if res.get("resourceType") != "Observation":
                continue

            # Resolve patient
            patient_ref = ref_id(((res.get("subject") or {}).get("reference")))
            patient_id = pat_map.get(patient_ref)
            if not patient_id:
                # can't store observation without known patient
                continue

            # Resolve (optional) encounter FK
            encounter_ref = (res.get("encounter") or {}).get("reference")
            encounter_id = resolve_encounter_id(db, encounter_ref, patient_id)

            status = res.get("status")
            cat_sys, cat_code, cat_disp = coding0(res, "category")
            sys, code, disp = coding0(res, "code")
            effective = parse_iso_dt(res.get("effectiveDateTime") or (res.get("effectivePeriod") or {}).get("start"))

            # Case A: BP panel (85354-9) -> explode components
            if code == "85354-9" and isinstance(res.get("component"), list):
                for comp in res["component"]:
                    csys, ccode, cdisp = coding0(comp, "code")
                    vq = comp.get("valueQuantity") or {}
                    c_val = vq.get("value")
                    c_unit = vq.get("unit")
                    # also support valueString if present
                    if c_val is None and "valueString" in comp:
                        add_observation_row(db, patient_id, encounter_id, status, cat_code, ccode, csys, cdisp,
                                            None, None, comp.get("valueString"), effective)
                        inserted += 1
                    else:
                        add_observation_row(db, patient_id, encounter_id, status, cat_code, ccode, csys, cdisp,
                                            float(c_val) if isinstance(c_val, (int, float, str)) and str(c_val).replace('.','',1).isdigit() else None,
                                            c_unit, None, effective)
                        inserted += 1
                continue  # done with this Observation resource

            # Case B: Simple valueQuantity/valueString
            value_num = None
            unit = None
            value_text = None

            if "valueQuantity" in res:
                vq = res["valueQuantity"] or {}
                v = vq.get("value")
                unit = vq.get("unit")
                try:
                    value_num = float(v) if v is not None else None
                except Exception:
                    value_num = None  # fall back to text below if present
            elif "valueString" in res:
                value_text = res.get("valueString")
            elif "valueCodeableConcept" in res:
                # sometimes values are coded text
                _, _, value_text = coding0(res, "valueCodeableConcept")

            add_observation_row(db, patient_id, encounter_id, status, cat_code, code, sys, disp,
                                value_num, unit, value_text, effective)
            inserted += 1

        db.commit()
        print(f"[observations] Inserted {inserted} observation row(s) from {bundle_path.name}")
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
        import_observations_from_bundle(path)
    elif path.is_dir():
        files = list(path.glob("*.json"))
        if not files:
            print(f"No JSON files found in {path}")
            return
        for f in files:
            import_observations_from_bundle(f)
    else:
        print("Path not found:", path)

if __name__ == "__main__":
    # Default: import all bundles from this folder
    import_path(Path("./data/bundles"))
