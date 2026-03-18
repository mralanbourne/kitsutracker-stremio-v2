import logging
from app.factory import create_app

logging.basicConfig(format="%(asctime)s %(message)s")


app = create_app()



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)