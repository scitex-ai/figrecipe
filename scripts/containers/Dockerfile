# FigRecipe - Docker Container
# Reproducible matplotlib environment with mm-precision layouts
# Build: docker build -t figrecipe -f scripts/containers/Dockerfile .
# Run:   docker run --rm -v $(pwd):/workspace figrecipe python3 script.py

FROM python:3.12-slim

LABEL maintainer="FigRecipe Project"
LABEL description="Reproducible matplotlib wrapper with mm-precision layouts"
LABEL version="1.0.0"

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV MPLBACKEND=Agg

# Install system dependencies for matplotlib rendering
RUN apt-get update && apt-get install -y --no-install-recommends \
    libfreetype6-dev \
    libpng-dev \
    libjpeg-dev \
    pkg-config \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN python3 -m pip install --upgrade pip

# Install figrecipe from source
COPY . /tmp/figrecipe
RUN pip3 install --no-cache-dir /tmp/figrecipe \
    && rm -rf /tmp/figrecipe

WORKDIR /workspace

# Create a non-root user
RUN useradd -m -s /bin/bash figrecipe && \
    chown -R figrecipe:figrecipe /workspace

USER figrecipe

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=1 \
    CMD python3 -c "import figrecipe" || exit 1

CMD ["bash"]

ARG BUILD_DATE
ARG VCS_REF
LABEL org.label-schema.build-date=$BUILD_DATE
LABEL org.label-schema.vcs-ref=$VCS_REF
LABEL org.label-schema.vcs-url="https://github.com/scitex-ai/figrecipe"
LABEL org.label-schema.schema-version="1.0"
