#!/usr/bin/env python3
"""
Test script to verify crew registry functionality.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from zerotoship.crews import CREW_REGISTRY
    print("✅ Successfully imported CREW_REGISTRY")
    print(f"📋 Available crews: {list(CREW_REGISTRY.keys())}")
    
    if 'AdvisoryBoardCrew' in CREW_REGISTRY:
        print("✅ AdvisoryBoardCrew is registered!")
        crew_class = CREW_REGISTRY['AdvisoryBoardCrew']
        print(f"📝 Crew class: {crew_class}")
        print(f"📝 Crew docstring: {crew_class.__doc__}")
    else:
        print("❌ AdvisoryBoardCrew is NOT registered!")
        print("Available crews:", list(CREW_REGISTRY.keys()))
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
