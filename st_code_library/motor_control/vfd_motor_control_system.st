(*
====================================================================
PROGRAM: MotorControlSystem
Description: Complete motor control system with VFD integration
Features: - Variable frequency drive control
          - Soft start/stop sequences
          - Speed ramping and profiling
          - Motor protection and monitoring
          - Energy optimization
          - Fault diagnosis and recovery
Application: Industrial motor drives, pumps, fans, conveyors
Author: PLC-Copilot Knowledge Base
Version: 3.1
Date: 2024-09-15
====================================================================
*)

PROGRAM MotorControlSystem
VAR
    // Motor control interface
    fbMotorDrive         : FB_MotorDriveControl;
    fbSpeedController    : FB_SpeedController;
    fbMotorProtection    : FB_MotorProtection;
    fbEnergyOptimizer    : FB_EnergyOptimizer;
    
    // HMI interface
    stHMIControl         : ST_MotorHMI;
    stHMIStatus          : ST_MotorStatus;
    
    // Communication with VFD
    stVFDCommand         : ST_VFDCommand;
    stVFDFeedback        : ST_VFDFeedback;
    
    // Safety and interlocks
    bEmergencyStop       : BOOL;
    bPermissiveStart     : BOOL;
    bMaintenanceMode     : BOOL;
    bBypassProtection    : BOOL;
    
    // Process control
    rSpeedSetpoint       : REAL := 0.0;    // Target speed (RPM)
    rSpeedFeedback       : REAL;           // Actual speed (RPM)
    rTorqueFeedback      : REAL;           // Motor torque (%)
    rCurrentFeedback     : REAL;           // Motor current (A)
    rPowerFeedback       : REAL;           // Motor power (kW)
    
    // System status
    eSystemState         : E_MotorSystemState;
    eLastSystemState     : E_MotorSystemState;
    bSystemHealthy       : BOOL;
    nFaultCode          : WORD;
    sStatusMessage      : STRING(80);
END_VAR

// Motor system states
TYPE E_MotorSystemState :
(
    MOTOR_STOPPED,
    MOTOR_STARTING,
    MOTOR_RUNNING,
    MOTOR_STOPPING,
    MOTOR_FAULT,
    MOTOR_MAINTENANCE
);
END_TYPE

// HMI control structure
TYPE ST_MotorHMI :
STRUCT
    bStartCommand        : BOOL;
    bStopCommand         : BOOL;
    bResetFaults         : BOOL;
    rSpeedCommand        : REAL;
    rAccelTime           : REAL;
    rDecelTime           : REAL;
    bJogMode             : BOOL;
    rJogSpeed            : REAL;
    bEnergyOptimize      : BOOL;
END_STRUCT
END_TYPE

// Motor status structure
TYPE ST_MotorStatus :
STRUCT
    bRunning             : BOOL;
    bFaulted             : BOOL;
    bReady               : BOOL;
    rActualSpeed         : REAL;
    rActualTorque        : REAL;
    rActualCurrent       : REAL;
    rActualPower         : REAL;
    rEfficiency          : REAL;
    rTemperature         : REAL;
    nRunHours           : DWORD;
    rEnergyConsumed     : REAL;
END_STRUCT
END_TYPE

// VFD command structure
TYPE ST_VFDCommand :
STRUCT
    bEnable              : BOOL;
    bStart               : BOOL;
    bStop                : BOOL;
    bReset               : BOOL;
    rSpeedReference      : REAL;
    rAcceleration        : REAL;
    rDeceleration        : REAL;
    eControlMode         : E_VFDControlMode;
END_STRUCT
END_TYPE

// VFD feedback structure
TYPE ST_VFDFeedback :
STRUCT
    bReady               : BOOL;
    bRunning             : BOOL;
    bFault               : BOOL;
    bWarning             : BOOL;
    rActualSpeed         : REAL;
    rOutputFrequency     : REAL;
    rOutputVoltage       : REAL;
    rOutputCurrent       : REAL;
    rDCBusVoltage        : REAL;
    rTemperature         : REAL;
    nFaultCode          : WORD;
    rPowerFactor        : REAL;
END_STRUCT
END_TYPE

// VFD control modes
TYPE E_VFDControlMode :
(
    VFD_SPEED_CONTROL,
    VFD_TORQUE_CONTROL,
    VFD_POSITION_CONTROL
);
END_TYPE

// ========== FUNCTION BLOCKS ==========

FUNCTION_BLOCK FB_MotorDriveControl
VAR_INPUT
    i_bEnable            : BOOL;
    i_bStart             : BOOL;
    i_bStop              : BOOL;
    i_bReset             : BOOL;
    i_rSpeedSetpoint     : REAL;
    i_stVFDFeedback      : ST_VFDFeedback;
    i_bEmergencyStop     : BOOL;
    i_bPermissive        : BOOL;
END_VAR

VAR_OUTPUT
    o_stVFDCommand       : ST_VFDCommand;
    o_eState             : E_MotorSystemState;
    o_bFaulted           : BOOL;
    o_nFaultCode         : WORD;
    o_sStatusMessage     : STRING(80);
END_VAR

VAR
    eState               : E_MotorSystemState;
    tonStartDelay        : TON;
    tonStopDelay         : TON;
    fbSafetyMonitor      : FB_SafetyMonitor;
    bStartConditionMet   : BOOL;
    bStopConditionMet    : BOOL;
END_VAR

// Safety and permissive checks
fbSafetyMonitor(
    i_bEmergencyStop := i_bEmergencyStop,
    i_bPermissive := i_bPermissive,
    i_stVFDFeedback := i_stVFDFeedback
);

bStartConditionMet := i_bEnable AND i_bPermissive AND NOT i_bEmergencyStop AND 
                     i_stVFDFeedback.bReady AND NOT i_stVFDFeedback.bFault;

bStopConditionMet := NOT i_bEnable OR i_bEmergencyStop OR i_stVFDFeedback.bFault;

// State machine
CASE eState OF
    MOTOR_STOPPED:
        o_stVFDCommand.bEnable := FALSE;
        o_stVFDCommand.bStart := FALSE;
        o_stVFDCommand.rSpeedReference := 0.0;
        o_sStatusMessage := 'Motor Stopped';
        
        IF i_bStart AND bStartConditionMet THEN
            eState := MOTOR_STARTING;
            tonStartDelay(IN := FALSE);
        END_IF
        
    MOTOR_STARTING:
        o_stVFDCommand.bEnable := TRUE;
        tonStartDelay(IN := TRUE, PT := T#2S);
        o_sStatusMessage := 'Motor Starting...';
        
        IF tonStartDelay.Q THEN
            o_stVFDCommand.bStart := TRUE;
            o_stVFDCommand.rSpeedReference := i_rSpeedSetpoint;
            eState := MOTOR_RUNNING;
        END_IF
        
        IF bStopConditionMet THEN
            eState := MOTOR_STOPPING;
        END_IF
        
    MOTOR_RUNNING:
        o_stVFDCommand.bEnable := TRUE;
        o_stVFDCommand.bStart := TRUE;
        o_stVFDCommand.rSpeedReference := i_rSpeedSetpoint;
        o_sStatusMessage := 'Motor Running';
        
        IF i_bStop OR bStopConditionMet THEN
            eState := MOTOR_STOPPING;
        END_IF
        
    MOTOR_STOPPING:
        o_stVFDCommand.bStart := FALSE;
        tonStopDelay(IN := TRUE, PT := T#3S);
        o_sStatusMessage := 'Motor Stopping...';
        
        IF tonStopDelay.Q OR i_stVFDFeedback.rActualSpeed < 10.0 THEN
            o_stVFDCommand.bEnable := FALSE;
            eState := MOTOR_STOPPED;
            tonStopDelay(IN := FALSE);
        END_IF
        
    MOTOR_FAULT:
        o_stVFDCommand.bEnable := FALSE;
        o_stVFDCommand.bStart := FALSE;
        o_bFaulted := TRUE;
        o_nFaultCode := i_stVFDFeedback.nFaultCode;
        o_sStatusMessage := 'Motor Fault - Check Diagnostics';
        
        IF i_bReset AND NOT i_stVFDFeedback.bFault THEN
            o_stVFDCommand.bReset := TRUE;
            eState := MOTOR_STOPPED;
            o_bFaulted := FALSE;
        END_IF
END_CASE

// Fault detection
IF i_stVFDFeedback.bFault THEN
    eState := MOTOR_FAULT;
END_IF

o_eState := eState;

END_FUNCTION_BLOCK

FUNCTION_BLOCK FB_SpeedController
VAR_INPUT
    i_rSpeedSetpoint     : REAL;
    i_rSpeedFeedback     : REAL;
    i_rAccelTime         : REAL;
    i_rDecelTime         : REAL;
    i_bEnable            : BOOL;
END_VAR

VAR_OUTPUT
    o_rSpeedCommand      : REAL;
    o_bAtSetpoint        : BOOL;
    o_rSpeedError        : REAL;
END_VAR

VAR
    fbRampGenerator      : FB_RampGenerator;
    fbPIDSpeed          : FB_PIDController;
    rRampedSetpoint     : REAL;
    rSpeedDeadband      : REAL := 5.0;
END_VAR

// Speed ramping
fbRampGenerator(
    i_rInput := i_rSpeedSetpoint,
    i_rRampUp := 100.0 / i_rAccelTime,     // Units per second
    i_rRampDown := 100.0 / i_rDecelTime,
    i_bEnable := i_bEnable
);
rRampedSetpoint := fbRampGenerator.o_rOutput;

// Speed control
fbPIDSpeed(
    i_rProcessValue := i_rSpeedFeedback,
    i_rSetpoint := rRampedSetpoint,
    i_bAutoMode := i_bEnable,
    i_rKp := 1.0,
    i_rTi := 0.5,
    i_rTd := 0.1,
    i_rOutputMin := 0.0,
    i_rOutputMax := 100.0,
    i_tSampleTime := T#100MS
);

o_rSpeedCommand := fbPIDSpeed.o_rOutput;
o_rSpeedError := rRampedSetpoint - i_rSpeedFeedback;
o_bAtSetpoint := ABS(o_rSpeedError) <= rSpeedDeadband;

END_FUNCTION_BLOCK

FUNCTION_BLOCK FB_MotorProtection
VAR_INPUT
    i_rCurrent           : REAL;
    i_rPower             : REAL;
    i_rTemperature       : REAL;
    i_rSpeed             : REAL;
    i_bRunning           : BOOL;
    i_bBypass            : BOOL;
END_VAR

VAR_OUTPUT
    o_bOvercurrent       : BOOL;
    o_bOverload          : BOOL;
    o_bOvertemperature   : BOOL;
    o_bUnderspeed        : BOOL;
    o_bProtectionTrip    : BOOL;
    o_sAlarmMessage      : STRING(80);
END_VAR

VAR
    // Protection limits
    rCurrentLimit        : REAL := 150.0;  // % of rated
    rPowerLimit          : REAL := 110.0;  // % of rated
    rTempLimit           : REAL := 85.0;   // °C
    rMinSpeed            : REAL := 50.0;   // RPM
    
    // Timers for protection delays
    tonOvercurrentDelay  : TON;
    tonOverloadDelay     : TON;
    tonOvertempDelay     : TON;
    tonUnderspeedDelay   : TON;
    
    // Alarm management
    bAnyAlarm            : BOOL;
END_VAR

// Current protection
tonOvercurrentDelay(IN := (i_rCurrent > rCurrentLimit) AND i_bRunning AND NOT i_bBypass, 
                   PT := T#500MS);
o_bOvercurrent := tonOvercurrentDelay.Q;

// Power/overload protection
tonOverloadDelay(IN := (i_rPower > rPowerLimit) AND i_bRunning AND NOT i_bBypass, 
                PT := T#10S);
o_bOverload := tonOverloadDelay.Q;

// Temperature protection
tonOvertempDelay(IN := (i_rTemperature > rTempLimit) AND NOT i_bBypass, 
                PT := T#5S);
o_bOvertemperature := tonOvertempDelay.Q;

// Underspeed protection
tonUnderspeedDelay(IN := (i_rSpeed < rMinSpeed) AND i_bRunning AND NOT i_bBypass, 
                  PT := T#15S);
o_bUnderspeed := tonUnderspeedDelay.Q;

// Overall protection trip
o_bProtectionTrip := o_bOvercurrent OR o_bOverload OR o_bOvertemperature OR o_bUnderspeed;

// Alarm message generation
IF o_bOvercurrent THEN
    o_sAlarmMessage := 'ALARM: Motor Overcurrent';
ELSIF o_bOverload THEN
    o_sAlarmMessage := 'ALARM: Motor Overload';
ELSIF o_bOvertemperature THEN
    o_sAlarmMessage := 'ALARM: Motor Overtemperature';
ELSIF o_bUnderspeed THEN
    o_sAlarmMessage := 'ALARM: Motor Underspeed';
ELSE
    o_sAlarmMessage := '';
END_IF;

END_FUNCTION_BLOCK

// ========== MAIN PROGRAM EXECUTION ==========

// Read HMI commands
rSpeedSetpoint := stHMIControl.rSpeedCommand;

// Motor drive control
fbMotorDrive(
    i_bEnable := NOT bEmergencyStop AND bPermissiveStart,
    i_bStart := stHMIControl.bStartCommand,
    i_bStop := stHMIControl.bStopCommand,
    i_bReset := stHMIControl.bResetFaults,
    i_rSpeedSetpoint := rSpeedSetpoint,
    i_stVFDFeedback := stVFDFeedback,
    i_bEmergencyStop := bEmergencyStop,
    i_bPermissive := bPermissiveStart
);

// Speed control
fbSpeedController(
    i_rSpeedSetpoint := rSpeedSetpoint,
    i_rSpeedFeedback := stVFDFeedback.rActualSpeed,
    i_rAccelTime := stHMIControl.rAccelTime,
    i_rDecelTime := stHMIControl.rDecelTime,
    i_bEnable := (fbMotorDrive.o_eState = MOTOR_RUNNING)
);

// Motor protection
fbMotorProtection(
    i_rCurrent := stVFDFeedback.rOutputCurrent,
    i_rPower := rPowerFeedback,
    i_rTemperature := stVFDFeedback.rTemperature,
    i_rSpeed := stVFDFeedback.rActualSpeed,
    i_bRunning := stVFDFeedback.bRunning,
    i_bBypass := bBypassProtection
);

// Energy optimization
fbEnergyOptimizer(
    i_rSpeed := stVFDFeedback.rActualSpeed,
    i_rTorque := rTorqueFeedback,
    i_rPower := rPowerFeedback,
    i_bOptimizeEnable := stHMIControl.bEnergyOptimize
);

// System state management
eSystemState := fbMotorDrive.o_eState;
bSystemHealthy := NOT fbMotorDrive.o_bFaulted AND NOT fbMotorProtection.o_bProtectionTrip;
nFaultCode := fbMotorDrive.o_nFaultCode;
sStatusMessage := fbMotorDrive.o_sStatusMessage;

// Update HMI status
stHMIStatus.bRunning := stVFDFeedback.bRunning;
stHMIStatus.bFaulted := fbMotorDrive.o_bFaulted OR fbMotorProtection.o_bProtectionTrip;
stHMIStatus.bReady := stVFDFeedback.bReady AND bSystemHealthy;
stHMIStatus.rActualSpeed := stVFDFeedback.rActualSpeed;
stHMIStatus.rActualTorque := rTorqueFeedback;
stHMIStatus.rActualCurrent := stVFDFeedback.rOutputCurrent;
stHMIStatus.rActualPower := rPowerFeedback;
stHMIStatus.rEfficiency := fbEnergyOptimizer.o_rEfficiency;
stHMIStatus.rTemperature := stVFDFeedback.rTemperature;
stHMIStatus.rEnergyConsumed := fbEnergyOptimizer.o_rEnergyConsumed;

// Emergency stop handling
IF bEmergencyStop THEN
    stVFDCommand.bEnable := FALSE;
    stVFDCommand.bStart := FALSE;
    eSystemState := MOTOR_STOPPING;
END_IF

// Copy motor drive commands to VFD interface
stVFDCommand := fbMotorDrive.o_stVFDCommand;
stVFDCommand.rAcceleration := stHMIControl.rAccelTime;
stVFDCommand.rDeceleration := stHMIControl.rDecelTime;
stVFDCommand.eControlMode := VFD_SPEED_CONTROL;

END_PROGRAM