#!/usr/bin/env python
"""
IPC Debugger - A tool for debugging Inter-Process Communication mechanisms.
This application provides visualization and debugging tools for pipes, message queues,
shared memory, and deadlock detection.
"""

import sys
import tkinter as tk
from ipc_debugger.gui import IPCDebuggerGUI

def main():
    """Main entry point for the application"""
    # Create the main window
    root = tk.Tk()
    
    try:
        # Try to set a nice icon
        root.iconbitmap("ipc_debugger/icon.ico")
    except:
        # Ignore if icon is not available
        pass
    
    # Create the application
    app = IPCDebuggerGUI(root)
    
    # Start the main event loop
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Application terminated by user")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 