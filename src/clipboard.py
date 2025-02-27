import subprocess
import platform
import threading
import time

def copy_to_clipboard(text, clear_after=30):
    """
    Copy text to system clipboard and optionally clear after a delay.
    
    Args:
        text: The text to copy to clipboard
        clear_after: Seconds after which to clear clipboard (0 to disable)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        system = platform.system()
        
        if system == 'Linux':
            # Try xclip first, then xsel if xclip not available
            try:
                process = subprocess.Popen(['xclip', '-selection', 'clipboard'], 
                                          stdin=subprocess.PIPE)
                process.communicate(input=text.encode())
                return process.returncode == 0
            except FileNotFoundError:
                try:
                    process = subprocess.Popen(['xsel', '--clipboard', '--input'], 
                                              stdin=subprocess.PIPE)
                    process.communicate(input=text.encode())
                    return process.returncode == 0
                except FileNotFoundError:
                    print("Error: xclip or xsel is required for clipboard functionality.")
                    print("Install with: sudo apt-get install xclip or sudo apt-get install xsel")
                    return False
                
        elif system == 'Darwin':  # macOS
            process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
            process.communicate(input=text.encode())
            return process.returncode == 0
            
        elif system == 'Windows':
            # For Windows, use clip.exe
            process = subprocess.Popen(['clip'], stdin=subprocess.PIPE)
            process.communicate(input=text.encode())
            return process.returncode == 0
            
        else:
            print(f"Clipboard functionality not supported on {system}")
            return False
            
    except Exception as e:
        print(f"Error copying to clipboard: {e}")
        return False
        
    # Start a timer to clear the clipboard after the specified delay
    if clear_after > 0:
        def clear_clipboard():
            time.sleep(clear_after)
            try:
                # Copy empty string to clipboard
                copy_to_clipboard("", clear_after=0)
                print(f"Clipboard cleared after {clear_after} seconds")
            except:
                pass
                
        # Start the timer in a daemon thread
        clear_thread = threading.Thread(target=clear_clipboard)
        clear_thread.daemon = True
        clear_thread.start()
        
    return True