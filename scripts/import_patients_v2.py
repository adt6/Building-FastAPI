import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy.exc import IntegrityError
from app_v2.database import SessionLocal
from app_v2.models.patient import PatientV2

# ---------- helpers to read FHIR fields ----------

def first_or_none(x: Optional[List[Any]]):
    return x[0] if isinstance(x, list) and x else None

def telecom_value(resource: Dict[str, Any], system: str) -> Optional[str]:
    telecom = resource.get("telecom", [])
    for t in telecom:
        if t.get("system") == system:
            return t.get("value")
    return None

def address_fields(resource: Dict[str, Any]):
    addr = first_or_none(resource.get("address", [])) or {}
    line0 = first_or_none(addr.get("line", []))
    return line0, addr.get("city"), addr.get("state"), addr.get("postalCode")

def human_name(resource: Dict[str, Any]):
    name = first_or_none(resource.get("name", [])) or {}
    given0 = first_or_none(name.get("given", []))
    family = name.get("family")
    text = name.get("text")  # sometimes Synthea fills this
    return given0, family, text

def patient_identifier(resource: Dict[str, Any]) -> Optional[str]:
    ident = first_or_none(resource.get("identifier", [])) or {}
    return ident.get("value")

def get_marital_status(resource: Dict[str, Any]) -> Optional[str]:
    ms = resource.get("maritalStatus")
    if not isinstance(ms, dict):
        return None
    coding = first_or_none(ms.get("coding", [])) or {}
    # return code or display
    return coding.get("code") or coding.get("display")

def get_language(resource: Dict[str, Any]) -> Optional[str]:
    comm = first_or_none(resource.get("communication", [])) or {}
    lang = comm.get("language", {})
    coding = first_or_none(lang.get("coding", [])) or {}
    return coding.get("code") or coding.get("display")

def get_extensions_value(resource: Dict[str, Any], url_match: str) -> Optional[str]:
    """
    For Synthea US Core race/ethnicity extensions.
    We return the first matching 'display' or 'code'.
    """
    for ext in resource.get("extension", []) or []:
        if ext.get("url") == url_match:
            # variant 1: ext.valueString
            if "valueString" in ext:
                return ext["valueString"]
            # variant 2: sub-extensions with coding
            for sub in ext.get("extension", []) or []:
                if sub.get("url") == "text" and "valueString" in sub:
                    return sub["valueString"]
                if "valueCoding" in sub:
                    value_coding = sub["valueCoding"]
                    if isinstance(value_coding, dict):
                        return value_coding.get("display") or value_coding.get("code")
            # try valueCoding directly
            value_coding = ext.get("valueCoding")
            if isinstance(value_coding, dict):
                return value_coding.get("display") or value_coding.get("code")
    return None

def extract_patient_fields(p: Dict[str, Any]) -> Dict[str, Any]:
    identifier = patient_identifier(p) or p.get("id")
    given, family, text_name = human_name(p)
    birth_date = p.get("birthDate")
    gender = p.get("gender")
    phone = telecom_value(p, "phone")
    email = telecom_value(p, "email")
    address_line, city, state, postal_code = address_fields(p)
    marital_status = get_marital_status(p)
    language = get_language(p)
    # Synthea US Core extensions (these URLs may vary by export)
    race = get_extensions_value(p, "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race")
    ethnicity = get_extensions_value(p, "http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity")
    deceased_date = p.get("deceasedDateTime")
    active = p.get("active", True)

    # managingOrganization is a Reference like "Organization/abc"
    managing_org_ref = (p.get("managingOrganization") or {}).get("reference")

    return {
        "identifier": identifier,
        "first_name": given,
        "last_name": family,
        "birth_date": birth_date,
        "gender": gender,
        "phone": phone,
        "email": email,
        "address_line": address_line,
        "city": city,
        "state": state,
        "postal_code": postal_code,
        "marital_status": marital_status,
        "language": language,
        "race": race,
        "ethnicity": ethnicity,
        "deceased_date": deceased_date,   # stored as ISO string in your model
        "active": active,
        "managing_organization_identifier": managing_org_ref,  # keep as reference string for now
    }

# ---------- core importer ----------

def import_patient_from_bundle(bundle_path: Path):
    """
    Reads a FHIR Bundle JSON file (Synthea) and inserts the Patient into patients_v2.
    If multiple Patient resources exist (rare in Synthea), imports the first one.
    """
    print(f"Reading: {bundle_path}")
    with open(bundle_path, "r", encoding="utf-8") as f:
        bundle = json.load(f)

    if bundle.get("resourceType") != "Bundle":
        print("Not a FHIR Bundle; skipping.")
        return

    # find the Patient resource
    patient_res = None
    for entry in bundle.get("entry", []):
        res = entry.get("resource", {})
        if res.get("resourceType") == "Patient":
            patient_res = res
            break

    if not patient_res:
        print("No Patient resource found; skipping.")
        return

    fields = extract_patient_fields(patient_res)

    # basic required fields guard
    if not fields["first_name"] or not fields["last_name"] or not fields["birth_date"]:
        print("Missing required name/birth_date; skipping insert:", fields)
        return

    # If birth_date is a string, let SQLAlchemy parse (or cast as date if needed)
    db = SessionLocal()
    try:
        patient = PatientV2(**fields)
        db.add(patient)
        db.commit()
        db.refresh(patient)
        print(f"Inserted PatientV2 id={patient.id}, identifier={patient.identifier}")
    except IntegrityError as ie:
        db.rollback()
        # likely duplicate identifier; you can turn this into an "upsert" if you want
        print(f"IntegrityError (maybe duplicate identifier): {ie}")
    except Exception as e:
        db.rollback()
        print("Failed to insert patient:", e)
    finally:
        db.close()

def import_folder(folder: Path):
    jsons = list(folder.glob("*.json"))
    if not jsons:
        print("No .json files found in", folder)
        return
    for jf in jsons:
        import_patient_from_bundle(jf)

if __name__ == "__main__":
    # change these paths as needed
    # Example: put one Synthea patient bundle into ./data/bundles/patient0.json
    bundle_or_folder = Path("./data/bundles")  # directory of JSON bundles
    if bundle_or_folder.is_dir():
        import_folder(bundle_or_folder)
    elif bundle_or_folder.is_file():
        import_patient_from_bundle(bundle_or_folder)
    else:
        print("Path not found:", bundle_or_folder.resolve())
