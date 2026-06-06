import os
import sys

_UI_DIR       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  
_PROJECT_ROOT = os.path.dirname(_UI_DIR)                                     

if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)