"""
Encounter-related tools for the clinical AI agent.
These tools allow the agent to interact with medical encounter data from the FHIR API.
"""
from langchain.tools import tool
from typing import Optional, List, Dict, Any
from datetime import datetime
from .base_tools import api_client, format_encounter_summary, format_list_summary

@tool
def get_encounter_details(encounter_id: int) -> str:
    """
    Get detailed information about a specific medical encounter by its ID.
    
    Args:
        encounter_id: The unique identifier of the encounter
        
    Returns:
        Formatted encounter information including status, start time, class code, and related entities
    """
    try:
        response = api_client.get(f"/encounters/{encounter_id}")
        
        if "error" in response:
            return f"Error retrieving encounter {encounter_id}: {response['error']}"
        
        # Format detailed encounter information
        result = f"=== ENCOUNTER DETAILS ===\n"
        result += f"ID: {response.get('id', 'Unknown')}\n"
        result += f"Status: {response.get('status', 'Unknown')}\n"
        result += f"Class Code: {response.get('class_code', 'Unknown')}\n"
        result += f"Start Time: {response.get('start_time', 'Unknown')}\n"
        result += f"End Time: {response.get('end_time', 'Not specified')}\n"
        result += f"Patient ID: {response.get('patient_id', 'Unknown')}\n"
        result += f"Practitioner ID: {response.get('practitioner_id', 'Not specified')}\n"
        result += f"Organization ID: {response.get('organization_id', 'Not specified')}\n"
        
        return result
    
    except Exception as e:
        return f"Unexpected error retrieving encounter {encounter_id}: {str(e)}"

@tool
def search_encounters(
    patient_id: Optional[int] = None,
    practitioner_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    status: Optional[str] = None,
    start_from: Optional[str] = None,
    start_to: Optional[str] = None,
    class_code: Optional[str] = None,
    limit: int = 20
) -> str:
    """
    Search for medical encounters based on various criteria.
    
    Args:
        patient_id: Filter by patient ID
        practitioner_id: Filter by practitioner ID
        organization_id: Filter by organization ID
        status: Filter by encounter status (planned, arrived, triaged, in-progress, onleave, finished, cancelled, entered-in-error, unknown)
        start_from: Filter encounters starting from this date (YYYY-MM-DD format)
        start_to: Filter encounters starting before this date (YYYY-MM-DD format)
        class_code: Filter by encounter class code
        limit: Maximum number of results to return (default: 20, max: 100)
        
    Returns:
        List of encounters matching the search criteria
    """
    try:
        # Build query parameters
        params = {}
        if patient_id:
            params['patient_id'] = patient_id
        if practitioner_id:
            params['practitioner_id'] = practitioner_id
        if organization_id:
            params['organization_id'] = organization_id
        if status:
            params['status'] = status
        if start_from:
            params['start_from'] = start_from
        if start_to:
            params['start_to'] = start_to
        if class_code:
            params['class_code'] = class_code
        if limit:
            params['limit'] = min(limit, 100)  # Cap at 100
        
        response = api_client.get("/encounters", params=params)
        
        if "error" in response:
            return f"Error searching encounters: {response['error']}"
        
        encounters = response if isinstance(response, list) else []
        
        if not encounters:
            return "No encounters found matching the search criteria."
        
        # Format the results
        result = f"Found {len(encounters)} encounter(s):\n\n"
        for i, encounter in enumerate(encounters[:10], 1):  # Show max 10
            result += f"{i}. {format_encounter_summary(encounter)}\n\n"
        
        if len(encounters) > 10:
            result += f"... and {len(encounters) - 10} more encounters."
        
        return result
    
    except Exception as e:
        return f"Unexpected error searching encounters: {str(e)}"

@tool
def get_encounters_by_date_range(start_date: str, end_date: str) -> str:
    """
    Get all encounters within a specific date range.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        List of encounters within the specified date range
    """
    try:
        response = api_client.get("/encounters", params={
            "start_from": start_date,
            "start_to": end_date,
            "limit": 100
        })
        
        if "error" in response:
            return f"Error retrieving encounters for date range {start_date} to {end_date}: {response['error']}"
        
        encounters = response if isinstance(response, list) else []
        
        if not encounters:
            return f"No encounters found between {start_date} and {end_date}."
        
        # Format the results
        result = f"Found {len(encounters)} encounter(s) between {start_date} and {end_date}:\n\n"
        for i, encounter in enumerate(encounters[:10], 1):  # Show max 10
            result += f"{i}. {format_encounter_summary(encounter)}\n\n"
        
        if len(encounters) > 10:
            result += f"... and {len(encounters) - 10} more encounters."
        
        return result
    
    except Exception as e:
        return f"Unexpected error retrieving encounters for date range: {str(e)}"

@tool
def get_encounters_by_practitioner(practitioner_id: int) -> str:
    """
    Get all encounters conducted by a specific practitioner.
    
    Args:
        practitioner_id: The unique identifier of the practitioner
        
    Returns:
        List of encounters conducted by the specified practitioner
    """
    try:
        response = api_client.get("/encounters", params={
            "practitioner_id": practitioner_id,
            "limit": 100
        })
        
        if "error" in response:
            return f"Error retrieving encounters for practitioner {practitioner_id}: {response['error']}"
        
        encounters = response if isinstance(response, list) else []
        
        if not encounters:
            return f"No encounters found for practitioner {practitioner_id}."
        
        # Format the results
        result = f"Practitioner {practitioner_id} has conducted {len(encounters)} encounter(s):\n\n"
        for i, encounter in enumerate(encounters[:10], 1):  # Show max 10
            result += f"{i}. {format_encounter_summary(encounter)}\n\n"
        
        if len(encounters) > 10:
            result += f"... and {len(encounters) - 10} more encounters."
        
        return result
    
    except Exception as e:
        return f"Unexpected error retrieving encounters for practitioner {practitioner_id}: {str(e)}"

@tool
def get_encounters_by_organization(organization_id: int) -> str:
    """
    Get all encounters hosted by a specific organization.
    
    Args:
        organization_id: The unique identifier of the organization
        
    Returns:
        List of encounters hosted by the specified organization
    """
    try:
        response = api_client.get("/encounters", params={
            "organization_id": organization_id,
            "limit": 100
        })
        
        if "error" in response:
            return f"Error retrieving encounters for organization {organization_id}: {response['error']}"
        
        encounters = response if isinstance(response, list) else []
        
        if not encounters:
            return f"No encounters found for organization {organization_id}."
        
        # Format the results
        result = f"Organization {organization_id} has hosted {len(encounters)} encounter(s):\n\n"
        for i, encounter in enumerate(encounters[:10], 1):  # Show max 10
            result += f"{i}. {format_encounter_summary(encounter)}\n\n"
        
        if len(encounters) > 10:
            result += f"... and {len(encounters) - 10} more encounters."
        
        return result
    
    except Exception as e:
        return f"Unexpected error retrieving encounters for organization {organization_id}: {str(e)}"

@tool
def get_encounter_statistics() -> str:
    """
    Get basic statistics about encounters in the system.
    
    Returns:
        Summary statistics about encounters including total count and status breakdown
    """
    try:
        # Get all encounters to calculate statistics
        response = api_client.get("/encounters", params={"limit": 1000})
        
        if "error" in response:
            return f"Error retrieving encounter statistics: {response['error']}"
        
        encounters = response if isinstance(response, list) else []
        
        if not encounters:
            return "No encounters found in the system."
        
        # Calculate statistics
        total_encounters = len(encounters)
        status_counts = {}
        class_code_counts = {}
        
        for encounter in encounters:
            status = encounter.get('status', 'unknown')
            class_code = encounter.get('class_code', 'unknown')
            
            status_counts[status] = status_counts.get(status, 0) + 1
            class_code_counts[class_code] = class_code_counts.get(class_code, 0) + 1
        
        # Format statistics
        result = f"=== ENCOUNTER STATISTICS ===\n"
        result += f"Total Encounters: {total_encounters}\n\n"
        
        result += "Status Breakdown:\n"
        for status, count in sorted(status_counts.items()):
            result += f"  {status}: {count}\n"
        
        result += "\nClass Code Breakdown:\n"
        for class_code, count in sorted(class_code_counts.items()):
            result += f"  {class_code}: {count}\n"
        
        return result
    
    except Exception as e:
        return f"Unexpected error retrieving encounter statistics: {str(e)}"
