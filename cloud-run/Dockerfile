FROM python:3.12-slim
WORKDIR /app
COPY app.py index.html privacy.html healthz.json ./
COPY blog ./blog
ENV PORT=8080
EXPOSE 8080
CMD ["python3", "app.py"]
