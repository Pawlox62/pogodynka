# Zadanie 2

> Sprawozdanie z realizacji zadania nr 2 (budowa, skanowanie i publikacja obrazu)

![CI status](https://github.com/pawlox62/pogodynka/actions/workflows/build-and-scan.yml/badge.svg)

---

## 1. Założenia zadania

* Zbudować obraz aplikacji z **zadania 1** na podstawie `Dockerfile`.
* Obraz musi wspierać **linux/amd64** i **linux/arm64**.
* W procesie budowy wykorzystywać **cache Buildx** trzymany w publicznym repo na Docker Hub.
* Po zbudowaniu obraz ma zostać opublikowany w **GHCR**.
* Pipeline ma **blokować publikację**, jeśli w skanie CVE wystąpią zagrożenia o poziomie **CRITICAL** lub **HIGH**.
* Całość wykonać w GitHub Actions.

---

## 2. Struktura repozytorium

```
.
├── app/ 
├── templates/ 
├── Dockerfile  
├── Dockerfile.multi2 
├── requirements.txt 
└── .github/
    └── workflows/
        └── build-and-scan.yml 
```

---

## 3. Dockerfile

Najważniejsze elementy:

| Fragment                                      | Cel                                                                                     |
| --------------------------------------------- | --------------------------------------------------------------------------------------- |
| `apt-get dist-upgrade`                        | Natychmiastowa instalacja wszystkich łatek bezpieczeństwa Debiana (usuwa CVE-2025‑4598) |
| Budowanie **wheel‑cache**                     | Szybsze i powtarzalne instalowanie zależności bez internetu w drugim etapie             |
| `pip install --no-index --find-links=/wheels` | Instalacja tylko z lokalnych plików, brak pobierania w stage finalnym                   |
| `pip cache purge` + czyszczenie APT           | Mniejszy rozmiar warstwy                                                                |

---

## 4. Workflow `build-and-scan.yml`

### 4.1 Kluczowe kroki

1. **Checkout** kodu.
2. **QEMU + Buildx** (amd64 + arm64).
3. **Logowanie** do Docker Hub) i GHCR.
4. **Budowa i push** z opcją:

   * `platforms: linux/amd64,linux/arm64`
   * `cache-from / cache-to` → `docker.io/<<user>>/pogodynka-cache:buildcache`
5. **Skan CVE (Trivy)**

   ```bash
   docker run --rm \
     -v /var/run/docker.sock:/var/run/docker.sock \
     -v $HOME/.docker/config.json:/root/.docker/config.json:ro \
     aquasec/trivy:latest image \
     --severity CRITICAL,HIGH \
     --exit-code 1 \
     --ignore-unfixed \
     ghcr.io/pawlox62/pogodynka:${{ github.sha }}
   ```

   * `--exit-code 1` → pipeline zatrzymuje się przy CVE HIGH/CRITICAL.
6. **Verify & finish** – sukces jest tylko, gdy Trivy zwraca kod 0.

### 4.2 Uprawnienia

```yaml
permissions:
  contents: read
  packages: write
```

---

## 5. Strategia tagowania

| Tag                                             | Przeznaczenie                                      | Dlaczego?                                                         |
| ----------------------------------------------- | -------------------------------------------------- | ----------------------------------------------------------------- |
| `ghcr.io/pawlox62/pogodynka:${{ github.sha }}`  | Niezmienny identyfikator konkretnego commita       | Pełna powtarzalność, łatwy rollback                               |
| `ghcr.io/pawlox62/pogodynka:latest`             | Wskazuje na najnowsze udane buildy z gałęzi `main` | Ułatwia „domyślny” pull w środowiskach testowych                  |
| `docker.io/<<user>>/pogodynka-cache:buildcache` | Warstwy Buildx                                     | Dzielona pamięć podręczna dla wszystkich architektur → szybsze CI |

Inspiracja: oficjalna dokumentacja Docker Buildx + tagowanie obrazów skrótem SHA commit. 

---

## 6. Wynik przykładowego uruchomienia

<details>
<summary>Logi Trivy – 0 Vuln HIGH/CRITICAL</summary>

```
Total: 0 (HIGH: 0, CRITICAL: 0)
```

</details>

---

## 7. Jak uruchomić lokalnie

```bash
# pobranie obrazu
docker pull ghcr.io/pawlox62/pogodynka:latest

# start aplikacji na porcie 8000
docker run -p 8000:8000 ghcr.io/pawlox62/pogodynka:latest

# przeglądarka -> http://localhost:8000
```

---

## 8. Autor

Paweł Peterwas  |  [s99658@pollub.edu.pl](mailto:s99658@pollub.edu.pl)

---
