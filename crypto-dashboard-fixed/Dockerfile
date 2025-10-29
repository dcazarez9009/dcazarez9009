FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
        gcc \
        g++ \
        postgresql-client \
        procps \
        default-jdk \
        curl && \
    rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME
ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV PATH="$JAVA_HOME/bin:$PATH"

# Set Spark compatibility environment variables
ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3

# Copy requirements and install Python dependencies
COPY requirements-app.txt .
RUN pip install --no-cache-dir -r requirements-app.txt

# Copy application files
COPY . .

EXPOSE ${STREAMLIT_PORT:-8501}

CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]
