#!/usr/bin/env python3
"""
svarx.ai Simple Launcher - Uses PowerShell for reliable downloads
Minimal EXE that downloads AI engine and model using PowerShell
"""

import sys
import os
import subprocess
import time
import json
try:
    import psutil
except ImportError:
    psutil = None

def print_header():
    """Print welcome header"""
    print("=" * 60)
    print("🚀 svarx.ai - AI Email Assistant Server")
    print("=" * 60)
    print("📧 Smart AI suggestions for Gmail, LinkedIn & more!")
    print("🎯 Downloads everything automatically on first run")
    print()

def check_python():
    """Check if Python is installed"""
    print("🔍 Checking Python installation...")
    try:
        result = subprocess.run(['python', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ Python found: {version}")
            return True
    except:
        pass
    
    print("❌ Python not found!")
    print("📥 Please install Python from: https://python.org/downloads/")
    input("Press Enter after installing Python...")
    return False

def get_app_dir():
    """Get application directory"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def download_with_powershell(url, file_path):
    """Download using PowerShell - most reliable on Windows"""
    try:
        print(f"   Downloading from: {url}")
        
        # Use PowerShell Invoke-WebRequest
        ps_command = [
            'powershell', '-Command',
            f'Invoke-WebRequest -Uri "{url}" -OutFile "{file_path}" -UseBasicParsing'
        ]
        
        result = subprocess.run(ps_command, capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                size_mb = os.path.getsize(file_path) / (1024 * 1024)
                print(f"   ✅ Downloaded successfully ({size_mb:.1f}MB)")
                return True
        
        print(f"   ❌ PowerShell download failed: {result.stderr}")
        return False
        
    except Exception as e:
        print(f"   ❌ Download error: {e}")
        return False

def download_ai_engine():
    """Download AI engine from GitHub using PowerShell"""
    app_dir = get_app_dir()
    ai_engine_path = os.path.join(app_dir, 'ai-engine')
    
    if os.path.exists(ai_engine_path):
        print("✅ AI engine already downloaded")
        return ai_engine_path
    
    print("📥 Downloading AI engine from GitHub...")
    
    # GitHub repository files we need
    base_url = "https://raw.githubusercontent.com/CleverKeyush/svarX.ai/master/ai-engine"
    files_to_download = [
        "local-server.py",
        "personalization.py", 
        "model_manager.py",
        "requirements.txt"
    ]
    
    try:
        os.makedirs(ai_engine_path, exist_ok=True)
        
        for file_name in files_to_download:
            print(f"   Downloading {file_name}...")
            file_url = f"{base_url}/{file_name}"
            file_path = os.path.join(ai_engine_path, file_name)
            
            if download_with_powershell(file_url, file_path):
                continue
            else:
                raise Exception(f"Failed to download {file_name}")
        
        print("✅ AI engine downloaded successfully!")
        return ai_engine_path
        
    except Exception as e:
        print(f"❌ Failed to download AI engine: {e}")
        return None

def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing AI dependencies...")
    
    packages = [
        'flask>=2.2.0',
        'flask-cors>=4.0.0', 
        'psutil>=5.9.0',
        'requests>=2.28.0',
        'llama-cpp-python>=0.2.0'
    ]
    
    for package in packages:
        print(f"   Installing {package}...")
        try:
            result = subprocess.run([
                'pip', 'install', package, '--upgrade'
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(f"   ✅ {package} installed")
            else:
                print(f"   ⚠️  {package} failed (will try when server starts)")
                
        except Exception as e:
            print(f"   ⚠️  {package} error: {e}")
    
    print("✅ Dependencies installation completed!")
    return True

def download_model(ai_engine_path):
    """Download AI model using PowerShell"""
    model_dir = os.path.join(ai_engine_path, 'models')
    model_path = os.path.join(model_dir, 'Llama-3.2-3B-Instruct-Q4_K_M.gguf')
    
    if os.path.exists(model_path) and os.path.getsize(model_path) > 1000000:
        size_gb = os.path.getsize(model_path) / (1024**3)
        print(f"✅ AI model already exists: {size_gb:.1f}GB")
        return True
    
    print("🤖 Downloading AI model (~2GB)...")
    print("   This may take 5-10 minutes depending on internet speed")
    
    os.makedirs(model_dir, exist_ok=True)
    
    model_urls = [
        "https://huggingface.co/microsoft/Llama-3.2-3B-Instruct-Q4_K_M-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf"
    ]
    
    for i, model_url in enumerate(model_urls):
        print(f"📥 Trying download source {i+1}/{len(model_urls)}...")
        
        if download_with_powershell(model_url, model_path):
            if os.path.exists(model_path) and os.path.getsize(model_path) > 1000000:
                size_gb = os.path.getsize(model_path) / (1024**3)
                print(f"✅ Model verified: {size_gb:.1f}GB")
                return True
        
        if i < len(model_urls) - 1:
            print("   Trying next source...")
    
    print("\n❌ All download sources failed!")
    print("💡 Manual download instructions:")
    print("   1. Go to: https://huggingface.co/microsoft/Llama-3.2-3B-Instruct-Q4_K_M-GGUF")
    print("   2. Download: Llama-3.2-3B-Instruct-Q4_K_M.gguf")
    print(f"   3. Save to: {model_path}")
    return False

def start_server(ai_engine_path):
    """Start the AI server"""
    server_script = os.path.join(ai_engine_path, 'local-server.py')
    
    print("🚀 Starting AI Server in background...")
    print("🌐 Server URL: http://127.0.0.1:8081")
    
    try:
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        # Run in background without console window
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        
        process = subprocess.Popen(
            ['python', server_script],
            cwd=ai_engine_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            env=env,
            encoding='utf-8',
            errors='replace',
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        print("✅ AI Server started in background!")
        print("🎉 Ready for AI suggestions in your browser!")
        input("\nPress Enter to close this window (server keeps running)...")
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        input("Press Enter to exit...")

def main():
    """Main function"""
    print_header()
    
    # Step 1: Check Python
    if not check_python():
        input("Press Enter to exit...")
        return
    
    # Step 2: Download AI engine
    ai_engine_path = download_ai_engine()
    if not ai_engine_path:
        input("Press Enter to exit...")
        return
    
    # Step 3: Install dependencies
    install_dependencies()
    
    # Step 4: Download model
    if not download_model(ai_engine_path):
        print("❌ Cannot start without AI model")
        input("Press Enter to exit...")
        return
    
    # Step 5: Start server
    print("🎯 Everything ready! Starting server...")
    start_server(ai_engine_path)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        input("Press Enter to exit...")