#!/usr/bin/env python3
"""
EcoSort AI - Main Entry Point
Interactive CLI for waste classification and disposal guidance
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agents.supervisor import EcoSortSupervisor
from agents.classifier import WasteClassifierAgent
from agents.rag_agent import RAGAgent
from agents.location_impact import LocationAgent, ImpactTrackerAgent


def print_banner():
    print("""
+----------------------------------------------------------------+
|                    [EcoSort AI v1.0]                        |
|         AI-Powered Smart Waste Segregation Assistant         |
|              Powered by IBM Granite + watsonx.ai             |
+----------------------------------------------------------------+
""")


def print_help():
    print("""
Commands:
  classify <item>        - Classify a waste item (e.g., "plastic bottle")
  ask <category> <question> - Ask disposal question (e.g., "Organic Can I compost meat?")
  centers [category]     - List nearby recycling centers
  impact <category> [kg] - Calculate environmental impact
  demo                   - Run demo with sample items
  help                   - Show this help
  quit                   - Exit

Examples:
  > classify banana peel
  > ask Recyclable (Plastic) How to recycle plastic bags?
  > centers E-waste
  > impact E-waste 2
  > demo
""")


def run_demo(supervisor):
    """Run interactive demo with sample items"""
    demo_items = [
        "plastic water bottle",
        "banana peel", 
        "old smartphone",
        "used battery",
        "aluminum can",
        "glass jar",
        "cardboard box",
        "pizza box (greasy)",
        "used cooking oil",
        "expired medicine"
    ]
    
    print("\n[DEMO] Running Demo with Sample Items\n" + "="*50)
    
    for item in demo_items:
        print(f"\n[>>] Analyzing: '{item}'")
        response = supervisor.process_request(item)
        print(response.user_friendly)
        print("-"*50)
    
    print(f"\n[OK] Demo complete!")


def main():
    import sys
    
    # Check for command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == 'demo':
        print_banner()
        supervisor = EcoSortSupervisor()
        run_demo(supervisor)
        return
    
    print_banner()
    
    # Initialize supervisor
    supervisor = EcoSortSupervisor()
    
    # Check if Watsonx is configured
    from src.config.settings import load_configs
    watsonx, cos, app = load_configs()
    
    if not watsonx.project_id:
        print("[WARN] Watsonx not configured - using rule-based fallback")
        print("   Set WATSONX_PROJECT_ID and WATSONX_API_KEY in .env for AI classification\n")
    
    if not cos.api_key_id:
        print("[WARN] COS not configured - image upload disabled")
        print("   Set COS_API_KEY_ID and COS_SERVICE_INSTANCE_ID in .env\n")
    
    print_help()
    
    while True:
        try:
            user_input = input("\n[EcoSort] ").strip()
            
            if not user_input:
                continue
            
            parts = user_input.split(maxsplit=2)
            cmd = parts[0].lower()
            
            if cmd in ('quit', 'exit', 'q'):
                print("Goodbye! Keep sorting!")
                break
            
            elif cmd == 'help':
                print_help()
            
            elif cmd == 'demo':
                run_demo(supervisor)
            
            elif cmd == 'classify':
                if len(parts) < 2:
                    print("Usage: classify <item description>")
                    continue
                item = parts[1]
                response = supervisor.process_request(item)
                print(response.user_friendly)
            
            elif cmd == 'ask':
                if len(parts) < 3:
                    print("Usage: ask <category> <question>")
                    continue
                category, question = parts[1], parts[2]
                result = supervisor.ask_question(category, question)
                print(f"\n[BOOK] Answer ({result.category}): {result.answer}")
            
            elif cmd == 'centers':
                category = parts[1] if len(parts) > 1 else None
                centers = supervisor.get_centers_nearby(category)
                if centers:
                    print(f"\n[LOCATION] Nearby Centers ({'for ' + category if category else 'all'}):")
                    for c in centers:
                        print(f"  * {c.name} ({c.distance_km} km) - {c.address} - {c.hours}")
                else:
                    print("No centers found")
            
            elif cmd == 'impact':
                if len(parts) < 2:
                    print("Usage: impact <category> [weight_kg]")
                    continue
                category = parts[1]
                weight = float(parts[2]) if len(parts) > 2 else 1.0
                metrics = supervisor.calculate_impact(category, weight)
                print(supervisor.impact.format_impact(metrics, category, weight))
            
            else:
                print(f"Unknown command: {cmd}. Type 'help' for commands.")
        
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"[ERROR] Error: {e}")


if __name__ == "__main__":
    main()