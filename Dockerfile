FROM python:3.12

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the application into the container.
COPY . /app

# Install the application dependencies.
WORKDIR /app
RUN uv sync --frozen --no-cache

ENV PATH="/app/.venv/bin:$PATH"

CMD ["fastapi", "run", "api/app.py", "--port", "80", "--workers", "1"]
