FROM python:3.12-slim
#RUN apt-get update && apt-get install -y --no-install-recommends \
#    build-essential curl \
#    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt -c constraints.txt
EXPOSE 5000
# CMD ["python", "app.py"]
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
