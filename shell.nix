{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  name = "openrouter-wrapper";

  # Add Python and necessary packages
  buildInputs = [
    pkgs.python312    # Python 3.10 or your preferred version
    pkgs.python312Packages.flask  # Flask web framework
    pkgs.python312Packages.gunicorn  # Gunicorn WSGI server
    pkgs.python312Packages.requests
    #pkgs.python312Packages.gzip
    pkgs.python312Packages.pip    # Python package manager
    pkgs.python312Packages.virtualenv  # Virtual environment tool
  ];

  # Set up environment variables
  FLASK_APP = "wrapper.py";  # Path to your Flask application file

  shellHook = ''
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
      virtualenv venv
    fi

    # Activate virtual environment
    source venv/bin/activate

    # Install dependencies
    if [ -f "requirements.txt" ]; then
      pip install -r requirements.txt
    fi

    echo "Starting Flask app using Gunicorn on localhost:8000..."

    # Function to check for git updates and restart Uvicorn
    check_and_update() {
        git fetch
        if [ "$(git rev-parse HEAD)" != "$(git rev-parse @{u})" ]; then
        echo "Update available. Pulling changes and restarting..."
        git pull
        kill $(pgrep -f "gunicorn")
        sleep 10
        gunicorn --bind 0.0.0.0:2500 --timeout 120 --keep-alive 10 wrapper:app &
        fi
    }

    # Run Flask app with Gunicorn on localhost:2500
    gunicorn --bind 0.0.0.0:2500 --timeout 120 --keep-alive 10 wrapper:app &

    # Run the update check every 30 seconds
    while true; do
        sleep 30
        check_and_update
    done
  '';
}
