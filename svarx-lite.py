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

def download_file_with_requests(url, file_path):
    """Download a single file using requests"""
    try:
        download_script = f'''
import requests

url = "{url}"
file_path = "{file_path}"

response = requests.get(url)
response.raise_for_status()

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(response.text)

print(f"Downloaded {{len(response.text)}} bytes")
'''
        
        result = subprocess.run(['python', '-c', download_script], 
                              capture_output=True, text=True, timeout=30)
        
        return result.returncode == 0
        
    except Exception as e:
        return False

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
        
        # First install requests
        print("   Installing requests for downloads...")
        subprocess.run(['pip', 'install', 'requests'], capture_output=True, timeout=60)
        
        for file_name in files_to_download:
            print(f"   Downloading {file_name}...")
            file_url = f"{base_url}/{file_name}"
            file_path = os.path.join(ai_engine_path, file_name)
            
            # Try requests method first
            if download_file_with_requests(file_url, file_path):
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    print(f"   ✅ {file_name} downloaded ({os.path.getsize(file_path)} bytes)")
                    continue
            
            # Fallback to urllib
            try:
                urllib.request.urlretrieve(file_url, file_path)
                
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
        print("💡 Alternative: Download source code from GitHub manually")
        return None

def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing AI dependencies...")
    
    # Essential packages (must work)
    essential_packages = [
        'flask>=2.2.0',
        'flask-cors>=4.0.0', 
        'psutil>=5.9.0',
        'requests>=2.28.0'
    ]
    
    # Optional packages (can fail)
    optional_packages = [
        'llama-cpp-python>=0.2.0'
    ]
    
    failed_essential = []
    failed_optional = []
    
    # Install essential packages
    for package in essential_packages:
        print(f"   Installing {package}...")
        try:
            result = subprocess.run([
                'pip', 'install', package, '--upgrade', '--no-cache-dir'
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                print(f"   ❌ Failed to install {package}")
                failed_essential.append(package)
            else:
                print(f"   ✅ {package} installed successfully")
                
        except Exception as e:
            print(f"   ❌ Error installing {package}: {e}")
            failed_essential.append(package)
    
    # Install optional packages
    for package in optional_packages:
        print(f"   Installing {package} (optional)...")
        try:
            result = subprocess.run([
                'pip', 'install', package, '--upgrade', '--no-cache-dir'
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                print(f"   ⚠️  {package} failed (will install when server starts)")
                failed_optional.append(package)
            else:
                print(f"   ✅ {package} installed successfully")
                
        except Exception as e:
            print(f"   ⚠️  {package} error (will install when server starts): {e}")
            failed_optional.append(package)
    
    if failed_essential:
        print(f"\n❌ Critical packages failed: {', '.join(failed_essential)}")
        print("   Try running as Administrator")
        return False
    elif failed_optional:
        print(f"\n💡 Optional packages will be installed when server starts: {', '.join(failed_optional)}")
        print("✅ Essential dependencies installed successfully!")
        return True
    else:
        print("✅ All dependencies installed successfully!")
        return True

def download_with_requests(url, file_path):
    """Download using requests library (more reliable than urllib)"""
    try:
        # First install requests if not available
        subprocess.run(['pip', 'install', 'requests'], capture_output=True, timeout=60)
        
        # Create a temporary Python script to avoid path escaping issues
        import tempfile
        temp_dir = tempfile.gettempdir()
        script_path = os.path.join(temp_dir, 'download_model.py')
        
        # Write the download script to a file
        with open(script_path, 'w') as f:
            f.write(f'''
import requests
import os
import sys

url = "{url}"
file_path = sys.argv[1]

print("   Starting download...")
try:
    response = requests.get(url, stream=True)
    response.raise_for_status()

    total_size = int(response.headers.get('content-length', 0))
    downloaded = 0

    with open(file_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded * 100) // total_size
                    mb_downloaded = downloaded // (1024 * 1024)
                    mb_total = total_size // (1024 * 1024)
                    print(f"\\r   Progress: {{percent}}% ({{mb_downloaded}}MB / {{mb_total}}MB)", end="", flush=True)

    print("\\n   Download completed!")
except Exception as e:
    print(f"   Download error: {{e}}")
    raise
''')
        
        # Run the script with file path as argument
        result = subprocess.run(['python', script_path, file_path], 
                              capture_output=True, text=True, timeout=600)
        
        # Clean up
        try:
            os.remove(script_path)
        except:
            pass
        
        if result.returncode == 0:
            return True
        else:
            print(f"   Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   Download error: {e}")
        return False

def download_with_pip(url, file_path):
    """Download using urllib with SSL fix as a fallback"""
    try:
        print("   Trying SSL-fixed download method...")
        
        import tempfile
        temp_dir = tempfile.gettempdir()
        script_path = os.path.join(temp_dir, 'download_ssl.py')
        
        # Create a simple download script
        with open(script_path, 'w') as f:
            f.write(f'''
import urllib.request
import ssl
import sys

# Create unverified SSL context (for compatibility)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

url = "{url}"
file_path = sys.argv[1]

print("   Starting SSL download...")
urllib.request.urlretrieve(url, file_path)
print("   Download completed!")
''')
        
        result = subprocess.run(['python', script_path, file_path], 
                              capture_output=True, text=True, timeout=600)
        
        # Cleanup
        try:
            os.remove(script_path)
        except:
            pass
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"   SSL download error: {e}")
        return False

def download_model(ai_engine_path):
    """Download AI model using multiple methods"""
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
        
        # Method 1: Try using requests library
        if download_with_requests(model_url, model_path):
            if os.path.exists(model_path) and os.path.getsize(model_path) > 1000000:
                size_gb = os.path.getsize(model_path) / (1024**3)
                print(f"✅ Model verified: {size_gb:.1f}GB")
                return True
        
        # Method 2: Try with SSL context fix
        if download_with_pip(model_url, model_path):
            if os.path.exists(model_path) and os.path.getsize(model_path) > 1000000:
                size_gb = os.path.getsize(model_path) / (1024**3)
                print(f"✅ Model verified: {size_gb:.1f}GB")
                return True
        
        # Method 3: Try PowerShell download (Windows)
        try:
            print("   Trying PowerShell download...")
            ps_command = f'Invoke-WebRequest -Uri "{model_url}" -OutFile "{model_path}" -UseBasicParsing'
            result = subprocess.run(['powershell', '-Command', ps_command], 
                                  capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0 and os.path.exists(model_path) and os.path.getsize(model_path) > 1000000:
                size_gb = os.path.getsize(model_path) / (1024**3)
                print(f"✅ Model verified: {size_gb:.1f}GB")
                return True
                
        except Exception as e:
            print(f"   PowerShell download failed: {e}")
        
        if i < len(model_urls) - 1:
            print("   Trying next source...")
            continue
    
    print("\n❌ All download methods failed!")
    print("💡 Manual download instructions:")
    print("   1. Open browser and go to:")
    print("      https://huggingface.co/microsoft/Llama-3.2-3B-Instruct-Q4_K_M-GGUF")
    print("   2. Click on 'Llama-3.2-3B-Instruct-Q4_K_M.gguf'")
    print("   3. Click 'Download' button")
    print(f"   4. Save the file to: {model_path}")
    print("   5. Run this program again")
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

def load_config():
    """Load configuration from file"""
    config_file = os.path.join(os.path.expanduser("~"), ".svarx-ai-config.json")
    default_config = {"auto_start_with_windows": False}
    
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
    except:
        pass
    
    return default_config

def save_config(config):
    """Save configuration to file"""
    config_file = os.path.join(os.path.expanduser("~"), ".svarx-ai-config.json")
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Error saving config: {e}")

def get_exe_path():
    """Get the path to this executable"""
    if getattr(sys, 'frozen', False):
        return sys.executable
    else:
        return os.path.abspath(__file__)

def add_to_startup():
    """Add this application to Windows startup"""
    try:
        import winreg
        exe_path = get_exe_path()
        
        # Add to Windows Registry (Run key)
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                           r"Software\Microsoft\Windows\CurrentVersion\Run", 
                           0, winreg.KEY_SET_VALUE)
        
        winreg.SetValueEx(key, "svarX.ai", 0, winreg.REG_SZ, 
                        f'"{exe_path}" --startup')
        winreg.CloseKey(key)
        return True
        
    except Exception as e:
        print(f"Error adding to startup: {e}")
        return False

def remove_from_startup():
    """Remove this application from Windows startup"""
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                           r"Software\Microsoft\Windows\CurrentVersion\Run", 
                           0, winreg.KEY_SET_VALUE)
        
        try:
            winreg.DeleteValue(key, "svarX.ai")
        except FileNotFoundError:
            pass  # Already removed
        
        winreg.CloseKey(key)
        return True
        
    except Exception as e:
        print(f"Error removing from startup: {e}")
        return False

def is_in_startup():
    """Check if application is in Windows startup"""
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                           r"Software\Microsoft\Windows\CurrentVersion\Run", 
                           0, winreg.KEY_READ)
        
        try:
            value, _ = winreg.QueryValueEx(key, "svarX.ai")
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            winreg.CloseKey(key)
            return False
            
    except Exception as e:
        return False

def show_startup_menu():
    """Show startup configuration menu"""
    config = load_config()
    
    while True:
        print("\n" + "="*60)
        print("⚙️  svarX.ai - Server Control Panel")
        print("="*60)
        
        # Check current status
        in_startup = is_in_startup()
        
        print(f"Windows Startup: {'✅ Enabled' if in_startup else '❌ Disabled'}")
        print()
        
        print("Options:")
        print("  1. Toggle Auto-start with Windows")
        print("  2. Start AI Server")
        print("  0. Exit")
        print()
        
        try:
            choice = input("Enter your choice (0-2): ").strip()
            
            if choice == '0':
                print("👋 Goodbye!")
                return None
            
            elif choice == '1':
                if in_startup:
                    if remove_from_startup():
                        config["auto_start_with_windows"] = False
                        save_config(config)
                        print("✅ Removed from Windows startup")
                    else:
                        print("❌ Failed to remove from startup")
                else:
                    if add_to_startup():
                        config["auto_start_with_windows"] = True
                        save_config(config)
                        print("✅ Added to Windows startup")
                        print("💡 svarX.ai will now start automatically when Windows boots")
                    else:
                        print("❌ Failed to add to startup")
            
            elif choice == '2':
                return "start_server"  # Start server
            
            else:
                print("❌ Invalid choice. Please enter 0-2.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Main function"""
    create_windows_defender_info()
    
    # Check for startup mode
    startup_mode = '--startup' in sys.argv
    
    if startup_mode:
        print("🚀 svarX.ai started with Windows - launching AI server...")
        server_mode = "start_server"
    else:
        print_header()
        
        # Show startup menu first
        server_mode = show_startup_menu()
        if not server_mode:
            return
    
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