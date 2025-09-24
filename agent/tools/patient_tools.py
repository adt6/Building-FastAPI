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
            # Search by identifier (UUID/MRN) - should be unique
            response = api_client.get("/patients", params={"identifier": clean_identifier})
            if isinstance(response, list):
                if len(response) == 0:
                    return f"No patient found with identifier: {clean_identifier}"
                elif len(response) == 1:
                    response = response[0]  # Take the single result
                else:
                    # This should never happen for UUIDs, but handle gracefully
                    return f"Multiple patients found with identifier: {clean_identifier}. Please use a more specific identifier."
        
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
        # Clean input parameters - remove any parameter formatting
        clean_first_name = first_name.strip() if first_name else None
        clean_last_name = last_name.strip() if last_name else None
        clean_birth_date = birth_date.strip() if birth_date else None
        clean_gender = gender.strip() if gender else None
        
        # Handle complex parameter formatting issues
        # Case: first_name="Robert854", last_name="Botsford977" (all in one string)
        if clean_first_name and "," in clean_first_name and "last_name=" in clean_first_name:
            # This is a combined string like: first_name="Robert854", last_name="Botsford977"
            parts = clean_first_name.split(",")
            for part in parts:
                part = part.strip()
                if "first_name=" in part:
                    clean_first_name = part.split("first_name=")[1].strip().strip('"')
                elif "last_name=" in part:
                    clean_last_name = part.split("last_name=")[1].strip().strip('"')
        
        # Case: Single parameter with quotes (e.g., first_name="Maxwell782")
        elif clean_first_name and "=" in clean_first_name and "first_name=" in clean_first_name:
            clean_first_name = clean_first_name.split("first_name=")[1].strip().strip('"')
        
        # Case: Single parameter with quotes (e.g., last_name="Smith123")
        elif clean_last_name and "=" in clean_last_name and "last_name=" in clean_last_name:
            clean_last_name = clean_last_name.split("last_name=")[1].strip().strip('"')
        
        # Build query parameters
        params = {}
        if clean_first_name:
            params['first_name'] = clean_first_name
        if clean_last_name:
            params['last_name'] = clean_last_name
        if clean_birth_date:
            params['birth_date'] = clean_birth_date
        if clean_gender:
            params['gender'] = clean_gender
        if limit:
            params['limit'] = min(limit, 100)  # Cap at 100
        
        # Debug logging (can be removed in production)
        # print(f"DEBUG: Original inputs - first_name='{first_name}', last_name='{last_name}'")
        # print(f"DEBUG: Cleaned inputs - first_name='{clean_first_name}', last_name='{clean_last_name}'")
        # print(f"DEBUG: Final params: {params}")
        
        response = api_client.get("/patients", params=params)
        
        if "error" in response:
            return f"Error searching patients: {response['error']}"
        
        patients = response if isinstance(response, list) else []
        
        if not patients:
            return "No patients found matching the search criteria."
        
        # Format the results
        result = f"Found {len(patients)} patient(s):\n\n"
        for i, patient in enumerate(patients[:10], 1):  # Show max 10
            result += f"{i}. **{patient.get('name', 'Unknown')}** (ID: {patient.get('id', 'Unknown')})\n"
            result += f"   Birth Date: {patient.get('birth_date', 'Unknown')}\n"
            result += f"   Gender: {patient.get('gender', 'Unknown')}\n"
            result += f"   Status: {patient.get('status', 'Unknown')}\n\n"
        
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

@tool
def get_patient_observations(patient_identifier: str) -> str:
    """
    Get all medical observations (lab results, vital signs, etc.) for a specific patient.
    
    Args:
        patient_identifier (str): The patient ID or medical record number
        
    Returns:
        str: Formatted list of patient observations
    """
    try:
        # Clean the patient identifier
        clean_identifier = patient_identifier.strip()
        if "=" in clean_identifier:
            clean_identifier = clean_identifier.split("=")[1].strip()
        
        # Remove quotes if present
        if clean_identifier.startswith('"') and clean_identifier.endswith('"'):
            clean_identifier = clean_identifier[1:-1]
        elif clean_identifier.startswith("'") and clean_identifier.endswith("'"):
            clean_identifier = clean_identifier[1:-1]
        
        # Get patient observations from API
        observations_data = api_client.get(f"/observations?patient_id={clean_identifier}")
        
        if not observations_data:
            return f"No observations found for patient {clean_identifier}"
        
        # Format observations
        formatted_observations = []
        for i, observation in enumerate(observations_data, 1):
            formatted_obs = format_observation_summary(observation)
            formatted_observations.append(f"{i}. {formatted_obs}")
        
        return f"Patient {clean_identifier} has {len(observations_data)} observation(s):\n" + "\n".join(formatted_observations)
        
    except Exception as e:
        return f"Error retrieving observations for patient {patient_identifier}: {str(e)}"

# Helper function for observation formatting
def format_observation_summary(observation_data: Dict[str, Any]) -> str:
    """Format observation data into a human-readable summary."""
    if "error" in observation_data:
        return f"Error retrieving observation: {observation_data['error']}"
    
    observation_type = observation_data.get('observation_type', 'Unknown')
    value = observation_data.get('value', 'Unknown')
    unit = observation_data.get('unit', '')
    date = observation_data.get('date', 'Unknown')
    status = observation_data.get('status', 'Unknown')
    
    value_str = f"{value} {unit}".strip() if unit else str(value)
    
    return f"Observation: {observation_type}\nValue: {value_str}\nDate: {date}\nStatus: {status}"
