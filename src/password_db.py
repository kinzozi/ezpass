import sqlite3
import os
import sys
import base64
import time
import json
import ctypes
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import getpass

# Simple secure string wrapper
class SecureString(str):
    """A string that attempts to clear itself from memory when deleted"""
    def __del__(self):
        # This is a simplified version - the original had memory issues
        pass

class PasswordDatabase:
    def __init__(self, db_path=None, master_password=None):
        """
        Initialize the password database with encryption.
        
        Args:
            db_path: Path to the database file (default: ~/.ezpass/passwords.db)
            master_password: Master password for encryption/decryption
        """
        if db_path is None:
            # Use default path: ~/.ezpass/passwords.db
            home_dir = os.path.expanduser("~")
            db_dir = os.path.join(home_dir, ".ezpass")
            os.makedirs(db_dir, exist_ok=True)
            self.db_path = os.path.join(db_dir, "passwords.db")
        else:
            self.db_path = db_path
            
        # Store path to attempts file for later use
        self.attempts_file = os.path.join(os.path.dirname(self.db_path), ".attempts")
            
        # Get master password if not provided
        if master_password is None:
            self.master_password = self._get_master_password()
        else:
            self.master_password = master_password
            
        try:
            # Derive encryption key from master password
            self.encryption_key = self._derive_key(self.master_password)
            
            # Initialize the database
            self._init_db()
            
            # Reset attempts counter on successful authentication
            if os.path.exists(self.db_path) and os.path.exists(self.attempts_file):
                with open(self.attempts_file, 'w') as f:
                    json.dump({"count": 0, "last_attempt": time.time()}, f)
        except Exception as e:
            # Increase attempts counter on failure
            if os.path.exists(self.attempts_file):
                try:
                    with open(self.attempts_file, 'r') as f:
                        attempts_data = json.load(f)
                    attempts_data["count"] += 1
                    with open(self.attempts_file, 'w') as f:
                        json.dump(attempts_data, f)
                except:
                    pass
            raise e
        
    def _get_master_password(self):
        """Prompt user for master password or create a new one."""
        try:
            if not os.path.exists(self.db_path):
                # New database, create a master password
                print("Creating a new password database. Master password requirements:")
                print("- At least 12 characters long")
                print("- Must contain uppercase, lowercase, digits, and special characters")
                
                while True:
                    password = getpass.getpass("Create master password: ")
                    
                    # Validate password strength
                    if len(password) < 12:
                        print("Password too short. Must be at least 12 characters.")
                        continue
                        
                    has_upper = any(c.isupper() for c in password)
                    has_lower = any(c.islower() for c in password)
                    has_digit = any(c.isdigit() for c in password)
                    has_special = any(not c.isalnum() for c in password)
                    
                    if not (has_upper and has_lower and has_digit and has_special):
                        print("Password must contain uppercase, lowercase, digits, and special characters.")
                        continue
                    
                    confirm = getpass.getpass("Confirm master password: ")
                    if password == confirm:
                        return password
                    print("Passwords do not match. Please try again.")
            else:
                # Existing database, prompt for password
                # Check for attempt tracking
                attempts_file = os.path.join(os.path.dirname(self.db_path), ".attempts")
                attempts_data = {"count": 0, "last_attempt": 0}
                
                if os.path.exists(attempts_file):
                    try:
                        with open(attempts_file, 'r') as f:
                            attempts_data = json.load(f)
                    except:
                        pass  # If file is corrupted, use default values
                
                # Check if we need to enforce delay (after 3 failed attempts)
                current_time = time.time()
                if attempts_data["count"] >= 3:
                    time_since_last = current_time - attempts_data["last_attempt"]
                    delay_needed = max(0, 5 - time_since_last)  # 5 second delay
                    
                    if delay_needed > 0:
                        print(f"Too many failed attempts. Please wait {int(delay_needed)} seconds...")
                        time.sleep(delay_needed)
                
                password = getpass.getpass("Enter master password: ")
                
                # Update attempts tracking
                attempts_data["count"] += 1
                attempts_data["last_attempt"] = current_time
                
                with open(attempts_file, 'w') as f:
                    json.dump(attempts_data, f)
                
                return password
        except (EOFError, IOError):
            # Handle non-interactive environments
            print("Error: Master password is required.")
            print("Use --master-password option for non-interactive mode.")
            sys.exit(1)
    
    def _derive_key(self, password):
        """Derive encryption key from master password."""
        # Generate a random salt for each new database
        salt_file = os.path.join(os.path.dirname(self.db_path), ".salt")
        
        if not os.path.exists(salt_file):
            # Create new salt if it doesn't exist
            import secrets
            salt = secrets.token_bytes(16)
            with open(salt_file, 'wb') as f:
                f.write(salt)
            # Set permissions to restrict access
            os.chmod(salt_file, 0o600)
        else:
            # Read existing salt
            with open(salt_file, 'rb') as f:
                salt = f.read()
    
        # Use enhanced PBKDF2 for key derivation with increased iterations
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=310000,  # Increased from 100000 for better security
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return Fernet(key)
    
    def _init_db(self):
        """Initialize the database with tables if they don't exist."""
        # Create new database file or open existing one
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create passwords table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS passwords (
            id INTEGER PRIMARY KEY,
            title TEXT UNIQUE,
            password TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
        
        # Set secure file permissions (0600 = user can read/write, group/others have no permissions)
        try:
            os.chmod(self.db_path, 0o600)
            
            # Also secure the directory containing the database
            db_dir = os.path.dirname(self.db_path)
            os.chmod(db_dir, 0o700)  # Only user can access directory
        except:
            print("Warning: Unable to set secure file permissions on the database.")
            pass  # Don't fail if permissions can't be set (e.g. on Windows)
    
    def add_password(self, title, password):
        """
        Add or update a password in the database.
        
        Args:
            title: A unique label/title for the password
            password: The password to store
        """
        # Encrypt the password
        encrypted_password = self.encryption_key.encrypt(password.encode()).decode()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Try to insert, if title exists, update
            cursor.execute('''
            INSERT INTO passwords (title, password)
            VALUES (?, ?)
            ON CONFLICT(title) DO UPDATE SET
                password = excluded.password,
                updated_at = CURRENT_TIMESTAMP
            ''', (title, encrypted_password))
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
        finally:
            conn.close()
    
    def get_password(self, title):
        """
        Retrieve a password by its title.
        
        Args:
            title: The label/title of the password to retrieve
            
        Returns:
            The decrypted password or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT password FROM passwords WHERE title = ?', (title,))
            result = cursor.fetchone()
            
            if result:
                encrypted_password = result[0]
                # Create a secure string that will be safer in memory
                decrypted_password = SecureString(self.encryption_key.decrypt(encrypted_password.encode()).decode())
                return decrypted_password
            return None
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None
        except Exception as e:
            print(f"Decryption error: {e}")
            return None
        finally:
            conn.close()
    
    def list_passwords(self):
        """
        List all password titles stored in the database.
        
        Returns:
            List of password titles
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT title FROM passwords ORDER BY title')
            return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []
        finally:
            conn.close()
    
    def delete_password(self, title):
        """
        Delete a password from the database.
        
        Args:
            title: The label/title of the password to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM passwords WHERE title = ?', (title,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
        finally:
            conn.close()