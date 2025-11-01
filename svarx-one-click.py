#!/usr/bin/env python3
"""
svarx.ai One-Click Server Launcher
Just double-click to start the AI server - handles everything automatically!
"""

import sys
import os
import subprocess
import time
import urllib.request
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
    print("🎯 One-click setup - handles everything automatically")
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

def find_ai_engine():
    """Find ai-engine folder"""
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
    else:
        exe_dir = os.path.dirname(os.path.abspath(__file__))
    
    possible_paths = [
        os.path.join(exe_dir, 'ai-engine'),
        os.path.join(exe_dir, 'gmail-ai-pro', 'ai-engine'),
        os.path.join(os.path.dirname(exe_dir), 'ai-engine'),
    ]
    
    for path in possible_paths:
        if os.path.exists(os.path.join(path, 'local-server.py')):
            return path
    
    return None

def install_dependencies(ai_engine_path):
    """Install required Python packages"""
    print("📦 Installing AI dependencies...")
    
    requirements_file = os.path.join(ai_engine_path, 'requirements.txt')
    if not os.path.exists(requirements_file):
        print("⚠️  Requirements file not found, installing essential packages...")
        essential_packages = [
            'flask>=2.2',
            'flask-cors>=4.0', 
            'psutil>=5.9',
            'llama-cpp-python>=0.1.37',
            'sqlalchemy>=1.4'
        ]
        
        for package in essential_packages:
            print(f"   Installing {package}...")
            try:
                subprocess.run(['pip', 'install', package], 
                             capture_output=True, timeout=60)
            except:
                print(f"   ⚠️  Failed to install {package}")
        return
    
    try:
        print("   Installing from requirements.txt...")
        result = subprocess.run(['pip', 'install', '-r', requirements_file], 
                              capture_output=True, text=True, timeout=180)
        
        if result.returncode == 0:
            print("✅ Dependencies installed successfully!")
        else:
            print("⚠️  Some dependencies may have failed to install")
            print("   The server will try to run anyway...")
            
    except Exception as e:
        print(f"⚠️  Installation error: {e}")
        print("   The server will try to run anyway...")

def check_model_exists(ai_engine_path):
    """Check if AI model exists"""
    model_path = os.path.join(ai_engine_path, 'models', 'Llama-3.2-3B-Instruct-Q4_K_M.gguf')
    
    if os.path.exists(model_path) and os.path.getsize(model_path) > 1000000:  # > 1MB
        size_gb = os.path.getsize(model_path) / (1024**3)
        print(f"✅ AI model found: {size_gb:.1f}GB")
        return True
    
    return False

def download_model_info():
    """Show model download information"""
    print("🤖 AI Model Setup Required")
    print("   The AI model (Llama-3.2-3B) needs to be downloaded")
    print("   Size: ~2GB | This is a one-time download")
    print()
    print("📥 The model will download automatically when the server starts")
    print("   First startup may take 5-10 minutes depending on internet speed")
    print()

def start_server(ai_engine_path, background_mode=False):
    """Start the AI server"""
    server_script = os.path.join(ai_engine_path, 'local-server.py')
    
    if not background_mode:
        print("🚀 Starting AI Server...")
        print("🌐 Server URL: http://127.0.0.1:8081")
        print("💡 Install Chrome extension to use AI suggestions")
        print("⚡ Press Ctrl+C to stop the server")
        print()
        print("🔄 Server starting...")
    
    try:
        # Start server process with proper encoding
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        if background_mode:
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
            
            # Create status file for background mode
            create_status_file(process.pid)
            print("✅ AI Server started in background!")
            print("🌐 Server URL: http://127.0.0.1:8081")
            print("💡 Server will keep running even if you close this window")
            print("🔍 Check system tray or task manager to stop the server")
            input("\nPress Enter to close this window (server keeps running)...")
            return
        else:
            process = subprocess.Popen(
                ['python', server_script],
                cwd=ai_engine_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                env=env,
                encoding='utf-8',
                errors='replace'
            )
        
        # Monitor server output
        server_ready = False
        try:
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    line = output.strip()
                    print(f"   {line}")
                    
                    # Detect when server is ready
                    if "Running on http://127.0.0.1:8081" in line:
                        server_ready = True
                        print()
                        print("✅ AI SERVER IS RUNNING!")
                        print("🎉 Ready for AI suggestions in your browser!")
                        print("📖 Next step: Install the Chrome extension")
                        print()
                        
        except KeyboardInterrupt:
            print("\n🛑 Shutting down AI server...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            print("👋 Server stopped. Goodbye!")
            
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        print("💡 Try running as Administrator or check Python installation")
        input("Press Enter to exit...")

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

def create_status_file(pid):
    """Create status file to track background server"""
    status_dir = os.path.join(os.path.expanduser("~"), ".svarx-ai")
    os.makedirs(status_dir, exist_ok=True)
    
    status_file = os.path.join(status_dir, "server.status")
    with open(status_file, 'w') as f:
        json.dump({
            "running": True,
            "pid": pid,
            "started_at": time.time(),
            "server_url": "http://127.0.0.1:8081"
        }, f)

def is_server_running():
    """Check if server is already running in background"""
    status_file = os.path.join(os.path.expanduser("~"), ".svarx-ai", "server.status")
    
    if not os.path.exists(status_file):
        return False
    
    try:
        with open(status_file, 'r') as f:
            status = json.load(f)
        
        # Check if process is still running
        import psutil
        if psutil.pid_exists(status.get("pid", 0)):
            return True
        else:
            # Clean up stale status file
            os.remove(status_file)
            return False
    except:
        return False

def stop_background_server():
    """Stop background server"""
    status_file = os.path.join(os.path.expanduser("~"), ".svarx-ai", "server.status")
    
    if not os.path.exists(status_file):
        print("❌ No background server found")
        return False
    
    try:
        with open(status_file, 'r') as f:
            status = json.load(f)
        
        import psutil
        pid = status.get("pid")
        if pid and psutil.pid_exists(pid):
            process = psutil.Process(pid)
            process.terminate()
            process.wait(timeout=5)
            print("✅ Background server stopped")
        
        os.remove(status_file)
        return True
        
    except Exception as e:
        print(f"❌ Error stopping server: {e}")
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
        server_running = is_server_running()
        
        print(f"Windows Startup: {'✅ Enabled' if in_startup else '❌ Disabled'}")
        print(f"Background Server: {'✅ Running' if server_running else '❌ Stopped'}")
        print()
        
        print("Options:")
        print("  1. Toggle Auto-start with Windows")
        if server_running:
            print("  2. Stop Background Server")
        else:
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
                if server_running:
                    stop_background_server()
                else:
                    return "background"  # Always start in background mode
            
            else:
                print("❌ Invalid choice. Please enter 0-2.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Main launcher function"""
    # Check for startup mode
    startup_mode = '--startup' in sys.argv
    
    if startup_mode:
        print("🚀 svarX.ai started with Windows - launching AI server in background...")
        server_mode = "background"
    else:
        print_header()
        
        # Show startup menu first
        server_mode = show_startup_menu()
        if not server_mode:
            return
    
    # Step 1: Check Python
    retry_count = 0
    while not check_python() and retry_count < 3:
        retry_count += 1
        if retry_count >= 3:
            print("❌ Cannot proceed without Python. Exiting...")
            input("Press Enter to exit...")
            return
    
    # Step 2: Find AI engine
    print("🔍 Locating AI engine...")
    ai_engine_path = find_ai_engine()
    if not ai_engine_path:
        print("❌ AI engine folder not found!")
        print("   Make sure this EXE is in the same folder as 'ai-engine'")
        input("Press Enter to exit...")
        return
    
    print(f"✅ AI engine found: {ai_engine_path}")
    
    # Step 3: Install dependencies
    install_dependencies(ai_engine_path)
    
    # Step 4: Check model
    if not check_model_exists(ai_engine_path):
        download_model_info()
    
    # Step 5: Start server
    background_mode = (server_mode == "background")
    if background_mode:
        print("🎯 Everything ready! Starting AI server in background...")
    else:
        print("🎯 Everything ready! Starting AI server...")
    
    time.sleep(1)
    start_server(ai_engine_path, background_mode)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        input("Press Enter to exit...")