#!/usr/bin/env python3
"""
Test to check which sample projects would be misclassified as off-topic.
"""

def _is_plc_related_current(message: str) -> bool:
    """Current implementation of PLC topic detection."""
    plc_keywords = [
        # Core PLC terms
        "plc", "programmable logic", "structured text", "ladder logic",
        "automation", "industrial", "control", "scada", "hmi",
        "motor", "sensor", "actuator", "conveyor", "process control",
        "safety", "interlock", "tag", "variable", "function block",
        
        # Manufacturing & Production
        "assembly line", "robot", "robotic", "packaging", "rfid", "tracking",
        "machine tool", "cnc", "cutting", "welding", "manufacturing",
        "injection molding", "steel mill", "rolling", "processing",
        
        # Building & Infrastructure  
        "hvac", "building management", "warehouse", "storage", "retrieval",
        "power distribution", "load management", "elevator", "baggage handling",
        
        # Energy & Utilities
        "solar panel", "solar", "wind turbine", "power", "energy",
        "water treatment", "pump station", "boiler", "steam",
        
        # Specialized Industries
        "semiconductor", "cleanroom", "hospital", "patient", "bed management",
        "airport", "baggage", "handling", "fish farm", "water quality",
        "pharmaceutical", "food processing", "chemical reactor",
        
        # General Industrial Terms
        "management system", "environmental control", "climate control",
        "temperature control", "pressure control", "monitoring",
        "distribution", "crane", "hoist", "textile", "loom",
        "brewery", "fermentation", "mining", "paper mill", "automotive",
        "glass manufacturing", "oil refinery", "greenhouse", "irrigation"
    ]
    
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in plc_keywords)

def test_sample_projects_classification():
    """Test all sample projects against the current classification."""
    
    # All 40 sample projects
    all_sample_projects = [
        "Conveyor Belt Control System with Safety Interlocks",
        "Motor Speed Control with VFD Integration",
        "Process Control with PID Temperature Regulation",
        "Automated Packaging Line with RFID Tracking",
        "Water Treatment Plant Control System",
        "Assembly Line Robot Integration",
        "HVAC Building Management System",
        "Batch Mixing Process Control",
        "Parking Garage Access Control",
        "Traffic Light Control System",
        "Warehouse Automated Storage and Retrieval",
        "Chemical Reactor Temperature and Pressure Control",
        "Elevator Control System with Safety Features",
        "Food Processing Line with Quality Control",
        "Solar Panel Tracking System",
        "Pump Station Control with Redundancy",
        "Machine Tool CNC Integration",
        "Power Distribution and Load Management",
        "Irrigation System with Soil Moisture Sensors",
        "Pharmaceutical Tablet Press Control",
        "Paint Booth Ventilation and Safety System",
        "Boiler Control with Steam Management",
        "Crane and Hoist Safety Control",
        "Textile Loom Automation",
        "Metal Cutting and Welding Line",
        "Brewery Fermentation Process Control",
        "Wind Turbine Control and Monitoring",
        "Mining Conveyor and Crusher Control",
        "Paper Mill Process Automation",
        "Automotive Paint Line Control",
        "Glass Manufacturing Temperature Control",
        "Oil Refinery Process Safety System",
        "Airport Baggage Handling System",
        "Hospital Patient Bed Management",
        "Data Center Environmental Control",
        "Greenhouse Climate Control System",
        "Fish Farm Water Quality Management",
        "Plastic Injection Molding Control",
        "Steel Mill Rolling Process Control",
        "Semiconductor Cleanroom Management"
    ]
    
    print("🔍 Testing Sample Project Classification")
    print("=" * 50)
    
    misclassified = []
    correctly_classified = []
    
    for project in all_sample_projects:
        is_plc_related = _is_plc_related_current(project)
        if is_plc_related:
            correctly_classified.append(project)
        else:
            misclassified.append(project)
    
    print(f"\n✅ Correctly classified ({len(correctly_classified)}/40):")
    for project in correctly_classified:
        print(f"   ✅ {project}")
    
    print(f"\n❌ Misclassified as OFF-TOPIC ({len(misclassified)}/40):")
    for project in misclassified:
        print(f"   ❌ {project}")
    
    if misclassified:
        print(f"\n🚨 {len(misclassified)} projects need keyword expansion!")
        
        # Analyze what keywords are missing
        print(f"\n🔍 Missing keyword analysis:")
        for project in misclassified:
            print(f"   '{project}' - needs keywords like:")
            project_lower = project.lower()
            suggestions = []
            if "parking" in project_lower:
                suggestions.append("parking")
            if "traffic" in project_lower:
                suggestions.append("traffic")
            if "solar" in project_lower:
                suggestions.append("solar")
            if "tracking" in project_lower:
                suggestions.append("tracking")
            if "airport" in project_lower:
                suggestions.append("airport")
            if "baggage" in project_lower:
                suggestions.append("baggage")
            if "handling" in project_lower:
                suggestions.append("handling")
            if "hospital" in project_lower:
                suggestions.append("hospital")
            if "patient" in project_lower:
                suggestions.append("patient")
            if "bed" in project_lower:
                suggestions.append("bed")
            if "management" in project_lower:
                suggestions.append("management")
            if "fish" in project_lower:
                suggestions.append("fish")
            if "farm" in project_lower:
                suggestions.append("farm")
            if "water quality" in project_lower:
                suggestions.append("water quality")
            if "semiconductor" in project_lower:
                suggestions.append("semiconductor")
            if "cleanroom" in project_lower:
                suggestions.append("cleanroom")
            
            print(f"     {', '.join(suggestions) if suggestions else 'General industrial/automation terms'}")
    else:
        print(f"\n🎉 All sample projects correctly classified!")

if __name__ == "__main__":
    test_sample_projects_classification()