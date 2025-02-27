import string
import secrets
import random

def generate_password(length=16, use_lowercase=True, use_uppercase=True, 
                      use_digits=True, use_special=True):
    """
    Generate a secure random password with specified characteristics.
    
    Args:
        length: Length of the password (default: 16)
        use_lowercase: Include lowercase letters (default: True)
        use_uppercase: Include uppercase letters (default: True)
        use_digits: Include digits (default: True)
        use_special: Include special characters (default: True)
        
    Returns:
        A randomly generated password as string
    """
    # Define character sets
    chars = ""
    if use_lowercase:
        chars += string.ascii_lowercase
    if use_uppercase:
        chars += string.ascii_uppercase
    if use_digits:
        chars += string.digits
    if use_special:
        chars += string.punctuation
        
    if not chars:
        raise ValueError("At least one character set must be selected")
        
    # Ensure at least one character from each selected character set
    password = []
    if use_lowercase:
        password.append(secrets.choice(string.ascii_lowercase))
    if use_uppercase:
        password.append(secrets.choice(string.ascii_uppercase))
    if use_digits:
        password.append(secrets.choice(string.digits))
    if use_special:
        password.append(secrets.choice(string.punctuation))
        
    # Fill the rest of the password
    remaining_length = length - len(password)
    password.extend(secrets.choice(chars) for _ in range(remaining_length))
    
    # Shuffle password to avoid predictable pattern
    random.shuffle(password)
    
    return ''.join(password)