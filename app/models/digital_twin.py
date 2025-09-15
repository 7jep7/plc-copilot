"""Digital twin model for simulating and testing PLC code."""

from sqlalchemy import Column, String, Text, Float, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from enum import Enum

from app.models.base import BaseModel


class SimulationStatus(str, Enum):
    """Digital twin simulation status."""
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class DigitalTwin(BaseModel):
    """Model for digital twin simulations of industrial processes."""
    
    __tablename__ = "digital_twins"
    
    # Basic information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Simulation configuration
    simulation_type = Column(String(100), nullable=False)  # e.g., "conveyor_belt", "robotic_arm"
    configuration = Column(JSONB, nullable=False)  # Simulation parameters and setup
    
    # Status and execution
    status = Column(String(20), default=SimulationStatus.CREATED.value)
    execution_time = Column(Float, nullable=True)  # Actual execution time in seconds
    start_time = Column(String, nullable=True)  # ISO timestamp
    end_time = Column(String, nullable=True)  # ISO timestamp
    
    # Results and metrics
    simulation_results = Column(JSONB, nullable=True)  # Detailed simulation output
    performance_metrics = Column(JSONB, nullable=True)  # Performance indicators
    error_log = Column(Text, nullable=True)
    
    # Validation flags
    is_successful = Column(Boolean, default=False)
    safety_checks_passed = Column(Boolean, default=False)
    efficiency_score = Column(Float, nullable=True)  # 0-100 efficiency rating
    
    def __repr__(self):
        return f"<DigitalTwin(id={self.id}, name={self.name}, type={self.simulation_type}, status={self.status})>"


class SimulationRun(BaseModel):
    """Model for individual simulation test runs."""
    
    __tablename__ = "simulation_runs"
    
    # Relationships
    digital_twin_id = Column(UUID(as_uuid=True), ForeignKey("digital_twins.id"), nullable=False)
    plc_code_id = Column(UUID(as_uuid=True), ForeignKey("plc_codes.id"), nullable=False)
    
    digital_twin = relationship("DigitalTwin", backref="simulation_runs")
    plc_code = relationship("PLCCode", backref="simulation_runs")
    
    # Test configuration
    test_name = Column(String(255), nullable=False)
    test_parameters = Column(JSONB, nullable=True)  # Test-specific parameters
    expected_outcomes = Column(JSONB, nullable=True)  # Expected results for validation
    
    # Execution details
    status = Column(String(20), default=SimulationStatus.CREATED.value)
    execution_duration = Column(Float, nullable=True)  # Duration in seconds
    
    # Results
    actual_outcomes = Column(JSONB, nullable=True)  # Actual results from simulation
    test_passed = Column(Boolean, default=False)
    error_messages = Column(Text, nullable=True)
    warnings = Column(Text, nullable=True)
    
    # Metrics
    cycle_time = Column(Float, nullable=True)  # Process cycle time in seconds
    energy_consumption = Column(Float, nullable=True)  # Estimated energy usage
    throughput = Column(Float, nullable=True)  # Items processed per hour
    
    def __repr__(self):
        return f"<SimulationRun(id={self.id}, test_name={self.test_name}, status={self.status})>"