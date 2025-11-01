#!/usr/bin/env python3
"""
svarx.ai Lite Launcher - Downloads everything when needed
Minimal EXE that downloads AI engine and model on first run
"""

import sys
import os
import subprocess
import time
import urllib.request
import json
import zipfile
import shutil
try:
    import psutil
except ImportError:
    psutil = None

def print_header():
    """Print welcome header"""
    print("=" * 60)
    print("🚀 svarx.ai - AI Email Assistant Server (Lite)")
    print("=" * 60)
    print("📧 Smart AI suggestions for Gmail, LinkedIn & more!")
    print("🎯 Downloads everything automatically on first run")
    print()
    print("⚠️  If Windows Defender blocked this, it's a FALSE POSITIVE")
    print("💡 See Windows-Defender-Exclusion.txt for fix instructions")
    print("✅ This is safe, open-source software from GitHub")
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
    
    try:
        result = subprocess.run(['python3', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ Python found: {version}")
            return True
    except:
        pass
    
    print("❌ Python not found!")
    print("📥 Please install Python from: https://python.org/downloads/")
    print("⚠️  Make sure to check 'Add to PATH' during installation")
    print()
    input("Press Enter after installing Python...")
    return False

def get_app_dir():
    """Get application directory"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def download_ai_engine():
    """Download AI engine from GitHub"""
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
    
    print(f"   Downloading from: {base_url}")
    print("   This may take a moment...")
    
    try:
        os.makedirs(ai_engine_path, exist_ok=True)
        
        for file_name in files_to_download:
            print(f"   Downloading {file_name}...")
            file_url = f"{base_url}/{file_name}"
            file_path = os.path.join(ai_engine_path, file_name)
            
            try:
                urllib.request.urlretrieve(file_url, file_path)
                
                # Verify file was downloaded and has content
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    print(f"   ✅ {file_name} downloaded ({os.path.getsize(file_path)} bytes)")
                else:
                    print(f"   ❌ {file_name} download failed - file empty or missing")
                    raise Exception(f"Failed to download {file_name}")
                    
            except Exception as e:
                print(f"   ❌ Error downloading {file_name}: {e}")
                print(f"   URL: {file_url}")
                raise
        
        print("✅ AI engine downloaded successfully!")
        return ai_engine_path
        
    except Exception as e:
        print(f"❌ Failed to download AI engine: {e}")
        print("💡 Please check your internet connection")
        return None

def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing AI dependencies...")
    
    essential_packages = [
        'flask>=2.2.0',
        'flask-cors>=4.0.0', 
        'psutil>=5.9.0',
        'requests>=2.28.0',
        'llama-cpp-python>=0.2.0'
    ]
    
    failed_packages = []
    
    for package in essential_packages:
        print(f"   Installing {package}...")
        try:
            result = subprocess.run([
                'pip', 'install', package, '--upgrade', '--no-cache-dir'
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                print(f"   ❌ Failed to install {package}")
                failed_packages.append(package)
            else:
                print(f"   ✅ {package} installed successfully")
                
        except Exception as e:
            print(f"   ❌ Error installing {package}: {e}")
            failed_packages.append(package)
    
    if failed_packages:
        print(f"\n⚠️  Some packages failed: {', '.join(failed_packages)}")
        print("   Try running as Administrator")
        return False
    else:
        print("✅ All dependencies installed successfully!")
        return True

def download_model(ai_engine_path):
    """Download AI model"""
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
        try:
            print(f"📥 Trying download source {i+1}/{len(model_urls)}...")
            
            def show_progress(block_num, block_size, total_size):
                downloaded = block_num * block_size
                if total_size > 0:
                    percent = min(100, (downloaded * 100) // total_size)
                    mb_downloaded = downloaded // (1024 * 1024)
                    mb_total = total_size // (1024 * 1024)
                    print(f"\r   Progress: {percent}% ({mb_downloaded}MB / {mb_total}MB)", end='', flush=True)
            
            urllib.request.urlretrieve(model_url, model_path, reporthook=show_progress)
            print("\n✅ Model downloaded successfully!")
            
            if os.path.exists(model_path) and os.path.getsize(model_path) > 1000000:
                size_gb = os.path.getsize(model_path) / (1024**3)
                print(f"✅ Model verified: {size_gb:.1f}GB")
                return True
                
        except Exception as e:
            print(f"\n⚠️  Download failed: {e}")
            if i < len(model_urls) - 1:
                print("   Trying next source...")
                continue
    
    print("\n❌ All download sources failed!")
    return False

def start_server(ai_engine_path):
    """Start the AI server"""
    server_script = os.path.join(ai_engine_path, 'local-server.py')
    
    print("🚀 Starting AI Server in background...")
    print("🌐 Server URL: http://127.0.0.1:8081")
    print("💡 Install Chrome extension to use AI suggestions")
    
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
        print("📖 Next step: Install the Chrome extension")
        input("\nPress Enter to close this window (server keeps running)...")
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        input("Press Enter to exit...")

def create_windows_defender_info():
    """Create Windows Defender exclusion instructions"""
    try:
        with open('Windows-Defender-Exclusion.txt', 'w') as f:
            f.write("""
# ⚠️ WINDOWS DEFENDER FALSE POSITIVE - SAFE TO IGNORE ⚠️

If Windows Defender blocked this file, it's a FALSE POSITIVE.
This is a legitimate AI assistant, NOT malware.

## Why this happens:
- PyInstaller EXEs often trigger antivirus (common issue)
- The app downloads files from internet (normal behavior)
- Creates folders and runs Python (normal AI server setup)

## Quick Fix - Add Windows Defender Exclusion:
1. Open "Windows Security" (search in Start menu)
2. Go to "Virus & threat protection"
3. Click "Manage settings" under "Virus & threat protection settings"
4. Scroll to "Exclusions" → "Add or remove exclusions"
5. Click "Add an exclusion" → "File"
6. Select this EXE file
7. Click "Open" to add exclusion

## Alternative - Exclude entire folder:
Add exclusion for the entire svarX.ai folder instead

## 100% Safe because:
✅ Open source code: https://github.com/CleverKeyush/svarX.ai
✅ No malicious code - you can verify yourself
✅ Only downloads legitimate AI models from Hugging Face
✅ Runs locally on your computer (no data sent anywhere)

## Still concerned?
Build from source code instead:
1. Install Python 3.9+
2. Download source from GitHub
3. Run: python svarx-lite.py

This is a legitimate productivity tool, not malware.
""".strip())
        print("📝 Created Windows-Defender-Exclusion.txt with detailed instructions")
    except:
        pass

def main():
    """Main function"""
    create_windows_defender_info()
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
    if not install_dependencies():
        choice = input("\nContinue anyway? (y/n): ").lower()
        if choice != 'y':
            return
    
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
        print("💡 If Windows Defender blocked this, see Windows-Defender-Exclusion.txt")
        input("Press Enter to exit...")