#!/usr/bin/env python3
"""
Script para executar o AI SQL Agent
"""
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from agents.terminal_interface import main

if __name__ == "__main__":
    main()
