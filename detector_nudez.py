
"""
Script wrapper para executar detector_nudez.py
Adiciona src ao path automaticamente
"""
import sys
import runpy
from pathlib import Path


project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))


if __name__ == "__main__":

    runpy.run_path(str(src_path / "detector_nudez.py"), run_name="__main__")
