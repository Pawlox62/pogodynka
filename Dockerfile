# syntax=docker/dockerfile:1.4
# ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder
WORKDIR /build

# ✚ wszystkie security-fixy z Debiana (usuwa CVE-2025-4598)
RUN apt-get update \
 && apt-get dist-upgrade -y --no-install-recommends \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# budujemy wheel-cache
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip wheel -r requirements.txt -w wheels

# ─────────────────────────────────────────────────────────
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PORT=8000
WORKDIR /app

# ✚ update security-fixy również w stage finalnym
RUN apt-get update \
 && apt-get dist-upgrade -y --no-install-recommends \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
COPY --from=builder /build/wheels /wheels
RUN pip install --no-index --find-links=/wheels -r requirements.txt \
 && rm -rf /wheels \
 && pip cache purge

COPY app ./app
COPY templates ./templates

EXPOSE ${PORT}
HEALTHCHECK CMD ["python","-c","import http.client,os,sys;c=http.client.HTTPConnection('localhost',int(os.getenv('PORT',8000)));c.request('GET','/');sys.exit(0) if c.getresponse().status<500 else sys.exit(1)"]
ENTRYPOINT ["python","-m","uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
