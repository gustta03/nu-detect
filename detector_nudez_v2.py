#!/usr/bin/env python3
"""
Script wrapper para executar detector_nudez_v2.py
Adiciona src ao path automaticamente
"""
import sys
import runpy
from pathlib import Path

# Adiciona src ao path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Executa o módulo principal
if __name__ == "__main__":
    # Executa o módulo como script
    runpy.run_path(str(src_path / "detector_nudez_v2.py"), run_name="__main__")
