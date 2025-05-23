# Zadanie 1 – Część dodatkowa, wariant 2 (+50 %)

**Podstawowe wymagania:**

1. Wykonano wszystkie punkty części obowiązkowej.
2. Wybrano rozwiązanie wariantu 2: obraz multi-arch (linux/amd64, linux/arm64) z wykorzystaniem cache-to/cache-from.
3. Obraz zweryfikowano narzędziem Trivy.

---

## 1. Konfiguracja Buildx

```bash
export DOCKER_CLI_EXPERIMENTAL=enabled
export DOCKER_BUILDKIT=1
docker buildx create --name zad1bx --driver docker-container --use
docker buildx inspect zad1bx --bootstrap
```

---

## 2. Plik `Dockerfile.multi2`

```dockerfile
# syntax=docker/dockerfile:1.4
FROM python:3.12-alpine AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip wheel -r requirements.txt -w wheels

FROM python:3.12-alpine
LABEL org.opencontainers.image.authors="Paweł Peterwas <s99658@pollub.edu.pl>"
ENV PYTHONUNBUFFERED=1 PORT=8000
WORKDIR /app
COPY requirements.txt .
COPY --from=builder /build/wheels /wheels
RUN pip install --no-index --find-links=/wheels -r requirements.txt \
 && rm -rf /wheels \
 && pip cache purge
COPY app ./app
COPY templates ./templates
EXPOSE ${PORT}
HEALTHCHECK CMD ["python","-c","import http.client,os,sys; c=http.client.HTTPConnection('localhost',int(os.getenv('PORT',8000))); c.request('GET','/'); sys.exit(0) if c.getresponse().status<500 else sys.exit(1)"]
ENTRYPOINT ["python","-m","uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
```

---

## 3. Budowa obrazu z cache

```bash
docker buildx build \
  --builder zadanie1bx \
  --platform linux/amd64,linux/arm64 \
  --file Dockerfile.multi2 \
  --tag pawloxdocker/pogodynka:multi2-alpine \
  --push \
  --cache-to type=registry,ref=pawloxdocker/pogodynka-cache:multi2-alpine,mode=max \
  --cache-to type=inline \
  --cache-from type=registry,ref=pawloxdocker/pogodynka-cache:multi2-alpine \
  --cache-from type=inline \
  .
```

**Fragment logu:**

```
 => => writing config sha256:7f3d1a427aa52800a7c2a4ae646685e7515f31ea  3.6s
 => => writing cache image manifest sha256:729cd1aa98fc2484ffaf565b4b  1.2s
 => [auth] pawloxdocker/pogodynka-cache:pull,push token for registry-  0.0s
```

---

## 4. Weryfikacja multi-arch

```bash
docker buildx imagetools inspect pawloxdocker/pogodynka:multi2-alpine
```

**Manifests:**

```
Manifests:
  Name:        docker.io/pawloxdocker/pogodynka:multi2@sha256:45d007f935c7965e974e1e3750597edcde67d7a7db65c4e7594cbd5842469897
  MediaType:   application/vnd.oci.image.manifest.v1+json
  Platform:    linux/amd64

  Name:        docker.io/pawloxdocker/pogodynka:multi2@sha256:8a7c4db9394086d18f8941bfa4964b234d7e55550ff16a4ae5638f119752ae22
  MediaType:   application/vnd.oci.image.manifest.v1+json
  Platform:    linux/arm64
```

---

## 5. Potwierdzenie cache-hit

```bash
docker buildx build \
  --builder zad1bx \
  --platform linux/amd64,linux/arm64 \
  --file Dockerfile.multi2 \
  --tag pawloxdocker/pogodynka:multi2-test \
  --load \
  --cache-to type=registry,ref=pawloxdocker/pogodynka-cache:multi2-alpine,mode=max \
  --cache-to type=inline \
  --cache-from type=registry,ref=pawloxdocker/pogodynka-cache:multi2-alpine \
  --cache-from type=inline \
  .
```

**Fragment logu:**

```
=> CACHED [linux/amd64 stage-1 2/7] WORKDIR /app                      0.0s
 => CACHED [linux/amd64 stage-1 3/7] COPY requirements.txt .           0.0s
 => CACHED [linux/amd64 builder 2/4] WORKDIR /build                    0.0s
 => CACHED [linux/amd64 builder 3/4] COPY requirements.txt .           0.0s
 => CACHED [linux/amd64 builder 4/4] RUN pip install --upgrade pip  &  0.0s
 => CACHED [linux/amd64 stage-1 4/7] COPY --from=builder /build/wheel  0.0s
 => CACHED [linux/amd64 stage-1 5/7] RUN pip install --no-index --fin  0.0s
 => CACHED [linux/amd64 stage-1 6/7] COPY app ./app                    0.0s
```

---

## 6. Analiza podatności (Trivy)

```bash
trivy image --severity CRITICAL,HIGH pawloxdocker/pogodynka:multi2-alpine
```

> **Wynik:** 1 podatność HIGH, 0 CRITICAL:
>
> * starlette (0.37.2): CVE-2024-47874 – Denial of service (DoS) via multipart/form-data (fixed in 0.40.0)

---

## 7. Uzasadnienie pominięcia CVE

Chociaż w obrazie wykryto jedną lukę **HIGH** (CVE-2024-47874 w bibliotece Starlette), można ją zignorować:

* Aplikacja nie korzysta z parsowania `multipart/form-data`.
* Formularz obsługuje tylko dwa pola tekstowe, bez uploadu plików.

---

## 8. Linki

* Repozytorium GitHub: [https://github.com/pawlox62/pogodynka](https://github.com/pawlox62/pogodynka)
* Docker Hub: [https://hub.docker.com/r/pawloxdocker/pogodynka/tags](https://hub.docker.com/r/pawloxdocker/pogodynka/tags)
