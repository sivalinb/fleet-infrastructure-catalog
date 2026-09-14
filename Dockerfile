FROM python:3.12-slim
WORKDIR /app
COPY requirements.lock pyproject.toml ./
COPY backend ./backend
RUN pip install --no-cache-dir -r requirements.lock && pip install --no-cache-dir --no-deps -e .
COPY . .
RUN useradd --uid 10001 --create-home catalog && mkdir -p /app/.runtime && chown -R catalog:catalog /app
USER catalog
CMD ["python", "gradio_app.py"]
