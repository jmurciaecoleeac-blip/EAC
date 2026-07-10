FROM python:3.11-slim

# cairo pour le rendu SVG, fontconfig pour les polices, DejaVu comme police de repli
RUN apt-get update && apt-get install -y --no-install-recommends \
        libcairo2 fontconfig fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md ./
COPY alone ./alone
RUN pip install --no-cache-dir .

# Les templates, polices et rendus vivent dans un volume
ENV ALONE_DATA_DIR=/data
VOLUME /data

EXPOSE 8000
CMD ["alone", "serve", "--host", "0.0.0.0", "--port", "8000"]
