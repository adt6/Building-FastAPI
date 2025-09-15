"""
Patient-related tools for the clinical AI agent.
These tools allow the agent to interact with patient data from the FHIR API.
"""
from langchain.tools import tool
from typing import Optional, List, Dict, Any
from .base_tools import api_client, format_patient_summary, format_patient_summary_html, format_list_summary

@tool
def get_patient_info(patient_identifier: str) -> str:
    """
    Get detailed information about a specific patient by their ID or identifier.
    
    Args:
        patient_identifier: The patient ID (integer) or identifier (UUID/MRN)
        
    Returns:
        Formatted patient information including name, birth date, gender, and ID
    """
    try:
        # Clean the input - remove any parameter formatting
        clean_identifier = patient_identifier.strip()
        if "=" in clean_identifier:
            clean_identifier = clean_identifier.split("=")[1].strip()
        
        # Try to get by ID first (if it's a number)
        if clean_identifier.isdigit():
            response = api_client.get(f"/patients/{clean_identifier}")
        else:
            # Search by identifier (UUID/MRN)
            response = api_client.get("/patients", params={"identifier": clean_identifier})
            if isinstance(response, list) and len(response) > 0:
                response = response[0]  # Take the first match
            elif isinstance(response, list) and len(response) == 0:
                return f"No patient found with identifier: {clean_identifier}"
        
        if "error" in response:
            return f"Error retrieving patient {clean_identifier}: {response['error']}"
        
        return format_patient_summary(response)
    
    except Exception as e:
        return f"Unexpected error retrieving patient {patient_identifier}: {str(e)}"

@tool
def search_patients(
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    birth_date: Optional[str] = None,
    gender: Optional[str] = None,
    limit: int = 20
) -> str:
    """
    Search for patients based on various criteria.
    
    Args:
        first_name: Patient's first name (partial match) - pass only the name value, e.g. "Maxwell782"
        last_name: Patient's last name (partial match) - pass only the name value, e.g. "Koepp521"
        birth_date: Patient's birth date (YYYY-MM-DD format)
        gender: Patient's gender (male, female, other, unknown)
        limit: Maximum number of results to return (default: 20, max: 100)
        
    Returns:
        List of patients matching the search criteria
        
    Example usage:
        search_patients(first_name="Maxwell782")
        search_patients(last_name="Koepp521")
    """
    try:
        # Build query parameters
        params = {}
        if first_name:
            params['first_name'] = first_name
        if last_name:
            params['last_name'] = last_name
        if birth_date:
            params['birth_date'] = birth_date
        if gender:
            params['gender'] = gender
        if limit:
            params['limit'] = min(limit, 100)  # Cap at 100
        
        response = api_client.get("/patients", params=params)
        
        if "error" in response:
            return f"Error searching patients: {response['error']}"
        
        patients = response if isinstance(response, list) else []
        
        if not patients:
            return "No patients found matching the search criteria."
        
        # Format the results
        result = f"Found {len(patients)} patient(s):\n\n"
        for i, patient in enumerate(patients[:10], 1):  # Show max 10
            result += f"{i}. {format_patient_summary(patient)}\n\n"
        
        if len(patients) > 10:
            result += f"... and {len(patients) - 10} more patients."
        
        return result
    
    except Exception as e:
        return f"Unexpected error searching patients: {str(e)}"

@tool
def get_patient_conditions(patient_identifier: str) -> str:
    """
    Get all medical conditions for a specific patient.
    
    Args:
        patient_identifier: The patient ID (integer) or identifier (UUID/MRN)
        
    Returns:
        List of conditions associated with the patient
    """
    try:
        # Clean the input - remove any parameter formatting
        clean_identifier = patient_identifier.strip()
        if "=" in clean_identifier:
            clean_identifier = clean_identifier.split("=")[1].strip()
        
        # Remove quotes if present
        if clean_identifier.startswith('"') and clean_identifier.endswith('"'):
            clean_identifier = clean_identifier[1:-1]
        elif clean_identifier.startswith("'") and clean_identifier.endswith("'"):
            clean_identifier = clean_identifier[1:-1]
        
        # First, get the patient to find their integer ID
        patient_info = get_patient_info(clean_identifier)
        if "Error" in patient_info:
            return f"Cannot find patient with identifier: {clean_identifier}"
        
        # Extract patient ID from the response (we need to get the actual patient data)
        if clean_identifier.isdigit():
            patient_id = int(clean_identifier)
        else:
            # Search for patient by identifier to get the integer ID
            response = api_client.get("/patients", params={"identifier": clean_identifier})
            if isinstance(response, list) and len(response) > 0:
                patient_id = response[0].get('id')
            else:
                return f"No patient found with identifier: {clean_identifier}"
        
        response = api_client.get(f"/conditions", params={"patient_id": patient_id})
        
        if "error" in response:
            return f"Error retrieving conditions for patient {patient_identifier}: {response['error']}"
        
        conditions = response if isinstance(response, list) else []
        
        if not conditions:
            return f"No conditions found for patient {patient_identifier}."
        
        # Format the results
        result = f"Patient {patient_identifier} has {len(conditions)} condition(s):\n\n"
        for i, condition in enumerate(conditions, 1):
            result += f"{i}. {format_condition_summary(condition)}\n\n"
        
        return result
    
    except Exception as e:
        return f"Unexpected error retrieving conditions for patient {patient_identifier}: {str(e)}"

@tool
def get_patient_encounters(patient_identifier: str) -> str:
    """
    Get all medical encounters for a specific patient.
    
    Args:
        patient_identifier: The patient ID (integer) or identifier (UUID/MRN)
        
    Returns:
        List of encounters associated with the patient
    """
    try:
        # Clean the input - remove any parameter formatting
        clean_identifier = patient_identifier.strip()
        if "=" in clean_identifier:
            clean_identifier = clean_identifier.split("=")[1].strip()
        
        # Get the patient's integer ID
        if clean_identifier.isdigit():
            patient_id = int(clean_identifier)
        else:
            # Search for patient by identifier to get the integer ID
            response = api_client.get("/patients", params={"identifier": clean_identifier})
            if isinstance(response, list) and len(response) > 0:
                patient_id = response[0].get('id')
            else:
                return f"No patient found with identifier: {clean_identifier}"
        
        response = api_client.get(f"/encounters", params={"patient_id": patient_id})
        
        if "error" in response:
            return f"Error retrieving encounters for patient {patient_identifier}: {response['error']}"
        
        encounters = response if isinstance(response, list) else []
        
        if not encounters:
            return f"No encounters found for patient {patient_identifier}."
        
        # Format the results
        result = f"Patient {patient_identifier} has {len(encounters)} encounter(s):\n\n"
        for i, encounter in enumerate(encounters, 1):
            result += f"{i}. {format_encounter_summary(encounter)}\n\n"
        
        return result
    
    except Exception as e:
        return f"Unexpected error retrieving encounters for patient {patient_identifier}: {str(e)}"

@tool
def get_patient_summary(patient_identifier: str) -> str:
    """
    Get a comprehensive summary of a patient including their basic info, conditions, and encounters.
    
    Args:
        patient_identifier: The patient ID (integer) or identifier (UUID/MRN)
        
    Returns:
        Complete patient summary with all related information
    """
    try:
        # Clean the input - remove any parameter formatting
        clean_identifier = patient_identifier.strip()
        if "=" in clean_identifier:
            clean_identifier = clean_identifier.split("=")[1].strip()
        
        # Get patient basic info
        patient_info = get_patient_info(clean_identifier)
        if "Error" in patient_info:
            return patient_info
        
        # Get conditions
        conditions_info = get_patient_conditions(clean_identifier)
        
        # Get encounters
        encounters_info = get_patient_encounters(clean_identifier)
        
        # Combine all information
        result = f"=== PATIENT SUMMARY ===\n\n"
        result += f"BASIC INFORMATION:\n{patient_info}\n\n"
        result += f"MEDICAL CONDITIONS:\n{conditions_info}\n\n"
        result += f"MEDICAL ENCOUNTERS:\n{encounters_info}\n"
        
        return result
    
    except Exception as e:
        return f"Unexpected error creating patient summary for {patient_identifier}: {str(e)}"


# Helper function for condition formatting (imported from base_tools)
def format_condition_summary(condition_data: Dict[str, Any]) -> str:
    """Format condition data into a human-readable summary."""
    if "error" in condition_data:
        return f"Error retrieving condition: {condition_data['error']}"
    
    code = condition_data.get('code', 'Unknown')
    display = condition_data.get('display', 'Unknown')
    status = condition_data.get('status', 'Unknown')
    onset_date = condition_data.get('onset_date', 'Unknown')
    
    return f"Condition: {display} ({code})\nStatus: {status}\nOnset Date: {onset_date}"

# Helper function for encounter formatting (imported from base_tools)
def format_encounter_summary(encounter_data: Dict[str, Any]) -> str:
    """Format encounter data into a human-readable summary."""
    if "error" in encounter_data:
        return f"Error retrieving encounter: {encounter_data['error']}"
    
    status = encounter_data.get('status', 'Unknown')
    start_time = encounter_data.get('start_time', 'Unknown')
    class_code = encounter_data.get('class_code', 'Unknown')
    
    return f"Encounter: {class_code}\nStatus: {status}\nStart Time: {start_time}"
