#!/usr/bin/env python3
"""
Test edge cases and borderline industrial examples.
"""

def _is_plc_related_current(message: str) -> bool:
    """Current implementation of PLC topic detection."""
    plc_keywords = [
        # Core PLC terms
        "plc", "programmable logic", "structured text", "ladder logic",
        "automation", "industrial automation", "industrial control", "control system",
        "scada", "hmi", "process control", "safety interlock", "safety system",
        "motor control", "sensor", "actuator", "conveyor", "interlock", 
        "tag", "variable", "function block",
        
        # Manufacturing & Production
        "assembly line", "manufacturing", "factory automation", "production line",
        "robotic", "packaging line", "rfid tracking", "manufacturing process",
        "machine tool", "cnc", "metal cutting", "welding line", 
        "injection molding", "steel mill", "rolling process",
        
        # Building & Infrastructure Systems
        "hvac", "building management", "warehouse automation", "storage system", 
        "automated storage", "power distribution", "load management", 
        "elevator control", "baggage handling system",
        
        # Energy & Utilities
        "solar panel tracking", "solar panel control", "wind turbine control", 
        "power plant", "energy management system", "water treatment", 
        "pump station", "boiler control", "steam management",
        
        # Specialized Industries
        "semiconductor", "cleanroom management", "hospital system", 
        "patient bed management", "airport system", "baggage handling",
        "fish farm", "water quality management", "pharmaceutical",
        "food processing", "chemical reactor", "process safety",
        
        # General Industrial Terms (more specific)
        "management system", "environmental control system", "climate control system",
        "temperature control", "pressure control", "monitoring system",
        "distribution system", "crane control", "hoist control", "textile loom",
        "brewery fermentation", "mining conveyor", "paper mill", "automotive paint",
        "glass manufacturing", "oil refinery", "greenhouse control", 
        "irrigation system", "equipment monitoring", "factory equipment"
    ]
    
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in plc_keywords)

def test_edge_cases():
    """Test edge cases and industrial borderline examples."""
    
    edge_cases = [
        # Should be ON-TOPIC (industrial/automation related)
        ("I want to automate my factory", True),
        ("Help me with industrial control systems", True),
        ("I need a robotic solution", True),
        ("Can you help with manufacturing processes?", True),
        ("I want to monitor my equipment", True),
        ("Need help with temperature control", True),
        ("Looking for energy management solutions", True),
        ("I need warehouse automation", True),
        ("Help with HVAC systems", True),
        ("Water treatment plant setup", True),
        
        # Should be OFF-TOPIC (not industrial/PLC related)  
        ("I want to control my TV", False),
        ("Help me track my fitness", False),
        ("I need energy drinks", False),
        ("Solar eclipse information", False),
        ("Hospital visitor information", False),
        ("Airport flight schedules", False),
        ("I want to cut my hair", False),
        ("Help me power my phone", False),
        ("I need to process my photos", False),
        ("Can you monitor my social media?", False),
        
        # Tricky cases
        ("Home automation with smart lights", False),  # Home, not industrial
        ("Package delivery tracking", False),  # Consumer, not industrial
        ("Personal energy management", False),  # Personal, not industrial
        ("Gaming robot programming", False),  # Gaming, not industrial
        ("Solar calculator for home", False),  # Home use, not industrial
    ]
    
    print("🔍 Testing Edge Cases and Borderline Examples")
    print("=" * 55)
    
    correct = 0
    total = len(edge_cases)
    
    for message, expected_on_topic in edge_cases:
        is_plc_related = _is_plc_related_current(message)
        is_correct = is_plc_related == expected_on_topic
        
        status = "✅" if is_correct else "❌"
        topic_status = "ON-TOPIC" if is_plc_related else "OFF-TOPIC"
        expected_status = "ON-TOPIC" if expected_on_topic else "OFF-TOPIC"
        
        print(f"   {status} '{message}'")
        print(f"       Classified: {topic_status} | Expected: {expected_status}")
        
        if is_correct:
            correct += 1
        else:
            # Find which keyword triggered for incorrect classifications
            if is_plc_related and not expected_on_topic:
                message_lower = message.lower()
                plc_keywords = [
                    "plc", "programmable logic", "structured text", "ladder logic",
                    "automation", "industrial", "control", "scada", "hmi",
                    "motor", "sensor", "actuator", "conveyor", "process control",
                    "safety", "interlock", "tag", "variable", "function block",
                    "assembly line", "robot", "robotic", "packaging", "rfid", "tracking",
                    "machine tool", "cnc", "cutting", "welding", "manufacturing",
                    "injection molding", "steel mill", "rolling", "processing",
                    "hvac", "building management", "warehouse", "storage", "retrieval",
                    "power distribution", "load management", "elevator", "baggage handling",
                    "solar panel", "solar", "wind turbine", "power", "energy",
                    "water treatment", "pump station", "boiler", "steam",
                    "semiconductor", "cleanroom", "hospital", "patient", "bed management",
                    "airport", "baggage", "handling", "fish farm", "water quality",
                    "pharmaceutical", "food processing", "chemical reactor",
                    "management system", "environmental control", "climate control",
                    "temperature control", "pressure control", "monitoring",
                    "distribution", "crane", "hoist", "textile", "loom",
                    "brewery", "fermentation", "mining", "paper mill", "automotive",
                    "glass manufacturing", "oil refinery", "greenhouse", "irrigation"
                ]
                
                triggered_keywords = [kw for kw in plc_keywords if kw in message_lower]
                print(f"       Incorrectly triggered by: {triggered_keywords}")
        
        print()
    
    print(f"🎯 Accuracy: {correct}/{total} ({correct/total*100:.1f}%)")

if __name__ == "__main__":
    test_edge_cases()