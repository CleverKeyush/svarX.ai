#!/usr/bin/env python3
"""
Clean build script for svarX.ai to avoid Windows Defender false positives
"""

import os
import subprocess
import sys
import shutil

def clean_build():
    """Build EXE with clean settings to avoid antivirus issues"""
    
    print("🧹 Cleaning previous builds...")
    
    # Remove old build artifacts
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    if os.path.exists('svarX.ai.spec'):
        os.remove('svarX.ai.spec')
    
    print("🔨 Building clean EXE...")
    
    # Build with specific flags to avoid false positives
    cmd = [
        'pyinstaller',
        '--onefile',
        '--name', 'svarX.ai',
        '--clean',
        '--noconfirm',
        '--add-data', 'ai-engine;ai-engine',
        '--exclude-module', 'tkinter',
        '--exclude-module', 'matplotlib',
        '--exclude-module', 'numpy',
        '--exclude-module', 'scipy',
        '--exclude-module', 'pandas',
        '--strip',  # Strip debug symbols
        '--noupx',  # Don't use UPX compression (can trigger AV)
        'svarx-one-click.py'
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Build completed successfully!")
        
        # Copy to main directory
        if os.path.exists('dist/svarX.ai.exe'):
            shutil.copy2('dist/svarX.ai.exe', 'svarX.ai.exe')
            print("✅ EXE copied to main directory")
            
            # Show file size
            size_mb = os.path.getsize('svarX.ai.exe') / (1024 * 1024)
            print(f"📦 File size: {size_mb:.1f}MB")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def create_exclusion_info():
    """Create file with Windows Defender exclusion instructions"""
    
    exclusion_text = """
# Windows Defender Exclusion Instructions

If Windows Defender flags svarX.ai.exe as a threat, it's a false positive.
This is common with PyInstaller-built executables.

## To add an exclusion:

1. Open Windows Security (Windows Defender)
2. Go to "Virus & threat protection"
3. Click "Manage settings" under "Virus & threat protection settings"
4. Scroll down to "Exclusions" and click "Add or remove exclusions"
5. Click "Add an exclusion" → "File"
6. Browse and select svarX.ai.exe
7. Click "Open" to add the exclusion

## Alternative: Exclude the entire folder
- Add an exclusion for the entire svarX.ai folder instead of just the EXE

## Why this happens:
- PyInstaller bundles Python with your app, which can look suspicious to antivirus
- The app makes network requests (for AI model downloads)
- It creates files and processes (normal AI server behavior)

## This is safe because:
- Source code is open and available on GitHub
- No malicious code is present
- The app only runs locally on your machine
- All network requests are to legitimate AI model repositories

If you're still concerned, you can build from source code instead of using the pre-built EXE.
"""
    
    with open('Windows-Defender-Exclusion.txt', 'w') as f:
        f.write(exclusion_text.strip())
    
    print("📝 Created Windows-Defender-Exclusion.txt with instructions")

if __name__ == "__main__":
    print("🚀 svarX.ai Clean Build Script")
    print("=" * 50)
    
    if clean_build():
        create_exclusion_info()
        print("\n✅ Build complete!")
        print("💡 If Windows Defender flags the EXE, see Windows-Defender-Exclusion.txt")
    else:
        print("\n❌ Build failed!")
        sys.exit(1)