import sys
import shutil
import os
import PyInstaller.__main__

def cleanup_dist_folder():
    """Robust cleanup: kill process, force delete locked files, remove folders."""
    import subprocess
    import time
    
    # Kill any running PREDERBY.exe
    subprocess.run(['taskkill', '/f', '/im', 'PREDERBY.exe'], 
                   capture_output=True, shell=True)
    print("[INFO] Killed any running PREDERBY.exe processes.")
    
    # Wait for unlock
    time.sleep(3)
    
    # Force delete specific locked exe
    exe_path = 'dist/PREDERBY.exe'
    if os.path.exists(exe_path):
        os.system(f'forfiles /p dist /m PREDERBY.exe /c "cmd /c del @path"')
        print("[INFO] Forced delete of PREDERBY.exe.")
    
    # Now rmtree folders
    for folder in ['dist', 'build']:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
                print(f"[INFO] {folder} folder removed successfully.")
            except PermissionError as e:
                print(f"[ERROR] Failed to remove {folder}: {e}")
                raise
            except Exception as e:
                print(f"[ERROR] Error removing {folder}: {e}")
                raise
    
    # Final check
    if os.path.exists('dist/PREDERBY.exe'):
        raise RuntimeError("PREDERBY.exe still locked after cleanup. Check antivirus/processes.")

if __name__ == '__main__':
    cleanup_dist_folder()
    
    print("[INFO] Starting PyInstaller build...")
    PyInstaller.__main__.run([
        'PREDERBY.spec',
        '--clean',
        '--noconfirm'
    ])
    print("[INFO] Build completed successfully.")
