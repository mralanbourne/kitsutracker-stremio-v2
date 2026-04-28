import logging
from app.factory import create_app

#===============
# Set up the basic configuration for the logger
# This ensures that all informational and error messages include a timestamp
#===============
logging.basicConfig(format="%(asctime)s %(message)s")

#===============
# Instantiate the Quart application using the factory pattern
#===============
app = create_app()

if __name__ == "__main__":
    #===============
    # Run the application on all available network interfaces on port 5000
    # Note: In production, Hypercorn is used via Docker instead of this built-in server
    #===============
    app.run(host="0.0.0.0", port=5000)
