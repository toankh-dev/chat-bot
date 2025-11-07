"""
AI Backend System - Root package.
"""

import sys
import os

# Add src directory to Python path for easier imports
if __name__ != "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

__version__ = "1.0.0"
__author__ = "Your Team" 
__description__ = "Enterprise AI chatbot backend with Clean Architecture"
