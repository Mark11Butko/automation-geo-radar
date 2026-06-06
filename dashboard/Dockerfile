# Use slim python image for lighter build size
FROM python:3.11-slim

# Install system dependencies if any, clean cache
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside container
WORKDIR /app

# Copy application files
COPY app.py /app/app.py

# Install python dependencies directly
RUN pip install --no-cache-dir \
    streamlit \
    pandas \
    folium \
    streamlit-folium \
    plotly \
    sqlalchemy

# Expose Streamlit default port
EXPOSE 8501

# Command to launch Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
