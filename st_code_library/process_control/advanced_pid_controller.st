(*
====================================================================
FUNCTION_BLOCK: FB_PIDController
Description: Industrial PID controller with advanced features
Features: - Auto-tuning capability
          - Anti-windup protection
          - Setpoint tracking
          - Manual/Auto modes
          - Cascade control support
          - Adaptive parameters
Application: Temperature, pressure, flow, level control
Author: PLC-Copilot Knowledge Base
Version: 2.3
Date: 2024-09-15
====================================================================
*)

FUNCTION_BLOCK FB_PIDController
VAR_INPUT
    // Process values
    i_rProcessValue   : REAL;    // Current process value
    i_rSetpoint       : REAL;    // Desired setpoint
    i_rFeedforward    : REAL;    // Feedforward signal
    
    // Control modes
    i_bManualMode     : BOOL;    // Manual mode enable
    i_bAutoMode       : BOOL;    // Automatic mode enable
    i_bCascadeMode    : BOOL;    // Cascade mode enable
    i_rManualOutput   : REAL;    // Manual output value
    
    // PID parameters
    i_rKp             : REAL;    // Proportional gain
    i_rTi             : REAL;    // Integral time (seconds)
    i_rTd             : REAL;    // Derivative time (seconds)
    i_rN              : REAL;    // Derivative filter factor
    
    // Limits and constraints
    i_rOutputMin      : REAL;    // Minimum output limit
    i_rOutputMax      : REAL;    // Maximum output limit
    i_rSlewRateMax    : REAL;    // Maximum output slew rate
    
    // Auto-tuning
    i_bAutoTune       : BOOL;    // Start auto-tuning
    i_rTuneAmplitude  : REAL;    // Tuning step amplitude
    
    // Advanced features
    i_bTrackingMode   : BOOL;    // Setpoint tracking mode
    i_rTrackingGain   : REAL;    // Tracking gain factor
    i_tSampleTime     : TIME;    // Controller sample time
END_VAR

VAR_OUTPUT
    // Control output
    o_rOutput         : REAL;    // Controller output
    o_rOutputPercent  : REAL;    // Output as percentage
    
    // Status
    o_bInAuto         : BOOL;    // Controller in automatic
    o_bInManual       : BOOL;    // Controller in manual
    o_bAtSetpoint     : BOOL;    // Process at setpoint
    o_bOutputLimited  : BOOL;    // Output is limited
    
    // Diagnostics
    o_rError          : REAL;    // Current error
    o_rErrorPercent   : REAL;    // Error as percentage of span
    o_rDerivative     : REAL;    // Derivative term
    o_rIntegral       : REAL;    // Integral term
    
    // Auto-tuning results
    o_bTuningComplete : BOOL;    // Auto-tuning finished
    o_rTunedKp        : REAL;    // Tuned proportional gain
    o_rTunedTi        : REAL;    // Tuned integral time
    o_rTunedTd        : REAL;    // Tuned derivative time
    
    // Performance metrics
    o_rSettlingTime   : REAL;    // Settling time (seconds)
    o_rOvershoot      : REAL;    // Maximum overshoot
    o_dControlCount   : DWORD;   // Control loop count
END_VAR

VAR
    // Control algorithm variables
    rError            : REAL;
    rLastError        : REAL;
    rErrorDerivative  : REAL;
    rErrorIntegral    : REAL;
    rLastProcessValue : REAL;
    
    // PID terms
    rProportional     : REAL;
    rIntegralTerm     : REAL;
    rDerivativeTerm   : REAL;
    rPIDSum           : REAL;
    
    // Output management
    rRawOutput        : REAL;
    rLastOutput       : REAL;
    rOutputChange     : REAL;
    bOutputSaturated  : BOOL;
    
    // Mode management
    eControlMode      : E_ControlMode;
    eLastMode         : E_ControlMode;
    bModeChanged      : BOOL;
    
    // Timing
    tonSampleTimer    : TON;
    tLastSample       : TIME;
    rDeltaTime        : REAL;
    
    // Auto-tuning variables
    eTuneState        : E_TuneState;
    rTuneStartPV      : REAL;
    rTuneStepTime     : REAL;
    rTuneResponse     : REAL;
    bTuneStepApplied  : BOOL;
    nTuneCycle        : INT;
    
    // Setpoint tracking
    rTrackingError    : REAL;
    rTrackingOutput   : REAL;
    
    // Anti-windup
    bWindupCondition  : BOOL;
    rWindupLimit      : REAL;
    
    // Performance monitoring
    rMaxError         : REAL;
    rErrorSum         : REAL;
    tonSettleTimer    : TON;
    bSettled          : BOOL;
    
    // Process span for percentage calculations
    rProcessSpan      : REAL := 100.0;
    rDeadbandPercent  : REAL := 1.0;
END_VAR

// Control mode enumeration
TYPE E_ControlMode :
(
    MANUAL,
    AUTOMATIC,
    CASCADE,
    TRACKING
);
END_TYPE

// Auto-tuning state enumeration
TYPE E_TuneState :
(
    TUNE_IDLE,
    TUNE_STEP,
    TUNE_MEASURE,
    TUNE_CALCULATE,
    TUNE_COMPLETE
);
END_TYPE

// ========== MAIN PROGRAM ==========

// Sample timer management
tonSampleTimer(IN := TRUE, PT := i_tSampleTime);
IF tonSampleTimer.Q THEN
    tonSampleTimer(IN := FALSE);
    rDeltaTime := TIME_TO_REAL(i_tSampleTime) / 1000.0; // Convert to seconds
    o_dControlCount := o_dControlCount + 1;
    
    // Mode determination
    IF i_bManualMode THEN
        eControlMode := MANUAL;
    ELSIF i_bCascadeMode THEN
        eControlMode := CASCADE;
    ELSIF i_bTrackingMode THEN
        eControlMode := TRACKING;
    ELSIF i_bAutoMode THEN
        eControlMode := AUTOMATIC;
    ELSE
        eControlMode := MANUAL; // Default to manual for safety
    END_IF
    
    // Mode change detection
    bModeChanged := (eControlMode <> eLastMode);
    IF bModeChanged THEN
        eLastMode := eControlMode;
        // Reset integral term on mode change
        rErrorIntegral := o_rOutput;
    END_IF
    
    // Error calculation
    rError := i_rSetpoint - i_rProcessValue;
    o_rError := rError;
    o_rErrorPercent := (rError / rProcessSpan) * 100.0;
    
    // Control algorithm execution
    CASE eControlMode OF
        MANUAL:
            o_rOutput := i_rManualOutput;
            // Track output for bumpless transfer
            rErrorIntegral := o_rOutput;
            
        AUTOMATIC, CASCADE:
            // Proportional term
            rProportional := i_rKp * rError;
            
            // Integral term with anti-windup
            IF i_rTi > 0.0 THEN
                rIntegralTerm := rErrorIntegral + (i_rKp * rError * rDeltaTime / i_rTi);
                
                // Anti-windup check
                rWindupLimit := i_rOutputMax - rProportional - rDerivativeTerm;
                IF rIntegralTerm > rWindupLimit THEN
                    rIntegralTerm := rWindupLimit;
                    bWindupCondition := TRUE;
                ELSIF rIntegralTerm < (i_rOutputMin - rProportional - rDerivativeTerm) THEN
                    rIntegralTerm := i_rOutputMin - rProportional - rDerivativeTerm;
                    bWindupCondition := TRUE;
                ELSE
                    bWindupCondition := FALSE;
                END_IF
                
                rErrorIntegral := rIntegralTerm;
            ELSE
                rIntegralTerm := 0.0;
            END_IF
            
            // Derivative term with filtering
            IF i_rTd > 0.0 AND rDeltaTime > 0.0 THEN
                rErrorDerivative := (i_rProcessValue - rLastProcessValue) / rDeltaTime;
                // Low-pass filter on derivative
                rDerivativeTerm := rDerivativeTerm + ((-i_rKp * i_rTd * rErrorDerivative) - rDerivativeTerm) * 
                                   (rDeltaTime / (i_rTd / i_rN + rDeltaTime));
            ELSE
                rDerivativeTerm := 0.0;
            END_IF
            
            // PID sum with feedforward
            rPIDSum := rProportional + rIntegralTerm + rDerivativeTerm + i_rFeedforward;
            
            // Output limiting with slew rate
            rOutputChange := rPIDSum - rLastOutput;
            IF i_rSlewRateMax > 0.0 THEN
                IF rOutputChange > (i_rSlewRateMax * rDeltaTime) THEN
                    rOutputChange := i_rSlewRateMax * rDeltaTime;
                ELSIF rOutputChange < (-i_rSlewRateMax * rDeltaTime) THEN
                    rOutputChange := -i_rSlewRateMax * rDeltaTime;
                END_IF
            END_IF
            
            rRawOutput := rLastOutput + rOutputChange;
            
            // Final output limiting
            IF rRawOutput > i_rOutputMax THEN
                o_rOutput := i_rOutputMax;
                bOutputSaturated := TRUE;
            ELSIF rRawOutput < i_rOutputMin THEN
                o_rOutput := i_rOutputMin;
                bOutputSaturated := TRUE;
            ELSE
                o_rOutput := rRawOutput;
                bOutputSaturated := FALSE;
            END_IF
            
        TRACKING:
            // Setpoint tracking mode
            rTrackingError := i_rSetpoint - o_rOutput;
            rTrackingOutput := o_rOutput + (i_rTrackingGain * rTrackingError * rDeltaTime);
            o_rOutput := LIMIT(i_rOutputMin, rTrackingOutput, i_rOutputMax);
    END_CASE
    
    // Auto-tuning logic (simplified Ziegler-Nichols method)
    IF i_bAutoTune AND (eControlMode = AUTOMATIC) THEN
        CASE eTuneState OF
            TUNE_IDLE:
                rTuneStartPV := i_rProcessValue;
                eTuneState := TUNE_STEP;
                nTuneCycle := 0;
                
            TUNE_STEP:
                // Apply step change
                o_rOutput := i_rManualOutput + i_rTuneAmplitude;
                bTuneStepApplied := TRUE;
                rTuneStepTime := 0.0;
                eTuneState := TUNE_MEASURE;
                
            TUNE_MEASURE:
                rTuneStepTime := rTuneStepTime + rDeltaTime;
                rTuneResponse := i_rProcessValue - rTuneStartPV;
                
                // Simple response measurement (63.2% of final value)
                IF ABS(rTuneResponse) >= (0.632 * i_rTuneAmplitude) THEN
                    eTuneState := TUNE_CALCULATE;
                END_IF
                
                // Timeout after 60 seconds
                IF rTuneStepTime > 60.0 THEN
                    eTuneState := TUNE_CALCULATE;
                END_IF
                
            TUNE_CALCULATE:
                // Calculate PID parameters (simplified)
                o_rTunedKp := 1.2 / (i_rTuneAmplitude / ABS(rTuneResponse));
                o_rTunedTi := 2.0 * rTuneStepTime;
                o_rTunedTd := 0.5 * rTuneStepTime;
                eTuneState := TUNE_COMPLETE;
                o_bTuningComplete := TRUE;
        END_CASE
    ELSE
        eTuneState := TUNE_IDLE;
        o_bTuningComplete := FALSE;
    END_IF
    
    // Performance monitoring
    IF ABS(rError) > rMaxError THEN
        rMaxError := ABS(rError);
        o_rOvershoot := rMaxError;
    END_IF
    
    // Settling time calculation
    tonSettleTimer(IN := (ABS(o_rErrorPercent) <= rDeadbandPercent), PT := T#5S);
    IF tonSettleTimer.Q AND NOT bSettled THEN
        o_rSettlingTime := TIME_TO_REAL(TIME() - tLastSample) / 1000.0;
        bSettled := TRUE;
    END_IF
    
    // Store values for next cycle
    rLastError := rError;
    rLastProcessValue := i_rProcessValue;
    rLastOutput := o_rOutput;
    tLastSample := TIME();
END_IF

// Output assignments
o_rOutputPercent := (o_rOutput / (i_rOutputMax - i_rOutputMin)) * 100.0;
o_bInAuto := (eControlMode = AUTOMATIC) OR (eControlMode = CASCADE);
o_bInManual := (eControlMode = MANUAL);
o_bAtSetpoint := ABS(o_rErrorPercent) <= rDeadbandPercent;
o_bOutputLimited := bOutputSaturated;

// Diagnostic outputs
o_rDerivative := rDerivativeTerm;
o_rIntegral := rIntegralTerm;

END_FUNCTION_BLOCK