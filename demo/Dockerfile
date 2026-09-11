FROM python:3.12-slim

# installa dipendenze base
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# setta workdir
WORKDIR /app

# copia requirements diretti (puoi anche creare un requirements.txt)
RUN pip install --no-cache-dir flask requests

# copia l’app flask
COPY app.py /app/app.py

# espone la porta flask
EXPOSE 5000

# avvia app
CMD ["python", "app.py"]

