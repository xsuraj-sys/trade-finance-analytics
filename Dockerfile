
FROM python:3.9-slim

WORKDIR /app

# Copy requirements FIRST (for caching)
COPY requirements.txt .

# Install dependencies (system level)
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Expose ports
EXPOSE 8000
EXPOSE 8501

# Command to run both (simple approach for demo purposes)
# In production, use separate containers or supervisor.
# Here we use a shell script wrapper.
RUN echo '#!/bin/bash\n\
uvicorn backend.app:app --host 0.0.0.0 --port 8000 & \n\
streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0\n\
' > /app/start.sh && chmod +x /app/start.sh

CMD ["/app/start.sh"]
