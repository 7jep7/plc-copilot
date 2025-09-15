"""Digital twin schemas for request/response validation."""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.digital_twin import SimulationStatus


class DigitalTwinBase(BaseModel):
    """Base digital twin schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    simulation_type: str = Field(..., min_length=1, max_length=100)


class DigitalTwinCreate(DigitalTwinBase):
    """Schema for creating a new digital twin."""
    configuration: Dict[str, Any] = Field(..., description="Simulation configuration parameters")


class DigitalTwinResponse(DigitalTwinBase):
    """Schema for digital twin responses."""
    id: str
    configuration: Dict[str, Any]
    status: str
    execution_time: Optional[float] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    simulation_results: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    error_log: Optional[str] = None
    is_successful: bool
    safety_checks_passed: bool
    efficiency_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SimulationRunBase(BaseModel):
    """Base simulation run schema."""
    test_name: str = Field(..., min_length=1, max_length=255)
    test_parameters: Optional[Dict[str, Any]] = None
    expected_outcomes: Optional[Dict[str, Any]] = None


class SimulationRunCreate(SimulationRunBase):
    """Schema for creating a simulation run."""
    plc_code_id: str = Field(..., description="UUID of the PLC code to test")


class SimulationTestRequest(BaseModel):
    """Schema for simulation test requests."""
    plc_code_id: str = Field(..., description="UUID of the PLC code to test")
    test_name: str = Field(..., min_length=1, max_length=255)
    test_parameters: Optional[Dict[str, Any]] = None
    expected_outcomes: Optional[Dict[str, Any]] = None
    
    # Test configuration
    simulation_duration: float = Field(default=10.0, gt=0.0, le=300.0)  # seconds
    real_time_factor: float = Field(default=1.0, gt=0.1, le=10.0)
    enable_safety_monitoring: bool = True
    enable_performance_monitoring: bool = True


class SimulationRunResponse(SimulationRunBase):
    """Schema for simulation run responses."""
    id: str
    digital_twin_id: str
    plc_code_id: str
    status: str
    execution_duration: Optional[float] = None
    actual_outcomes: Optional[Dict[str, Any]] = None
    test_passed: bool
    error_messages: Optional[str] = None
    warnings: Optional[str] = None
    cycle_time: Optional[float] = None
    energy_consumption: Optional[float] = None
    throughput: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SimulationMetrics(BaseModel):
    """Schema for simulation performance metrics."""
    cycle_time: Optional[float] = None
    energy_consumption: Optional[float] = None
    throughput: Optional[float] = None
    efficiency_score: Optional[float] = None
    safety_violations: int = 0
    total_runtime: Optional[float] = None
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None