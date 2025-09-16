(*
====================================================================
FUNCTION_BLOCK: FB_BeltConveyor
Description: Industrial belt conveyor control with comprehensive safety
Features: - Emergency stop circuits
          - Light curtain safety
          - Motor protection
          - Diagnostic monitoring
          - Maintenance counters
Author: PLC-Copilot Knowledge Base
Version: 2.1
Date: 2024-09-15
====================================================================
*)

FUNCTION_BLOCK FB_BeltConveyor
VAR_INPUT
    // Command inputs
    i_bStart          : BOOL;    // Start command
    i_bStop           : BOOL;    // Stop command
    i_bReset          : BOOL;    // Fault reset
    
    // Safety inputs
    i_bEmergencyStop  : BOOL;    // Emergency stop chain
    i_bLightCurtain   : BOOL;    // Light curtain OK
    i_bGuardDoor      : BOOL;    // Guard door closed
    
    // Sensor inputs
    i_bMotorThermal   : BOOL;    // Motor thermal protection
    i_bBeltAlignment  : BOOL;    // Belt alignment sensor
    i_rMotorCurrent   : REAL;    // Motor current feedback
    i_rSpeed          : REAL;    // Speed feedback (Hz)
    
    // Configuration
    i_rSetSpeed       : REAL;    // Desired speed (Hz)
    i_rMaxCurrent     : REAL;    // Maximum allowed current
    i_tStartDelay     : TIME;    // Start delay time
END_VAR

VAR_OUTPUT
    // Control outputs
    o_bMotorRun       : BOOL;    // Motor run command
    o_bMotorForward   : BOOL;    // Motor forward direction
    o_rSpeedRef       : REAL;    // Speed reference output
    
    // Status outputs
    o_bRunning        : BOOL;    // Conveyor running
    o_bReady          : BOOL;    // Ready to start
    o_bFault          : BOOL;    // Fault active
    o_bWarning        : BOOL;    // Warning active
    
    // Diagnostic outputs
    o_sStatus         : STRING;  // Status text
    o_dRunHours       : DWORD;   // Total run hours
    o_dStartCount     : DWORD;   // Start counter
END_VAR

VAR
    // Internal state machine
    eState            : E_ConveyorState;
    eLastState        : E_ConveyorState;
    
    // Timers
    tonStartDelay     : TON;
    tonCurrentLimit   : TON;
    tonRunTimer       : TON;
    
    // Safety logic
    bSafetyOK         : BOOL;
    bSafetyChain      : BOOL;
    
    // Fault handling
    bOverCurrent      : BOOL;
    bSpeedDeviation   : BOOL;
    bFaultLatched     : BOOL;
    
    // Maintenance counters
    dRunSeconds       : DWORD;
    tLastStart        : TIME;
    
    // Speed control
    rSpeedError       : REAL;
    rSpeedTolerance   : REAL := 2.0;
END_VAR

// State enumeration
TYPE E_ConveyorState :
(
    STOPPED,
    STARTING,
    RUNNING,
    STOPPING,
    FAULT
);
END_TYPE

// ========== MAIN PROGRAM ==========

// Safety chain evaluation
bSafetyChain := i_bEmergencyStop AND i_bLightCurtain AND i_bGuardDoor AND i_bMotorThermal;
bSafetyOK := bSafetyChain AND i_bBeltAlignment;

// Fault detection
bOverCurrent := i_rMotorCurrent > i_rMaxCurrent;
tonCurrentLimit(IN := bOverCurrent, PT := T#2S);

bSpeedDeviation := (eState = RUNNING) AND (ABS(i_rSpeed - i_rSetSpeed) > rSpeedTolerance);

// Fault latching
IF tonCurrentLimit.Q OR bSpeedDeviation OR NOT bSafetyOK THEN
    bFaultLatched := TRUE;
END_IF

IF i_bReset AND (eState = FAULT) THEN
    bFaultLatched := FALSE;
END_IF

// State machine
CASE eState OF
    STOPPED:
        o_bMotorRun := FALSE;
        o_bMotorForward := FALSE;
        o_rSpeedRef := 0.0;
        o_sStatus := 'Stopped';
        
        IF i_bStart AND bSafetyOK AND NOT bFaultLatched THEN
            eState := STARTING;
            tLastStart := TIME();
            o_dStartCount := o_dStartCount + 1;
        END_IF
        
        IF bFaultLatched THEN
            eState := FAULT;
        END_IF
    
    STARTING:
        tonStartDelay(IN := TRUE, PT := i_tStartDelay);
        o_sStatus := 'Starting...';
        
        IF tonStartDelay.Q THEN
            eState := RUNNING;
            tonStartDelay(IN := FALSE);
            tonRunTimer(IN := TRUE, PT := T#1S);
        END_IF
        
        IF i_bStop OR NOT bSafetyOK OR bFaultLatched THEN
            eState := STOPPING;
            tonStartDelay(IN := FALSE);
        END_IF
    
    RUNNING:
        o_bMotorRun := TRUE;
        o_bMotorForward := TRUE;
        o_rSpeedRef := i_rSetSpeed;
        o_sStatus := 'Running';
        
        // Run time accumulation
        tonRunTimer(IN := TRUE, PT := T#1S);
        IF tonRunTimer.Q THEN
            dRunSeconds := dRunSeconds + 1;
            o_dRunHours := dRunSeconds / 3600;
            tonRunTimer(IN := FALSE);
        END_IF
        
        IF i_bStop OR NOT bSafetyOK OR bFaultLatched THEN
            eState := STOPPING;
        END_IF
    
    STOPPING:
        o_bMotorRun := FALSE;
        o_rSpeedRef := 0.0;
        o_sStatus := 'Stopping...';
        tonRunTimer(IN := FALSE);
        
        // Wait for speed to drop to zero
        IF i_rSpeed < 1.0 THEN
            eState := STOPPED;
        END_IF
        
        IF bFaultLatched THEN
            eState := FAULT;
        END_IF
    
    FAULT:
        o_bMotorRun := FALSE;
        o_bMotorForward := FALSE;
        o_rSpeedRef := 0.0;
        tonRunTimer(IN := FALSE);
        
        IF bOverCurrent THEN
            o_sStatus := 'FAULT: Overcurrent';
        ELSIF bSpeedDeviation THEN
            o_sStatus := 'FAULT: Speed deviation';
        ELSIF NOT bSafetyChain THEN
            o_sStatus := 'FAULT: Safety circuit';
        ELSE
            o_sStatus := 'FAULT: General';
        END_IF
        
        IF i_bReset AND NOT bFaultLatched THEN
            eState := STOPPED;
        END_IF
END_CASE

// Output assignments
o_bRunning := (eState = RUNNING);
o_bReady := (eState = STOPPED) AND bSafetyOK AND NOT bFaultLatched;
o_bFault := (eState = FAULT);
o_bWarning := bOverCurrent AND NOT tonCurrentLimit.Q;

// State change detection for logging
IF eState <> eLastState THEN
    eLastState := eState;
    // Log state change (implementation depends on logging system)
END_IF

END_FUNCTION_BLOCK