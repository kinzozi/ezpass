# EZPass - Simple and Secure Password Manager

EZPass is a command-line password manager that helps you generate, store, and manage your passwords securely.

## Features

- Generate strong, random passwords with customizable options
- Store passwords securely in an encrypted database
- Retrieve passwords quickly when needed
- Copy passwords to clipboard for easy use

## Installation

```bash
# Clone the repository
git clone https://github.com/kinzozi/ezpass.git
cd ezpass

# Install the package
pip install -e .
```

## Usage

```bash
# Generate a new password
ezpass generate

# Generate a password with custom options
ezpass generate --length 20 --no-special

# Store a password
ezpass store example.com myusername

# Retrieve a password
ezpass get example.com

# List all stored accounts
ezpass list
```

## Security

EZPass uses industry-standard encryption to protect your passwords. The password database is encrypted using a master password that only you know.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 