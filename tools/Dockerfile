FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends libcairo2 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir cairosvg==2.7.1 pypdf==5.1.0
