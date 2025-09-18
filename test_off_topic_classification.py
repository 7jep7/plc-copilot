#!/usr/bin/env python3
"""
Test to ensure genuinely off-topic requests are still caught.
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

def test_off_topic_examples():
    """Test genuinely off-topic examples to ensure they're still caught."""
    
    off_topic_examples = [
        "I want to learn about cooking pasta recipes",
        "How do I fix my car's engine?",
        "What is the weather like today?",
        "Can you help me with my homework on biology?",
        "I need help writing a resume",
        "How to bake a chocolate cake?",
        "What are the best travel destinations?",
        "How do I learn guitar?",
        "What is quantum physics?",
        "Help me plan my wedding",
        "How to lose weight effectively?",
        "What are the best movies to watch?",
        "How to train my dog?",
        "I need fashion advice",
        "How to grow tomatoes in my garden?",
        "Can you help me with my relationship problems?",
        "What is cryptocurrency?",
        "How to learn Spanish?",
        "Best hiking trails near me",
        "How to paint a portrait?"
    ]
    
    print("🔍 Testing Off-Topic Classification")
    print("=" * 45)
    
    correctly_off_topic = []
    incorrectly_classified = []
    
    for example in off_topic_examples:
        is_plc_related = _is_plc_related_current(example)
        if not is_plc_related:
            correctly_off_topic.append(example)
        else:
            incorrectly_classified.append(example)
    
    print(f"\n✅ Correctly classified as OFF-TOPIC ({len(correctly_off_topic)}/{len(off_topic_examples)}):")
    for example in correctly_off_topic:
        print(f"   ✅ '{example}'")
    
    if incorrectly_classified:
        print(f"\n❌ Incorrectly classified as ON-TOPIC ({len(incorrectly_classified)}/{len(off_topic_examples)}):")
        for example in incorrectly_classified:
            print(f"   ❌ '{example}'")
            
            # Find which keyword triggered
            example_lower = example.lower()
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
            
            triggered_keywords = [kw for kw in plc_keywords if kw in example_lower]
            print(f"      Triggered by: {triggered_keywords}")
    else:
        print(f"\n🎉 All off-topic examples correctly classified!")

if __name__ == "__main__":
    test_off_topic_examples()