#!/usr/bin/env python3
import argparse
import sys
import getpass
import signal
import time
import threading

from password_generator import generate_password
from password_db import PasswordDatabase
from clipboard import copy_to_clipboard

# Global variables
session_timer = None
SESSION_TIMEOUT = 60  # 60 seconds of inactivity

def clear_session(db=None):
    """Clear sensitive data from memory after timeout"""
    print("\nSession timeout reached. Clearing sensitive data from memory.")
    
    # Force Python's garbage collection
    import gc
    if db:
        # Clear master password and encryption key
        if hasattr(db, 'master_password'):
            db.master_password = None
        if hasattr(db, 'encryption_key'):
            db.encryption_key = None
    
    # Force garbage collection
    gc.collect()
    sys.exit(0)
    
def start_session_timer(db=None):
    """Start/reset the session timeout timer"""
    global session_timer
    
    # Cancel existing timer if any
    if session_timer:
        session_timer.cancel()
        
    # Start new timer
    session_timer = threading.Timer(SESSION_TIMEOUT, clear_session, args=[db])
    session_timer.daemon = True
    session_timer.start()

def main():
    parser = argparse.ArgumentParser(
        description="ezpass - Secure password manager for the command line",
        epilog="Examples:\n"
               "  ezpass -g mybank        # Generate a new password for 'mybank'\n"
               "  ezpass -c mybank        # Copy 'mybank' password to clipboard\n"
               "  ezpass -l               # List all stored password titles\n"
               "  ezpass -d mybank        # Delete 'mybank' password",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Add arguments
    parser.add_argument("-g", "--generate", metavar="TITLE", 
                      help="Generate a new password and store it with the given title")
    parser.add_argument("-c", "--copy", metavar="TITLE",
                      help="Copy the password with the given title to clipboard")
    parser.add_argument("-l", "--list", action="store_true",
                      help="List all stored password titles")
    parser.add_argument("-d", "--delete", metavar="TITLE",
                      help="Delete the password with the given title")
    
    # Hidden master password option (for testing/automation)
    parser.add_argument("--master-password", help=argparse.SUPPRESS)
    
    # Clipboard clearing option
    parser.add_argument("--clipboard-timeout", type=int, default=30,
                      help="Seconds before clipboard is cleared (0 to disable)")
    
    # Password generation options
    generation_group = parser.add_argument_group("Password Generation Options")
    generation_group.add_argument("--length", type=int, default=16,
                               help="Length of the generated password (default: 16)")
    generation_group.add_argument("--no-lowercase", action="store_true",
                               help="Exclude lowercase letters")
    generation_group.add_argument("--no-uppercase", action="store_true",
                               help="Exclude uppercase letters")
    generation_group.add_argument("--no-digits", action="store_true",
                               help="Exclude digits")
    generation_group.add_argument("--no-special", action="store_true",
                               help="Exclude special characters")
    
    # Add timeout option
    parser.add_argument("--timeout", type=int, default=60,
                      help=argparse.SUPPRESS)  # Hidden option
                      
    args = parser.parse_args()
    
    # Set session timeout
    global SESSION_TIMEOUT
    SESSION_TIMEOUT = args.timeout

    # Initialize database
    try:
        db = PasswordDatabase(master_password=args.master_password)
        # Start session timeout timer
        start_session_timer(db)
    except Exception as e:
        print(f"Error initializing password database: {e}")
        sys.exit(1)
    
    # Check if no action specified
    if not (args.generate or args.copy or args.list or args.delete):
        parser.print_help()
        sys.exit(0)
    
    # Handle generate command
    if args.generate:
        # Validate title to prevent injection attacks
        title = args.generate
        if len(title) == 0:
            print("Error: Title cannot be empty")
            sys.exit(1)
        if "'" in title or '"' in title or ';' in title or '\\' in title:
            print("Error: Title contains invalid characters")
            sys.exit(1)
        
        # Generate password with specified options
        try:
            password = generate_password(
                length=args.length,
                use_lowercase=not args.no_lowercase,
                use_uppercase=not args.no_uppercase,
                use_digits=not args.no_digits,
                use_special=not args.no_special
            )
            
            # Store the password
            if db.add_password(title, password):
                print(f"Generated and stored password for '{title}'")
                
                # Copy to clipboard with auto-clearing
                if copy_to_clipboard(password, clear_after=args.clipboard_timeout):
                    if args.clipboard_timeout > 0:
                        print(f"Password copied to clipboard (will clear in {args.clipboard_timeout} seconds)")
                    else:
                        print("Password copied to clipboard")
                
                # Show password briefly
                try:
                    show_password = input("Show password? (y/n): ").lower() == 'y'
                    if show_password:
                        print(f"Password: {password}")
                except (EOFError, IOError):
                    # In non-interactive mode, always show the password
                    print(f"Password: {password}")
            else:
                print(f"Failed to store password for '{title}'")
                sys.exit(1)
                
        except Exception as e:
            print(f"Error generating password: {e}")
            sys.exit(1)
    
    # Handle copy command
    elif args.copy:
        # Validate title to prevent injection attacks
        title = args.copy
        if len(title) == 0:
            print("Error: Title cannot be empty")
            sys.exit(1)
        if "'" in title or '"' in title or ';' in title or '\\' in title:
            print("Error: Title contains invalid characters")
            sys.exit(1)
        
        # Retrieve the password
        password = db.get_password(title)
        if password:
            if copy_to_clipboard(password, clear_after=args.clipboard_timeout):
                if args.clipboard_timeout > 0:
                    print(f"Password for '{title}' copied to clipboard (will clear in {args.clipboard_timeout} seconds)")
                else:
                    print(f"Password for '{title}' copied to clipboard")
            else:
                print("Failed to copy to clipboard")
                sys.exit(1)
        else:
            print(f"No password found for '{title}'")
            sys.exit(1)
    
    # Handle list command
    elif args.list:
        passwords = db.list_passwords()
        if passwords:
            print("Stored passwords:")
            for title in passwords:
                print(f"  - {title}")
        else:
            print("No passwords stored yet")
    
    # Handle delete command
    elif args.delete:
        # Validate title to prevent injection attacks
        title = args.delete
        if len(title) == 0:
            print("Error: Title cannot be empty")
            sys.exit(1)
        if "'" in title or '"' in title or ';' in title or '\\' in title:
            print("Error: Title contains invalid characters")
            sys.exit(1)
        
        # Confirm deletion
        confirm = input(f"Are you sure you want to delete the password for '{title}'? (y/n): ")
        if confirm.lower() == 'y':
            if db.delete_password(title):
                print(f"Password for '{title}' deleted")
            else:
                print(f"No password found for '{title}'")
                sys.exit(1)
        else:
            print("Deletion cancelled")

if __name__ == "__main__":
    main()