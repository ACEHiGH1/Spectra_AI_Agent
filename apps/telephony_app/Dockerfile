FROM vocodedev/vocode:latest

WORKDIR /code

# Install system dependencies including updated SQLite
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install updated SQLite
RUN wget https://www.sqlite.org/2024/sqlite-autoconf-3450100.tar.gz \
    && tar xvfz sqlite-autoconf-3450100.tar.gz \
    && cd sqlite-autoconf-3450100 \
    && ./configure \
    && make \
    && make install \
    && cd .. \
    && rm -rf sqlite-autoconf-3450100* \
    && ldconfig

# Copy dependency files
COPY ./pyproject.toml /code/pyproject.toml
COPY ./poetry.lock /code/poetry.lock

# Install poetry and dependencies
RUN pip install --no-cache-dir --upgrade poetry
RUN poetry config virtualenvs.create false

# Update poetry.lock file and install dependencies
RUN poetry lock
RUN poetry install --only main --no-interaction --no-ansi

# Install ChromaDB and its dependencies
RUN pip install --no-cache-dir chromadb==0.4.22

# Copy application files
COPY . /code/

# Create directory for knowledge store and set permissions
RUN mkdir -p /code/knowledge_store && \
    chmod -R 777 /code/knowledge_store

# Set LD_LIBRARY_PATH
ENV LD_LIBRARY_PATH=/usr/local/lib

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]
