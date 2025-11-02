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

def download_and_install_python():
    """Download and install Python automatically"""
    print("📥 Downloading Python installer...")
    
    # Python 3.11 installer URL (reliable and stable)
    python_url = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    installer_path = os.path.join(os.path.expanduser("~"), "Downloads", "python-installer.exe")
    
    try:
        # Download Python installer using PowerShell
        if download_with_powershell(python_url, installer_path):
            print("✅ Python installer downloaded!")
            
            print("🔧 Installing Python (this may take a few minutes)...")
            print("   Installing with 'Add to PATH' enabled...")
            
            # Install Python silently with PATH addition
            install_command = [
                installer_path,
                '/quiet',
                'InstallAllUsers=1',
                'PrependPath=1',
                'Include_test=0'
            ]
            
            result = subprocess.run(install_command, timeout=300)
            
            if result.returncode == 0:
                print("✅ Python installed successfully!")
                
                # Clean up installer
                try:
                    os.remove(installer_path)
                except:
                    pass
                
                # Refresh PATH by restarting this process
                print("🔄 Restarting to refresh PATH...")
                time.sleep(2)
                subprocess.run([sys.executable] + sys.argv)
                sys.exit(0)
            else:
                print("❌ Python installation failed")
                return False
        else:
            print("❌ Failed to download Python installer")
            return False
            
    except Exception as e:
        print(f"❌ Error installing Python: {e}")
        return False

def check_python():
    """Check if Python is installed, install if missing"""
    print("🔍 Checking Python installation...")
    
    # Try python command
    try:
        result = subprocess.run(['python', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ Python found: {version}")
            return True
    except:
        pass
    
    # Try python3 command
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
    print("🤖 svarX.ai can automatically install Python for you")
    
    choice = input("Install Python automatically? (y/n): ").lower().strip()
    
    if choice == 'y' or choice == 'yes':
        return download_and_install_python()
    else:
        print("💡 Manual installation:")
        print("   1. Go to: https://python.org/downloads/")
        print("   2. Download Python 3.11 or newer")
        print("   3. Run installer and check 'Add to PATH'")
        print("   4. Run this program again")
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
    """Install required Python packages with automatic pip upgrade"""
    print("📦 Installing AI dependencies...")
    
    # First upgrade pip to latest version
    print("   Upgrading pip to latest version...")
    try:
        subprocess.run(['python', '-m', 'pip', 'install', '--upgrade', 'pip'], 
                      capture_output=True, timeout=60)
        print("   ✅ pip upgraded")
    except:
        print("   ⚠️  pip upgrade failed, continuing anyway...")
    
    # Essential packages (must work for basic functionality)
    essential_packages = [
        'flask>=2.2.0',
        'flask-cors>=4.0.0', 
        'psutil>=5.9.0',
        'requests>=2.28.0'
    ]
    
    # Optional packages (AI functionality)
    optional_packages = [
        'llama-cpp-python>=0.2.0',
        'sqlalchemy>=1.4.0',
        'huggingface-hub>=0.16.0'
    ]
    
    failed_essential = []
    
    # Install essential packages
    for package in essential_packages:
        print(f"   Installing {package}...")
        try:
            result = subprocess.run([
                'python', '-m', 'pip', 'install', package, '--upgrade', '--no-cache-dir'
            ], capture_output=True, text=True, timeout=180)
            
            if result.returncode == 0:
                print(f"   ✅ {package} installed successfully")
            else:
                print(f"   ❌ {package} failed: {result.stderr}")
                failed_essential.append(package)
                
        except Exception as e:
            print(f"   ❌ {package} error: {e}")
            failed_essential.append(package)
    
    # Install optional packages (don't fail if these don't work)
    for package in optional_packages:
        print(f"   Installing {package} (optional)...")
        try:
            result = subprocess.run([
                'python', '-m', 'pip', 'install', package, '--upgrade', '--no-cache-dir'
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(f"   ✅ {package} installed successfully")
            else:
                print(f"   ⚠️  {package} failed (will install when server starts)")
                
        except Exception as e:
            print(f"   ⚠️  {package} error (will install when server starts)")
    
    if failed_essential:
        print(f"\n❌ Critical packages failed: {', '.join(failed_essential)}")
        print("💡 Try running as Administrator or check internet connection")
        return False
    else:
        print("✅ Essential dependencies installed successfully!")
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
    """Main function - Complete automatic setup"""
    print_header()
    
    print("🎯 svarX.ai will now set up everything automatically:")
    print("   • Python (if not installed)")
    print("   • AI Engine files")
    print("   • Python libraries") 
    print("   • AI Model (~2GB)")
    print()
    
    # Step 1: Check/Install Python
    print("=" * 50)
    print("STEP 1: Python Setup")
    print("=" * 50)
    if not check_python():
        print("❌ Python setup failed")
        input("Press Enter to exit...")
        return
    
    # Step 2: Download AI engine
    print("\n" + "=" * 50)
    print("STEP 2: AI Engine Download")
    print("=" * 50)
    ai_engine_path = download_ai_engine()
    if not ai_engine_path:
        print("❌ AI Engine download failed")
        input("Press Enter to exit...")
        return
    
    # Step 3: Install dependencies
    print("\n" + "=" * 50)
    print("STEP 3: Python Libraries")
    print("=" * 50)
    if not install_dependencies():
        choice = input("\nSome packages failed. Continue anyway? (y/n): ").lower()
        if choice != 'y':
            return
    
    # Step 4: Download model
    print("\n" + "=" * 50)
    print("STEP 4: AI Model Download")
    print("=" * 50)
    if not download_model(ai_engine_path):
        print("❌ Cannot start without AI model")
        print("💡 You can download it manually and run this again")
        input("Press Enter to exit...")
        return
    
    # Step 5: Start server
    print("\n" + "=" * 50)
    print("STEP 5: Starting AI Server")
    print("=" * 50)
    print("🎉 Setup complete! Starting AI server...")
    start_server(ai_engine_path)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        input("Press Enter to exit...")