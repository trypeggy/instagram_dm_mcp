#!/usr/bin/env python3
"""
Helper script to set up Instagram credentials in a .env file.
"""

import os
import getpass

def setup_env():
    """Interactive setup for Instagram credentials."""
    print("Instagram DM MCP - Environment Setup")
    print("=" * 40)
    print()
    
    # Check if .env already exists
    if os.path.exists('.env'):
        print("⚠️  .env file already exists!")
        overwrite = input("Do you want to overwrite it? (y/N): ").lower().strip()
        if overwrite != 'y':
            print("Setup cancelled.")
            return
    
    # Get credentials
    print("Please enter your Instagram credentials:")
    username = input("Instagram Username: ").strip()
    password = getpass.getpass("Instagram Password: ").strip()
    
    if not username or not password:
        print("❌ Username and password are required!")
        return
    
    # Write to .env file
    env_content = f"""# Instagram Credentials
INSTAGRAM_USERNAME={username}
INSTAGRAM_PASSWORD={password}
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ .env file created successfully!")
        print("🔒 Your credentials are now stored securely in the .env file")
        print("📝 Remember to add .env to your .gitignore if it's not already there")
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")

if __name__ == "__main__":
    setup_env() 