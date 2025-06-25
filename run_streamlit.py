#!/usr/bin/env python3
"""
Launcher script for the Airbnb Revenue Predictor Streamlit app.
This script installs dependencies and runs the Streamlit application.
"""

import subprocess
import sys
import os
from pathlib import Path

def install_requirements():
    """Install required packages from requirements.txt"""
    print("📦 Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ All packages installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing packages: {e}")
        return False

def run_streamlit():
    """Run the Streamlit app"""
    print("🚀 Starting Streamlit app...")
    print("\n📍 New Feature: Address Validation!")
    print("   - Enter any address in San Francisco, San Mateo, or Santa Clara counties")
    print("   - The app will automatically validate and convert to coordinates")
    print("   - Only supported locations will be accepted for predictions")
    print("\n🌐 The app will open in your default web browser...")
    print("=" * 60)
    
    try:
        # Run Streamlit app
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "src/streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n👋 App stopped by user")
    except Exception as e:
        print(f"❌ Error running Streamlit app: {e}")

def main():
    """Main function"""
    print("🏠 Airbnb Revenue Predictor")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path("requirements.txt").exists():
        print("❌ Error: requirements.txt not found!")
        print("   Please run this script from the project root directory.")
        sys.exit(1)
    
    # Install requirements
    if not install_requirements():
        sys.exit(1)
    
    # Run the app
    run_streamlit()

if __name__ == "__main__":
    main() 