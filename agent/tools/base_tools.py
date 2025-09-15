"""
Base tools and HTTP client for API interactions.
This provides the foundation for all API calling tools.
"""
import requests
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FHIRAPIClient:
    """
    HTTP client for interacting with the FHIR API.
    Handles authentication, error handling, and response formatting.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000/api/v2"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make a GET request to the API.
        
        Args:
            endpoint: API endpoint (e.g., '/patients', '/conditions')
            params: Query parameters
            
        Returns:
            API response as dictionary
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.get(url, params=params, allow_redirects=True)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"GET request failed for {url}: {e}")
            return {"error": str(e), "status_code": getattr(e.response, 'status_code', None)}
    
    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a POST request to the API.
        
        Args:
            endpoint: API endpoint
            data: Request body data
            
        Returns:
            API response as dictionary
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"POST request failed for {url}: {e}")
            return {"error": str(e), "status_code": getattr(e.response, 'status_code', None)}
    
    def put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a PUT request to the API.
        
        Args:
            endpoint: API endpoint
            data: Request body data
            
        Returns:
            API response as dictionary
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.put(url, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"PUT request failed for {url}: {e}")
            return {"error": str(e), "status_code": getattr(e.response, 'status_code', None)}
    
    def delete(self, endpoint: str) -> Dict[str, Any]:
        """
        Make a DELETE request to the API.
        
        Args:
            endpoint: API endpoint
            
        Returns:
            API response as dictionary
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.delete(url)
            response.raise_for_status()
            return {"success": True, "status_code": response.status_code}
        except requests.exceptions.RequestException as e:
            logger.error(f"DELETE request failed for {url}: {e}")
            return {"error": str(e), "status_code": getattr(e.response, 'status_code', None)}

# Global API client instance
api_client = FHIRAPIClient()

def format_patient_summary(patient_data: Dict[str, Any]) -> str:
    """
    Format patient data into a human-readable summary.
    
    Args:
        patient_data: Patient data from API
        
    Returns:
        Formatted patient summary
    """
    if "error" in patient_data:
        return f"Error retrieving patient: {patient_data['error']}"
    
    # Basic Information
    name = f"{patient_data.get('first_name', 'Unknown')} {patient_data.get('last_name', 'Unknown')}"
    birth_date = patient_data.get('birth_date', 'Unknown')
    gender = patient_data.get('gender', 'Unknown')
    patient_id = patient_data.get('id', 'Unknown')
    identifier = patient_data.get('identifier', 'Not assigned')
    
    # Contact Information
    phone = patient_data.get('phone', 'Not provided')
    email = patient_data.get('email', 'Not provided')
    
    # Address Information
    address_line = patient_data.get('address_line', 'Not provided')
    city = patient_data.get('city', 'Not provided')
    state = patient_data.get('state', 'Not provided')
    postal_code = patient_data.get('postal_code', 'Not provided')
    
    # Demographics
    marital_status = patient_data.get('marital_status', 'Not specified')
    language = patient_data.get('language', 'Not specified')
    race = patient_data.get('race', 'Not specified')
    ethnicity = patient_data.get('ethnicity', 'Not specified')
    
    # Medical Information
    deceased_date = patient_data.get('deceased_date', 'N/A')
    active = patient_data.get('active', True)
    managing_org = patient_data.get('managing_organization_identifier', 'Not assigned')
    
    # Format the complete summary with better spacing
    result = f"**PATIENT INFORMATION**\n\n"
    result += f"**Name:** {name}\n"
    result += f"**ID:** {patient_id}\n"
    result += f"**Medical Record Number:** {identifier}\n"
    result += f"**Birth Date:** {birth_date}\n"
    result += f"**Gender:** {gender}\n"
    result += f"**Status:** {'Active' if active else 'Inactive'}\n"
    
    if deceased_date != 'N/A':
        result += f"**Deceased Date:** {deceased_date}\n"
    
    result += f"\n**CONTACT INFORMATION**\n\n"
    result += f"**Phone:** {phone}\n"
    result += f"**Email:** {email}\n"
    
    result += f"\n**ADDRESS**\n\n"
    result += f"**Address:** {address_line}\n"
    result += f"**City:** {city}\n"
    result += f"**State:** {state}\n"
    result += f"**Postal Code:** {postal_code}\n"
    
    result += f"\n**DEMOGRAPHICS**\n\n"
    result += f"**Marital Status:** {marital_status}\n"
    result += f"**Language:** {language}\n"
    result += f"**Race:** {race}\n"
    result += f"**Ethnicity:** {ethnicity}\n"
    
    result += f"\n**ORGANIZATIONAL**\n\n"
    result += f"**Managing Organization:** {managing_org}\n"
    
    return result

def format_patient_summary_html(patient_data: Dict[str, Any]) -> str:
    """
    Format patient data into HTML for better display in Streamlit.
    
    Args:
        patient_data: Patient data from API
        
    Returns:
        HTML formatted patient summary
    """
    if "error" in patient_data:
        return f"<div style='color: red;'>Error retrieving patient: {patient_data['error']}</div>"
    
    # Basic Information
    name = f"{patient_data.get('first_name', 'Unknown')} {patient_data.get('last_name', 'Unknown')}"
    birth_date = patient_data.get('birth_date', 'Unknown')
    gender = patient_data.get('gender', 'Unknown')
    patient_id = patient_data.get('id', 'Unknown')
    identifier = patient_data.get('identifier', 'Not assigned')
    
    # Contact Information
    phone = patient_data.get('phone', 'Not provided')
    email = patient_data.get('email', 'Not provided')
    
    # Address Information
    address_line = patient_data.get('address_line', 'Not provided')
    city = patient_data.get('city', 'Not provided')
    state = patient_data.get('state', 'Not provided')
    postal_code = patient_data.get('postal_code', 'Not provided')
    
    # Demographics
    marital_status = patient_data.get('marital_status', 'Not specified')
    language = patient_data.get('language', 'Not specified')
    race = patient_data.get('race', 'Not specified')
    ethnicity = patient_data.get('ethnicity', 'Not specified')
    
    # Medical Information
    deceased_date = patient_data.get('deceased_date', 'N/A')
    active = patient_data.get('active', True)
    managing_org = patient_data.get('managing_organization_identifier', 'Not assigned')
    
    # Create HTML with better styling
    html = f"""
    <div style="background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 20px; margin: 10px 0; font-family: Arial, sans-serif;">
        <h3 style="color: #2c3e50; margin-top: 0; border-bottom: 2px solid #3498db; padding-bottom: 10px;">👤 Patient Information</h3>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
            <div>
                <h4 style="color: #34495e; margin-bottom: 10px;">Basic Details</h4>
                <p><strong>Name:</strong> {name}</p>
                <p><strong>Patient ID:</strong> {patient_id}</p>
                <p><strong>Medical Record #:</strong> {identifier}</p>
                <p><strong>Birth Date:</strong> {birth_date}</p>
                <p><strong>Gender:</strong> {gender}</p>
                <p><strong>Status:</strong> <span style="color: {'#27ae60' if active else '#e74c3c'}">{'Active' if active else 'Inactive'}</span></p>
                {f'<p><strong>Deceased Date:</strong> {deceased_date}</p>' if deceased_date != 'N/A' else ''}
            </div>
            
            <div>
                <h4 style="color: #34495e; margin-bottom: 10px;">Contact Information</h4>
                <p><strong>Phone:</strong> {phone}</p>
                <p><strong>Email:</strong> {email}</p>
                
                <h4 style="color: #34495e; margin: 15px 0 10px 0;">Address</h4>
                <p><strong>Address:</strong> {address_line}</p>
                <p><strong>City:</strong> {city}</p>
                <p><strong>State:</strong> {state}</p>
                <p><strong>Postal Code:</strong> {postal_code}</p>
            </div>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
            <div>
                <h4 style="color: #34495e; margin-bottom: 10px;">Demographics</h4>
                <p><strong>Marital Status:</strong> {marital_status}</p>
                <p><strong>Language:</strong> {language}</p>
                <p><strong>Race:</strong> {race}</p>
                <p><strong>Ethnicity:</strong> {ethnicity}</p>
            </div>
            
            <div>
                <h4 style="color: #34495e; margin-bottom: 10px;">Organizational</h4>
                <p><strong>Managing Organization:</strong> {managing_org}</p>
            </div>
        </div>
    </div>
    """
    
    return html

def format_condition_summary(condition_data: Dict[str, Any]) -> str:
    """
    Format condition data into a human-readable summary.
    
    Args:
        condition_data: Condition data from API
        
    Returns:
        Formatted condition summary
    """
    if "error" in condition_data:
        return f"Error retrieving condition: {condition_data['error']}"
    
    code = condition_data.get('code', 'Unknown')
    display = condition_data.get('display', 'Unknown')
    status = condition_data.get('status', 'Unknown')
    onset_date = condition_data.get('onset_date', 'Unknown')
    
    return f"Condition: {display} ({code})\nStatus: {status}\nOnset Date: {onset_date}"

def format_encounter_summary(encounter_data: Dict[str, Any]) -> str:
    """
    Format encounter data into a human-readable summary.
    
    Args:
        encounter_data: Encounter data from API
        
    Returns:
        Formatted encounter summary
    """
    if "error" in encounter_data:
        return f"Error retrieving encounter: {encounter_data['error']}"
    
    status = encounter_data.get('status', 'Unknown')
    start_time = encounter_data.get('start_time', 'Unknown')
    class_code = encounter_data.get('class_code', 'Unknown')
    
    return f"Encounter: {class_code}\nStatus: {status}\nStart Time: {start_time}"

def format_list_summary(items: List[Dict[str, Any]], item_type: str) -> str:
    """
    Format a list of items into a human-readable summary.
    
    Args:
        items: List of items from API
        item_type: Type of items (e.g., 'patients', 'conditions')
        
    Returns:
        Formatted list summary
    """
    if not items:
        return f"No {item_type} found."
    
    if len(items) == 1:
        return f"Found 1 {item_type[:-1]}: {items[0].get('id', 'Unknown')}"
    
    return f"Found {len(items)} {item_type}. IDs: {', '.join([str(item.get('id', 'Unknown')) for item in items[:5]])}{'...' if len(items) > 5 else ''}"
