"""Alias nazwy 00_start.py — ten sam test, bez zmian ERPNext."""
import runpy
from pathlib import Path
if __name__ == '__main__':
    runpy.run_path(str(Path(__file__).with_name('00_start.py')), run_name='__main__')
