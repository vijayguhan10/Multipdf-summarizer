import os
import subprocess
import sys
import platform

def create_virtual_environment():
    """Create and set up a virtual environment for the project."""
    
    print("Setting up Multi-PDF Extractor and Summarizer...")
    
    # Check if Python is installed
    python_version = platform.python_version()
    print(f"Python version: {python_version}")
    if int(python_version.split('.')[0]) < 3 or (int(python_version.split('.')[0]) == 3 and int(python_version.split('.')[1]) < 8):
        print("Error: Python 3.8 or higher is required.")
        sys.exit(1)
    
    # Create virtual environment
    print("\nCreating virtual environment...")
    if os.path.exists("venv"):
        print("Virtual environment already exists.")
    else:
        try:
            subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
            print("Virtual environment created successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error creating virtual environment: {e}")
            sys.exit(1)
    
    # Determine activation script based on OS
    if platform.system() == "Windows":
        activate_script = os.path.join("venv", "Scripts", "activate")
        pip_path = os.path.join("venv", "Scripts", "pip")
    else:  # macOS or Linux
        activate_script = os.path.join("venv", "bin", "activate")
        pip_path = os.path.join("venv", "bin", "pip")
    
    # Install dependencies
    print("\nInstalling dependencies...")
    try:
        if platform.system() == "Windows":
            # For Windows, we need to run a separate command
            subprocess.run(f"{pip_path} install -r requirements.txt", shell=True, check=True)
        else:
            # For Unix systems
            subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)
    
    # Create uploads directory if it doesn't exist
    if not os.path.exists(os.path.join("backend", "uploads")):
        os.makedirs(os.path.join("backend", "uploads"))
        print("\nCreated uploads directory.")
    
    # Check for .env file and prompt if not found
    env_path = os.path.join("backend", ".env")
    if not os.path.exists(env_path):
        print("\nNOTE: You need to create a .env file in the backend directory with your AWS and Gemini API credentials.")
        print("Example .env file content:")
        print("----------------------------")
        print("AWS_ACCESS_KEY_ID=your_aws_access_key")
        print("AWS_SECRET_ACCESS_KEY=your_aws_secret_key")
        print("GEMINI_API_KEY=your_gemini_api_key")
        print("----------------------------")
    
    # Print activation instructions
    print("\nSetup completed!")
    print("\nTo activate the virtual environment, run:")
    if platform.system() == "Windows":
        print("  .\\venv\\Scripts\\activate")
    else:
        print("  source venv/bin/activate")
    
    print("\nTo start the backend server:")
    print("  cd backend")
    print("  python app.py")
    
    print("\nTo start the frontend (optional):")
    print("  python -m http.server 9000")

if __name__ == "__main__":
    create_virtual_environment() 