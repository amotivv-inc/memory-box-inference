"""API endpoints for persona management"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional, List
import uuid

from app.core.database import get_db
from app.core.security import get_current_organization
from app.models.personas import PersonaCreate, PersonaUpdate, PersonaResponse, PersonaList
from app.services.persona_service import PersonaService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/personas", tags=["personas"])


@router.post("", response_model=PersonaResponse)
async def create_persona(
    persona_data: PersonaCreate,
    db: AsyncSession = Depends(get_db),
    organization: Dict[str, Any] = Depends(get_current_organization)
):
    """
    Create a new persona.
    
    This endpoint creates a new persona (system prompt) for the organization.
    Personas can be used in requests to the OpenAI API to provide consistent
    system prompts.
    
    Parameters:
    - **name**: Name of the persona
    - **description**: Optional description of the persona
    - **content**: System prompt content
    - **user_id**: Optional user ID to restrict the persona to a specific user
    
    Returns:
    - Persona details including ID, name, content, etc.
    
    Raises:
    - 401: Unauthorized - If JWT authentication fails
    - 403: Forbidden - If organization doesn't have permission
    - 409: Conflict - If a persona with the same name already exists
    - 422: Validation Error - If request data is invalid
    """
    try:
        logger.info(f"Creating persona for organization {organization['organization_id']}")
        persona_service = PersonaService(db)
        
        try:
            persona = await persona_service.create_persona(
                organization_id=organization["organization_id"],
                name=persona_data.name,
                content=persona_data.content,
                description=persona_data.description,
                user_id=persona_data.user_id
            )
        except Exception as e:
            if "duplicate key value violates unique constraint" in str(e):
                raise HTTPException(
                    status_code=409,
                    detail=f"A persona with the name '{persona_data.name}' already exists"
                )
            raise
        
        # Convert internal user ID to external user ID
        external_user_id = None
        if persona.user_id:
            external_user_id = await persona_service.get_external_user_id(persona.user_id)
        
        return PersonaResponse(
            id=str(persona.id),
            organization_id=str(persona.organization_id),
            user_id=external_user_id,
            name=persona.name,
            description=persona.description,
            content=persona.content,
            is_active=persona.is_active,
            created_at=persona.created_at,
            updated_at=persona.updated_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating persona: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating persona: {str(e)}"
        )


@router.get("", response_model=PersonaList)
async def list_personas(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    include_inactive: bool = Query(False, description="Include inactive personas"),
    db: AsyncSession = Depends(get_db),
    organization: Dict[str, Any] = Depends(get_current_organization)
):
    """
    List personas for the organization.
    
    This endpoint returns a list of personas (system prompts) for the organization.
    
    Parameters:
    - **user_id**: Optional filter by user ID
    - **include_inactive**: Whether to include inactive personas (default: false)
    
    Returns:
    - List of personas with their details
    
    Raises:
    - 401: Unauthorized - If JWT authentication fails
    - 403: Forbidden - If organization doesn't have permission
    """
    try:
        logger.info(f"Listing personas for organization {organization['organization_id']}")
        persona_service = PersonaService(db)
        
        personas = await persona_service.list_personas(
            organization_id=organization["organization_id"],
            external_user_id=user_id,
            include_inactive=include_inactive
        )
        
        # Convert internal user IDs to external user IDs
        persona_responses = []
        for persona in personas:
            external_user_id = None
            if persona.user_id:
                external_user_id = await persona_service.get_external_user_id(persona.user_id)
            
            persona_responses.append(PersonaResponse(
                id=str(persona.id),
                organization_id=str(persona.organization_id),
                user_id=external_user_id,
                name=persona.name,
                description=persona.description,
                content=persona.content,
                is_active=persona.is_active,
                created_at=persona.created_at,
                updated_at=persona.updated_at
            ))
        
        return PersonaList(personas=persona_responses)
    
    except Exception as e:
        logger.error(f"Error listing personas: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing personas: {str(e)}"
        )


@router.get("/{persona_id}", response_model=PersonaResponse)
async def get_persona(
    persona_id: str,
    db: AsyncSession = Depends(get_db),
    organization: Dict[str, Any] = Depends(get_current_organization)
):
    """
    Get a persona by ID.
    
    This endpoint returns the details of a specific persona.
    
    Parameters:
    - **persona_id**: ID of the persona to retrieve
    
    Returns:
    - Persona details including ID, name, content, etc.
    
    Raises:
    - 401: Unauthorized - If JWT authentication fails
    - 403: Forbidden - If organization doesn't have permission
    - 404: Not Found - If the persona doesn't exist
    """
    try:
        logger.info(f"Getting persona {persona_id} for organization {organization['organization_id']}")
        persona_service = PersonaService(db)
        
        try:
            persona_uuid = uuid.UUID(persona_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid persona ID format"
            )
        
        persona = await persona_service.get_persona(
            organization_id=organization["organization_id"],
            persona_id=persona_id
        )
        
        if not persona:
            raise HTTPException(
                status_code=404,
                detail=f"Persona with ID {persona_id} not found"
            )
        
        # Convert internal user ID to external user ID
        external_user_id = None
        if persona.user_id:
            external_user_id = await persona_service.get_external_user_id(persona.user_id)
        
        return PersonaResponse(
            id=str(persona.id),
            organization_id=str(persona.organization_id),
            user_id=external_user_id,
            name=persona.name,
            description=persona.description,
            content=persona.content,
            is_active=persona.is_active,
            created_at=persona.created_at,
            updated_at=persona.updated_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting persona: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting persona: {str(e)}"
        )


@router.put("/{persona_id}", response_model=PersonaResponse)
async def update_persona(
    persona_id: str,
    persona_data: PersonaUpdate,
    db: AsyncSession = Depends(get_db),
    organization: Dict[str, Any] = Depends(get_current_organization)
):
    """
    Update a persona.
    
    This endpoint updates the details of a specific persona.
    
    Parameters:
    - **persona_id**: ID of the persona to update
    - **name**: Optional new name for the persona
    - **description**: Optional new description
    - **content**: Optional new system prompt content
    - **user_id**: Optional user ID to restrict the persona to
    - **is_active**: Optional flag to activate/deactivate the persona
    
    Returns:
    - Updated persona details
    
    Raises:
    - 401: Unauthorized - If JWT authentication fails
    - 403: Forbidden - If organization doesn't have permission
    - 404: Not Found - If the persona doesn't exist
    - 409: Conflict - If updating the name would create a duplicate
    - 422: Validation Error - If request data is invalid
    """
    try:
        logger.info(f"Updating persona {persona_id} for organization {organization['organization_id']}")
        persona_service = PersonaService(db)
        
        try:
            persona_uuid = uuid.UUID(persona_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid persona ID format"
            )
        
        try:
            persona = await persona_service.update_persona(
                organization_id=organization["organization_id"],
                persona_id=persona_id,
                data=persona_data.model_dump(exclude_unset=True)
            )
        except Exception as e:
            if "duplicate key value violates unique constraint" in str(e):
                raise HTTPException(
                    status_code=409,
                    detail=f"A persona with the name '{persona_data.name}' already exists"
                )
            raise
        
        if not persona:
            raise HTTPException(
                status_code=404,
                detail=f"Persona with ID {persona_id} not found"
            )
        
        # Convert internal user ID to external user ID
        external_user_id = None
        if persona.user_id:
            external_user_id = await persona_service.get_external_user_id(persona.user_id)
        
        return PersonaResponse(
            id=str(persona.id),
            organization_id=str(persona.organization_id),
            user_id=external_user_id,
            name=persona.name,
            description=persona.description,
            content=persona.content,
            is_active=persona.is_active,
            created_at=persona.created_at,
            updated_at=persona.updated_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating persona: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error updating persona: {str(e)}"
        )


@router.delete("/{persona_id}")
async def delete_persona(
    persona_id: str,
    db: AsyncSession = Depends(get_db),
    organization: Dict[str, Any] = Depends(get_current_organization)
):
    """
    Delete a persona.
    
    This endpoint deletes a specific persona.
    
    Parameters:
    - **persona_id**: ID of the persona to delete
    
    Returns:
    - Success message
    
    Raises:
    - 401: Unauthorized - If JWT authentication fails
    - 403: Forbidden - If organization doesn't have permission
    - 404: Not Found - If the persona doesn't exist
    """
    try:
        logger.info(f"Deleting persona {persona_id} for organization {organization['organization_id']}")
        persona_service = PersonaService(db)
        
        try:
            persona_uuid = uuid.UUID(persona_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid persona ID format"
            )
        
        success = await persona_service.delete_persona(
            organization_id=organization["organization_id"],
            persona_id=persona_id
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Persona with ID {persona_id} not found"
            )
        
        return {"success": True, "message": f"Persona {persona_id} deleted"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting persona: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting persona: {str(e)}"
        )
