# We use the slim python 3.11 image to keep the container footprint small
#===============
# A smaller base image reduces the attack surface and speeds up the
# deployment times on PaaS providers like Koyeb.
#===============
FROM python:3.11-slim

WORKDIR /app

# We install requirements first to leverage Docker's layer caching mechanism
#===============
# This ensures that rebuilding the container is extremely fast if the
# requirements.txt has not been modified.
#===============
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8000
EXPOSE 8000

# We use hypercorn as the ASGI server to run the Quart framework efficiently
#===============
# Hypercorn is built for modern asynchronous python web applications.
#===============
CMD ["hypercorn", "run:app", "--bind", "0.0.0.0:8000"]
