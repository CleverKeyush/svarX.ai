# model_manager.py
from pathlib import Path
import platform
import os

SYSTEM = platform.system()

def program_model_dir():
    """
    Return the program-level model directory depending on OS.
    Windows -> C:\Program Files\GmailAIPro\models
    macOS  -> /Applications/GmailAIPro/models
    Linux  -> /opt/GmailAIPro/models (fallback)
    """
    if SYSTEM == "Windows":
        return Path(os.environ.get("ProgramFiles", "C:\\Program Files")) / "GmailAIPro" / "models"
    elif SYSTEM == "Darwin":
        return Path("/Applications") / "GmailAIPro" / "models"
    else:
        return Path("/opt") / "GmailAIPro" / "models"

# expected model filename (Llama-3.2-3B quantized)
MODEL_FILENAME = "Llama-3.2-3B-Instruct-Q4_K_M.gguf"

DEFAULT_MODEL_PATH = program_model_dir() / MODEL_FILENAME

def get_model_path():
    """
    Find the model file in order of preference:
    1. Program directory (production)
    2. Local models directory (development)
    """
    # Check program directory first
    program_path = program_model_dir() / MODEL_FILENAME
    if program_path.exists() and program_path.stat().st_size > 1000:
        return program_path
    
    # Check local development directory
    local_path = Path(__file__).parent / "models" / MODEL_FILENAME
    # Create models directory if it doesn't exist
    local_path.parent.mkdir(exist_ok=True)
    if local_path.exists() and local_path.stat().st_size > 1000:
        return local_path
    
    # Return default path for error reporting
    return program_path

def model_exists(path: Path = None) -> bool:
    if path is None:
        path = get_model_path()
    return path.exists() and path.stat().st_size > 1000

def model_path_str(path: Path = None) -> str:
    if path is None:
        path = get_model_path()
    return str(path)
