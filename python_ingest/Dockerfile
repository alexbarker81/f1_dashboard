FROM python:3.9-slim-buster

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Add this line to make the script executable
RUN chmod +x ingest_f1_data.py

CMD ["python", "ingest_f1_data.py"]
