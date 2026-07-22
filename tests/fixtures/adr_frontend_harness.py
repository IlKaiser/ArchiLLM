import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.adr_frontend import render

render(default_llm_model="test-model")
