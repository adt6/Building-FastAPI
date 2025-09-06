from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app_v2.database import get_db
from app_v2.models.organization import OrganizationV2
from app_v2.schemas.organization import OrganizationCreate, OrganizationRead, OrganizationUpdate

router = APIRouter(prefix="/organizations", tags=["organizations v2"])


@router.get("/", response_model=List[OrganizationRead])
def list_organizations(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    name: Optional[str] = None,
    type_code: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    identifier: Optional[str] = None,
):
    """
    List organizations with filtering options.
    
    - **name**: Filter by organization name (partial match)
    - **type_code**: Filter by organization type (hospital, clinic, etc.)
    - **city**: Filter by city
    - **state**: Filter by state
    - **identifier**: Filter by organization identifier
    """
    query = db.query(OrganizationV2)
    
    if name is not None:
        query = query.filter(OrganizationV2.name.ilike(f"%{name}%"))
    if type_code is not None:
        query = query.filter(OrganizationV2.type_code == type_code)
    if city is not None:
        query = query.filter(OrganizationV2.city.ilike(f"%{city}%"))
    if state is not None:
        query = query.filter(OrganizationV2.state == state)
    if identifier is not None:
        query = query.filter(OrganizationV2.identifier == identifier)

    organizations = query.order_by(OrganizationV2.name.asc()).limit(limit).offset(offset).all()
    return organizations


@router.get("/{organization_id}", response_model=OrganizationRead)
def get_organization(organization_id: int, db: Session = Depends(get_db)):
    """Get a specific organization by ID."""
    organization = db.query(OrganizationV2).get(organization_id)
    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return organization


@router.post("/", response_model=OrganizationRead, status_code=status.HTTP_201_CREATED)
def create_organization(payload: OrganizationCreate, db: Session = Depends(get_db)):
    """Create a new organization."""
    new_organization = OrganizationV2(**payload.model_dump(exclude_unset=True))
    db.add(new_organization)
    db.commit()
    db.refresh(new_organization)
    return new_organization


@router.put("/{organization_id}", response_model=OrganizationRead)
def update_organization(organization_id: int, payload: OrganizationUpdate, db: Session = Depends(get_db)):
    """Update an existing organization."""
    organization = db.query(OrganizationV2).get(organization_id)
    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(organization, key, value)

    db.commit()
    db.refresh(organization)
    return organization


@router.delete("/{organization_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_organization(organization_id: int, db: Session = Depends(get_db)):
    """Delete an organization."""
    organization = db.query(OrganizationV2).get(organization_id)
    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    db.delete(organization)
    db.commit()
    return None
