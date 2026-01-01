#!/usr/bin/env python3
"""
Script de inicialização rápida para GUI
Execute este arquivo para iniciar a interface gráfica
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

sys.path.insert(0, str(project_root / "gui"))

if __name__ == "__main__":
    from gui_main import main
    main()

