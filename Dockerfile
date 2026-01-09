FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends git openssh-client ca-certificates \
 && rm -rf /var/lib/apt/lists/*

RUN apt-get update \
 && apt-get install -y --no-install-recommends git \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py migrate.py run.py ./
COPY migrations ./migrations

EXPOSE 8000
CMD ["python", "run.py"]

# con questo comando avvia il server uvicorn => ora lo fa python
# CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
