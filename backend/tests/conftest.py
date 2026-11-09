import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["LLM_PROVIDER"] = "mock"
os.environ["LLM_FALLBACK_PROVIDER"] = ""
os.environ["GNANI_API_KEY"] = ""
