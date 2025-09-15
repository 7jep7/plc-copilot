"""Digital twin simulation service for testing PLC code."""

import structlog
import asyncio
import time
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.models.digital_twin import DigitalTwin, SimulationRun, SimulationStatus
from app.models.plc_code import PLCCode
from app.schemas.digital_twin import DigitalTwinCreate, SimulationTestRequest

logger = structlog.get_logger()


class DigitalTwinService:
    """Service for digital twin simulation and testing."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_digital_twin(self, twin_data: DigitalTwinCreate) -> DigitalTwin:
        """Create a new digital twin simulation environment."""
        digital_twin = DigitalTwin(
            name=twin_data.name,
            description=twin_data.description,
            simulation_type=twin_data.simulation_type,
            configuration=twin_data.configuration,
            status=SimulationStatus.CREATED
        )
        
        self.db.add(digital_twin)
        self.db.commit()
        self.db.refresh(digital_twin)
        
        logger.info("Digital twin created", twin_id=str(digital_twin.id))
        return digital_twin
    
    def get_digital_twins(
        self,
        skip: int = 0,
        limit: int = 100,
        simulation_type: Optional[str] = None
    ) -> List[DigitalTwin]:
        """Get list of digital twins with optional filtering."""
        query = self.db.query(DigitalTwin)
        
        if simulation_type:
            query = query.filter(DigitalTwin.simulation_type == simulation_type)
        
        return query.offset(skip).limit(limit).all()
    
    def get_digital_twin(self, twin_id: str) -> Optional[DigitalTwin]:
        """Get a specific digital twin by ID."""
        try:
            return self.db.query(DigitalTwin).filter(DigitalTwin.id == twin_id).first()
        except Exception:
            return None
    
    def delete_digital_twin(self, twin_id: str) -> bool:
        """Delete a digital twin and all its simulation runs."""
        twin = self.get_digital_twin(twin_id)
        if not twin:
            return False
        
        # Delete all simulation runs first
        self.db.query(SimulationRun).filter(SimulationRun.digital_twin_id == twin_id).delete()
        
        # Delete the twin
        self.db.delete(twin)
        self.db.commit()
        return True
    
    async def run_simulation(self, twin_id: str, test_request: SimulationTestRequest) -> Optional[SimulationRun]:
        """
        Run a simulation test of PLC code in the digital twin.
        
        Args:
            twin_id: ID of the digital twin
            test_request: Test configuration and parameters
            
        Returns:
            Simulation run record with results
        """
        twin = self.get_digital_twin(twin_id)
        if not twin:
            return None
        
        # Get the PLC code to test
        plc_code = self.db.query(PLCCode).filter(PLCCode.id == test_request.plc_code_id).first()
        if not plc_code:
            raise ValueError(f"PLC code {test_request.plc_code_id} not found")
        
        # Create simulation run record
        simulation_run = SimulationRun(
            digital_twin_id=twin_id,
            plc_code_id=test_request.plc_code_id,
            test_name=test_request.test_name,
            test_parameters=test_request.test_parameters,
            expected_outcomes=test_request.expected_outcomes,
            status=SimulationStatus.RUNNING
        )
        
        self.db.add(simulation_run)
        self.db.commit()
        self.db.refresh(simulation_run)
        
        logger.info("Starting simulation", run_id=str(simulation_run.id))
        
        try:
            # Run the actual simulation
            start_time = time.time()
            simulation_results = await self._execute_simulation(twin, plc_code, test_request)
            execution_duration = time.time() - start_time
            
            # Update simulation run with results
            simulation_run.status = SimulationStatus.COMPLETED
            simulation_run.execution_duration = execution_duration
            simulation_run.actual_outcomes = simulation_results["outcomes"]
            simulation_run.test_passed = simulation_results["test_passed"]
            simulation_run.cycle_time = simulation_results.get("cycle_time")
            simulation_run.energy_consumption = simulation_results.get("energy_consumption")
            simulation_run.throughput = simulation_results.get("throughput")
            
            if simulation_results.get("warnings"):
                simulation_run.warnings = "\n".join(simulation_results["warnings"])
            
            self.db.commit()
            self.db.refresh(simulation_run)
            
            logger.info("Simulation completed", run_id=str(simulation_run.id), passed=simulation_results["test_passed"])
            return simulation_run
            
        except Exception as e:
            # Update simulation run with error
            simulation_run.status = SimulationStatus.FAILED
            simulation_run.error_messages = str(e)
            simulation_run.test_passed = False
            
            self.db.commit()
            self.db.refresh(simulation_run)
            
            logger.error("Simulation failed", run_id=str(simulation_run.id), error=str(e))
            raise
    
    async def _execute_simulation(
        self,
        twin: DigitalTwin,
        plc_code: PLCCode,
        test_request: SimulationTestRequest
    ) -> Dict[str, Any]:
        """
        Execute the actual simulation logic.
        
        This is a simplified simulation - in a real system, this would
        interface with actual simulation software or physics engines.
        """
        simulation_type = twin.simulation_type.lower()
        
        # Simulate execution delay
        await asyncio.sleep(min(test_request.simulation_duration, 5.0))
        
        # Generate simulated results based on simulation type
        if simulation_type == "conveyor_belt":
            return await self._simulate_conveyor_belt(twin, plc_code, test_request)
        elif simulation_type == "robotic_arm":
            return await self._simulate_robotic_arm(twin, plc_code, test_request)
        else:
            return await self._simulate_generic_process(twin, plc_code, test_request)
    
    async def _simulate_conveyor_belt(self, twin: DigitalTwin, plc_code: PLCCode, test_request: SimulationTestRequest) -> Dict[str, Any]:
        """Simulate a conveyor belt system."""
        # Simplified conveyor belt simulation
        config = twin.configuration
        belt_speed = config.get("belt_speed", 1.0)  # m/s
        belt_length = config.get("belt_length", 10.0)  # meters
        
        cycle_time = belt_length / belt_speed
        throughput = 3600 / cycle_time  # items per hour
        energy_consumption = belt_speed * 0.5  # kW (simplified)
        
        # Check for safety conditions in PLC code
        safety_checks_passed = "emergency_stop" in plc_code.source_code.lower()
        
        return {
            "test_passed": safety_checks_passed,
            "outcomes": {
                "belt_operational": True,
                "items_transported": int(throughput * test_request.simulation_duration / 3600),
                "safety_systems_active": safety_checks_passed
            },
            "cycle_time": cycle_time,
            "energy_consumption": energy_consumption,
            "throughput": throughput,
            "warnings": [] if safety_checks_passed else ["No emergency stop logic detected in PLC code"]
        }
    
    async def _simulate_robotic_arm(self, twin: DigitalTwin, plc_code: PLCCode, test_request: SimulationTestRequest) -> Dict[str, Any]:
        """Simulate a robotic arm system."""
        config = twin.configuration
        arm_reach = config.get("arm_reach", 1.5)  # meters
        payload_capacity = config.get("payload_capacity", 10.0)  # kg
        
        # Simplified arm simulation
        cycle_time = 15.0  # seconds per pick-place cycle
        throughput = 3600 / cycle_time  # operations per hour
        energy_consumption = payload_capacity * 0.1  # kW (simplified)
        
        # Check for position limits in PLC code
        has_limits = any(keyword in plc_code.source_code.lower() for keyword in ["limit", "range", "boundary"])
        
        return {
            "test_passed": has_limits,
            "outcomes": {
                "arm_operational": True,
                "successful_operations": int(throughput * test_request.simulation_duration / 3600),
                "position_limits_enforced": has_limits
            },
            "cycle_time": cycle_time,
            "energy_consumption": energy_consumption,
            "throughput": throughput,
            "warnings": [] if has_limits else ["No position limit checks detected in PLC code"]
        }
    
    async def _simulate_generic_process(self, twin: DigitalTwin, plc_code: PLCCode, test_request: SimulationTestRequest) -> Dict[str, Any]:
        """Simulate a generic industrial process."""
        return {
            "test_passed": True,
            "outcomes": {
                "process_completed": True,
                "no_errors": True
            },
            "cycle_time": 10.0,
            "energy_consumption": 2.5,
            "throughput": 360.0,
            "warnings": []
        }
    
    def get_simulation_runs(self, twin_id: str, skip: int = 0, limit: int = 50) -> List[SimulationRun]:
        """Get simulation runs for a specific digital twin."""
        return (self.db.query(SimulationRun)
                .filter(SimulationRun.digital_twin_id == twin_id)
                .offset(skip)
                .limit(limit)
                .all())
    
    def get_simulation_run(self, run_id: str) -> Optional[SimulationRun]:
        """Get a specific simulation run by ID."""
        try:
            return self.db.query(SimulationRun).filter(SimulationRun.id == run_id).first()
        except Exception:
            return None