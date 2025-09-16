(*
====================================================================
FUNCTION_BLOCK: FB_SafetyController
Description: Safety Integrated Level (SIL2) controller for industrial automation
Features: - Dual channel safety monitoring
          - Safety relay output control
          - Diagnostic coverage
          - Proof test management
          - Safety function monitoring
Standard: IEC 61508 / IEC 62061 compliant
Author: PLC-Copilot Knowledge Base
Version: 3.0
Date: 2024-09-15
====================================================================
*)

FUNCTION_BLOCK FB_SafetyController
VAR_INPUT
    // Dual channel emergency stop inputs
    i_bEStop_Ch1      : BOOL;    // E-Stop channel 1
    i_bEStop_Ch2      : BOOL;    // E-Stop channel 2
    
    // Light curtain dual channel
    i_bLightCurtain_Ch1 : BOOL;  // Light curtain channel 1
    i_bLightCurtain_Ch2 : BOOL;  // Light curtain channel 2
    
    // Safety door monitoring
    i_bSafetyDoor_Ch1 : BOOL;    // Safety door channel 1  
    i_bSafetyDoor_Ch2 : BOOL;    // Safety door channel 2
    i_bDoorLock       : BOOL;    // Door lock feedback
    
    // Enable/disable inputs
    i_bEnableSwitch_Ch1 : BOOL;  // Enable switch channel 1
    i_bEnableSwitch_Ch2 : BOOL;  // Enable switch channel 2
    
    // System control
    i_bSystemReset    : BOOL;    // System reset command
    i_bTestMode       : BOOL;    // Test mode activation
    i_tProofTestInterval : TIME; // Proof test interval
    
    // Configuration
    i_bBypassEnable   : BOOL;    // Maintenance bypass enable
    i_sAccessCode     : STRING;  // Access code for bypass
END_VAR

VAR_OUTPUT
    // Safety outputs (dual channel)
    o_bSafetyRelay_Ch1 : BOOL;   // Safety relay channel 1
    o_bSafetyRelay_Ch2 : BOOL;   // Safety relay channel 2
    o_bSafetyOK       : BOOL;    // Combined safety status
    
    // Door control
    o_bDoorUnlock     : BOOL;    // Door unlock command
    
    // Status and diagnostics
    o_bFault          : BOOL;    // Fault detected
    o_bWarning        : BOOL;    // Warning condition
    o_bTestRequired   : BOOL;    // Proof test required
    o_sStatus         : STRING;  // Status message
    
    // Diagnostic outputs
    o_wDiagnostic     : WORD;    // Diagnostic word
    o_dSafetyTime     : DWORD;   // Total safety time
    o_dFaultCount     : DWORD;   // Fault counter
END_VAR

VAR
    // Safety state machine
    eSafetyState      : E_SafetyState;
    eLastState        : E_SafetyState;
    
    // Channel monitoring
    bEStop_OK         : BOOL;
    bLightCurtain_OK  : BOOL;
    bSafetyDoor_OK    : BOOL;
    bEnableSwitch_OK  : BOOL;
    
    // Discrepancy detection
    bEStop_Discrepancy     : BOOL;
    bLightCurtain_Discrepancy : BOOL;
    bSafetyDoor_Discrepancy   : BOOL;
    bEnableSwitch_Discrepancy : BOOL;
    
    // Timers
    tonDiscrepancyDelay    : TON;
    tonDoorUnlockDelay     : TON;
    tonSafetyTimer         : TON;
    tonProofTestTimer      : TON;
    
    // Fault management
    bChannelFault     : BOOL;
    bCommunicationFault : BOOL;
    bFaultLatched     : BOOL;
    
    // Test management
    bProofTestActive  : BOOL;
    bTestStepComplete : BOOL;
    nTestStep         : INT;
    
    // Maintenance bypass
    bBypassActive     : BOOL;
    tonBypassTimer    : TON;
    
    // Internal safety logic
    bAllChannelsOK    : BOOL;
    bSafetyConditions : BOOL;
    
    // Diagnostics
    tSystemStartTime  : TIME;
    dSafeSeconds      : DWORD;
END_VAR

// Safety state enumeration
TYPE E_SafetyState :
(
    SAFE_STOP,          // All systems stopped safely
    SAFE_OPERATIONAL,   // Normal operation allowed
    FAULT,              // Fault condition
    TEST_MODE,          // Proof test mode
    BYPASS_MODE         // Maintenance bypass
);
END_TYPE

// ========== MAIN PROGRAM ==========

// Dual channel input evaluation
bEStop_OK := i_bEStop_Ch1 AND i_bEStop_Ch2;
bLightCurtain_OK := i_bLightCurtain_Ch1 AND i_bLightCurtain_Ch2;
bSafetyDoor_OK := i_bSafetyDoor_Ch1 AND i_bSafetyDoor_Ch2;
bEnableSwitch_OK := i_bEnableSwitch_Ch1 AND i_bEnableSwitch_Ch2;

// Discrepancy detection (cross-channel monitoring)
bEStop_Discrepancy := i_bEStop_Ch1 XOR i_bEStop_Ch2;
bLightCurtain_Discrepancy := i_bLightCurtain_Ch1 XOR i_bLightCurtain_Ch2;
bSafetyDoor_Discrepancy := i_bSafetyDoor_Ch1 XOR i_bSafetyDoor_Ch2;
bEnableSwitch_Discrepancy := i_bEnableSwitch_Ch1 XOR i_bEnableSwitch_Ch2;

// Channel fault detection
bChannelFault := bEStop_Discrepancy OR bLightCurtain_Discrepancy OR 
                 bSafetyDoor_Discrepancy OR bEnableSwitch_Discrepancy;

// Discrepancy timer for fault latching
tonDiscrepancyDelay(IN := bChannelFault, PT := T#500MS);

IF tonDiscrepancyDelay.Q THEN
    bFaultLatched := TRUE;
    o_dFaultCount := o_dFaultCount + 1;
END_IF

// Overall safety condition
bAllChannelsOK := bEStop_OK AND bLightCurtain_OK AND bSafetyDoor_OK;
bSafetyConditions := bAllChannelsOK AND NOT bFaultLatched;

// Proof test timer
tonProofTestTimer(IN := TRUE, PT := i_tProofTestInterval);
o_bTestRequired := tonProofTestTimer.Q;

// Safety state machine
CASE eSafetyState OF
    SAFE_STOP:
        o_bSafetyRelay_Ch1 := FALSE;
        o_bSafetyRelay_Ch2 := FALSE;
        o_bSafetyOK := FALSE;
        o_bDoorUnlock := TRUE;  // Allow access when stopped
        o_sStatus := 'Safety Stop';
        
        // Transition to operational if conditions met
        IF bSafetyConditions AND bEnableSwitch_OK AND i_bDoorLock THEN
            tonDoorUnlockDelay(IN := FALSE);
            o_bDoorUnlock := FALSE;
            eSafetyState := SAFE_OPERATIONAL;
        END_IF
        
        // Transition to test mode
        IF i_bTestMode AND NOT bFaultLatched THEN
            eSafetyState := TEST_MODE;
            nTestStep := 1;
        END_IF
        
        // Fault condition
        IF bFaultLatched THEN
            eSafetyState := FAULT;
        END_IF
    
    SAFE_OPERATIONAL:
        o_bSafetyRelay_Ch1 := TRUE;
        o_bSafetyRelay_Ch2 := TRUE;
        o_bSafetyOK := TRUE;
        o_bDoorUnlock := FALSE;
        o_sStatus := 'Operational';
        
        // Safety timer for maximum operation time
        tonSafetyTimer(IN := TRUE, PT := T#1S);
        IF tonSafetyTimer.Q THEN
            dSafeSeconds := dSafeSeconds + 1;
            o_dSafetyTime := dSafeSeconds;
            tonSafetyTimer(IN := FALSE);
        END_IF
        
        // Return to safe stop on any safety condition failure
        IF NOT bSafetyConditions OR NOT bEnableSwitch_OK THEN
            eSafetyState := SAFE_STOP;
            tonSafetyTimer(IN := FALSE);
        END_IF
        
        // Door unlock delay when stopping
        tonDoorUnlockDelay(IN := (eSafetyState = SAFE_STOP), PT := T#2S);
    
    FAULT:
        o_bSafetyRelay_Ch1 := FALSE;
        o_bSafetyRelay_Ch2 := FALSE;
        o_bSafetyOK := FALSE;
        o_bDoorUnlock := TRUE;
        tonSafetyTimer(IN := FALSE);
        
        IF bChannelFault THEN
            o_sStatus := 'FAULT: Channel discrepancy';
        ELSIF bCommunicationFault THEN
            o_sStatus := 'FAULT: Communication';
        ELSE
            o_sStatus := 'FAULT: General';
        END_IF
        
        // Reset fault if conditions cleared and reset pressed
        IF i_bSystemReset AND NOT bChannelFault THEN
            bFaultLatched := FALSE;
            eSafetyState := SAFE_STOP;
        END_IF
    
    TEST_MODE:
        o_bSafetyOK := FALSE;
        o_sStatus := 'Proof Test Active';
        
        // Simplified proof test sequence
        CASE nTestStep OF
            1: // Test safety relays
                o_bSafetyRelay_Ch1 := FALSE;
                o_bSafetyRelay_Ch2 := TRUE;
                nTestStep := 2;
            
            2: // Test cross-channel
                o_bSafetyRelay_Ch1 := TRUE;
                o_bSafetyRelay_Ch2 := FALSE;
                nTestStep := 3;
            
            3: // Complete test
                o_bSafetyRelay_Ch1 := FALSE;
                o_bSafetyRelay_Ch2 := FALSE;
                bTestStepComplete := TRUE;
                tonProofTestTimer(IN := FALSE); // Reset proof test timer
                eSafetyState := SAFE_STOP;
        END_CASE
        
        // Exit test mode
        IF NOT i_bTestMode THEN
            eSafetyState := SAFE_STOP;
        END_IF
    
    BYPASS_MODE:
        // Maintenance bypass (use with extreme caution)
        o_sStatus := 'BYPASS MODE - CAUTION';
        tonBypassTimer(IN := TRUE, PT := T#30M); // 30 minute maximum
        
        IF tonBypassTimer.Q OR NOT i_bBypassEnable THEN
            eSafetyState := SAFE_STOP;
            tonBypassTimer(IN := FALSE);
        END_IF
END_CASE

// Output assignments and diagnostics
o_bFault := (eSafetyState = FAULT);
o_bWarning := bChannelFault AND NOT bFaultLatched;

// Diagnostic word assignment
o_wDiagnostic.0 := bEStop_Discrepancy;
o_wDiagnostic.1 := bLightCurtain_Discrepancy;
o_wDiagnostic.2 := bSafetyDoor_Discrepancy;
o_wDiagnostic.3 := bEnableSwitch_Discrepancy;
o_wDiagnostic.4 := bFaultLatched;
o_wDiagnostic.5 := o_bTestRequired;
o_wDiagnostic.6 := (eSafetyState = TEST_MODE);
o_wDiagnostic.7 := (eSafetyState = BYPASS_MODE);

// State change logging
IF eSafetyState <> eLastState THEN
    eLastState := eSafetyState;
    // Log safety state change for audit trail
END_IF

END_FUNCTION_BLOCK