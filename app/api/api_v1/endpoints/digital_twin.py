"""Digital twin simulation endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import structlog

from app.core.database import get_db
from app.models.digital_twin import DigitalTwin, SimulationRun, SimulationStatus
from app.services.digital_twin_service import DigitalTwinService
from app.schemas.digital_twin import (
    DigitalTwinCreate, 
    DigitalTwinResponse, 
    SimulationRunCreate, 
    SimulationRunResponse,
    SimulationTestRequest
)

router = APIRouter()
logger = structlog.get_logger()


@router.post("/", response_model=DigitalTwinResponse, status_code=status.HTTP_201_CREATED)
async def create_digital_twin(
    twin_data: DigitalTwinCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new digital twin simulation environment.
    
    - **twin_data**: Digital twin configuration and parameters
    """
    logger.info("Creating digital twin", simulation_type=twin_data.simulation_type)
    
    twin_service = DigitalTwinService(db)
    
    try:
        twin = twin_service.create_digital_twin(twin_data)
        logger.info("Digital twin created", twin_id=str(twin.id))
        return twin
        
    except Exception as e:
        logger.error("Digital twin creation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create digital twin"
        )


@router.get("/", response_model=List[DigitalTwinResponse])
async def list_digital_twins(
    skip: int = 0,
    limit: int = 100,
    simulation_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of digital twins.
    
    - **skip**: Number of twins to skip (for pagination)
    - **limit**: Maximum number of twins to return
    - **simulation_type**: Optional filter by simulation type
    """
    twin_service = DigitalTwinService(db)
    twins = twin_service.get_digital_twins(
        skip=skip, 
        limit=limit, 
        simulation_type=simulation_type
    )
    return twins


@router.get("/{twin_id}", response_model=DigitalTwinResponse)
async def get_digital_twin(
    twin_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific digital twin by ID.
    
    - **twin_id**: UUID of the digital twin to retrieve
    """
    twin_service = DigitalTwinService(db)
    twin = twin_service.get_digital_twin(twin_id)
    
    if not twin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Digital twin not found"
        )
    
    return twin


@router.post("/{twin_id}/test", response_model=SimulationRunResponse, status_code=status.HTTP_201_CREATED)
async def test_plc_code(
    twin_id: str,
    test_request: SimulationTestRequest,
    db: Session = Depends(get_db)
):
    """
    Test PLC code in the digital twin simulation.
    
    - **twin_id**: UUID of the digital twin to use for testing
    - **test_request**: Test configuration and PLC code reference
    """
    logger.info("Starting PLC code test", twin_id=twin_id, plc_code_id=test_request.plc_code_id)
    
    twin_service = DigitalTwinService(db)
    
    try:
        simulation_run = await twin_service.run_simulation(twin_id, test_request)
        logger.info("Simulation test completed", run_id=str(simulation_run.id))
        return simulation_run
        
    except Exception as e:
        logger.error("Simulation test failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run simulation test"
        )


@router.get("/{twin_id}/runs", response_model=List[SimulationRunResponse])
async def get_simulation_runs(
    twin_id: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get simulation runs for a specific digital twin.
    
    - **twin_id**: UUID of the digital twin
    - **skip**: Number of runs to skip (for pagination)
    - **limit**: Maximum number of runs to return
    """
    twin_service = DigitalTwinService(db)
    runs = twin_service.get_simulation_runs(twin_id, skip=skip, limit=limit)
    return runs


@router.get("/runs/{run_id}", response_model=SimulationRunResponse)
async def get_simulation_run(
    run_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific simulation run by ID.
    
    - **run_id**: UUID of the simulation run to retrieve
    """
    twin_service = DigitalTwinService(db)
    run = twin_service.get_simulation_run(run_id)
    
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulation run not found"
        )
    
    return run


@router.delete("/{twin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_digital_twin(
    twin_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a digital twin and all its simulation runs.
    
    - **twin_id**: UUID of the digital twin to delete
    """
    twin_service = DigitalTwinService(db)
    success = twin_service.delete_digital_twin(twin_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Digital twin not found"
        )
    
    logger.info("Digital twin deleted", twin_id=twin_id)