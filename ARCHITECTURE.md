Miravaz Home Lab: Architecture & Context Manifest
=================================================

**Status:** Active **Location:** `C:\miravaz-stack` (Server: Windows 11 Desktop) **Ingress:** Cloudflare Tunnels (`*.miravaz.com`) **Orchestration:** Docker Compose + Watchtower

* * *

🤖 AI Assistant Instructions
----------------------------

**Critical Context for Future Sessions:** If you are an AI assistant reading this file, you are acting as the **Senior DevOps & Software Architect** for the Miravaz Home Lab.

1.  **Framework:** All new microservices **must** be built using **FastAPI** (Python 3.10+).
    
2.  **Deployment Model:** "GitOps-Lite".
    
    *   **Brain:** Code is pushed to GitHub.
        
    *   **Factory:** GitHub Actions builds the Docker Image.
        
    *   **Runner:** Server pulls image via Watchtower.
        
    *   **Constraint:** **We never edit code directly on the server.** We only edit the `docker-compose.yml` configuration.
        
3.  **Infrastructure:**
    
    *   **Network:** All containers run on the `miravaz-net` bridge network.
        
    *   **Ingress:** Public access is **only** via Cloudflare Tunnels. **Do not** suggest opening router ports.
        
    *   **Inter-Service:** Services talk via container names (e.g., `http://commander:8000`).
        

* * *

1\. The Architecture
--------------------

The system follows a "Brain, Factory, Runner" model to ensure the home server remains clean and stable.

### 🧠 The Brain (Dev Machine)

*   **Role:** Development, Code Writing, Local Testing.
    
*   **Tooling:** Antigravity (Python), Docker Desktop (for verification).
    
*   **Repo Structure:** Polyrepo (or Monorepo with distinct service folders).
    
*   **Source of Truth:** GitHub.
    

### 🏭 The Factory (GitHub CI/CD)

*   **Role:** Builds the "sealed package" (Docker Image).
    
*   **Trigger:** Push to `main` (or `master`) branch.
    
*   **Action:** GitHub Actions builds the image using the `Dockerfile` and pushes it to **GHCR** (GitHub Container Registry).
    
*   **Tagging Strategy:** `:latest` is used for the production home lab deployment.
    

### 🏃 The Runner (Home Server)

*   **OS:** Windows 11 Desktop (Docker Desktop).
    
*   **Location:** `C:\miravaz-stack`
    
*   **Configuration:** A single `docker-compose.yml` file manages the entire stack.
    
*   **Updates:** `Watchtower` runs as a service, checking for new images every 5 minutes and restarting containers automatically.
    
### 👁️ Observability Stack (New)

*   **Collector/UI:** `jaeger` container (All-in-One).
    
*   **Protocol:** OTLP gRPC (http://jaeger:4317).
    
*   **Internal Endpoint:** http://jaeger:4317 (For services to send data).
    
*   **Public URL:** https://trace.miravaz.com (For viewing data).
    
### 🚪 The Gateway (Cloudflare)

*   **Role:** Secure Public Ingress.
    
*   **Component:** `cloudflared` container running inside the stack.
    
*   **Routing Path:** `User` → `https://api.miravaz.com` → `Cloudflare Edge` → `cloudflared (Tunnel)` → `commander:8000`
    

* * *

2\. Service Registry & Naming
-----------------------------

We use a Functional naming strategy.

Service | Docker Name | Port (Internal) | Public URL | Description
--- | --- | --- | --- | ---
Commander | commander | 8000 | api.miravaz.com | Central API dashboard.
Trace UI | jaeger | 16686 | trace.miravaz.com | Jaeger Observability UI.
Tunnel | cloudflared | N/A | N/A | Secure connection to Cloudflare.
Watchtower | watchtower | N/A | N/A | Auto-updates containers.

* * * 

3\. Standard Tech Stack ("The Golden Path")
-------------------------------------------

All new services must adhere to these standards.

| **Component** | **Standard** | **Notes** |
| --- | --- | --- |
 **Language** | Python 3.10+ | Use `python:3.10-slim` for base images. |
 **Web Framework** | **FastAPI** | Mandatory. |
 **Server** | Uvicorn | Standard ASGI server. |
 **Validation** | Pydantic | Strict typing for all data models. |
 **Observability** | OpenTelemetry | opentelemetry-instrumentation-fastapi |
 **Transport** | OTLP gRPC | Endpoint: http://jaeger:4317 |
 **Logging** | JSON | Structured logging for future ingestion. |

* * *

4\. Workflow: Creating a New API
--------------------------------

**Scenario:** Creating a new service called **"Sentinel"** (`miravaz-sentinel`).

### Phase A: Local Dev (The Brain)

1.  **Initialize:** Create folder/repo `miravaz-sentinel`.
    
2.  **Boilerplate Files:**
    
    *   **`main.py`**:
        
        Python
        
            from fastapi import FastAPI
            app = FastAPI(title="Miravaz Sentinel")
            
            @app.get("/")
            def health():
                return {"status": "online", "service": "sentinel"}
        
    *   **`requirements.txt`**:
        
        Plaintext
        
            fastapi
            uvicorn
            pydantic
        
    *   **`Dockerfile`** (Standard):
        
        Dockerfile
        
            FROM python:3.10-slim
            WORKDIR /app
            COPY requirements.txt .
            RUN pip install --no-cache-dir -r requirements.txt
            COPY main.py .
            # CMD is handled by docker-compose, but good to have default:
            CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
        
3.  **Test:** Verify locally using `uvicorn main:app --reload`.
    

### Phase B: CI/CD Setup (The Factory)

1.  **Push:** Push code to GitHub repository `miravaz-sentinel`.
    
2.  **Secrets:** Ensure `GHCR_PAT` is added to Repo Secrets.
    
3.  **Workflow:** Copy the standard `.github/workflows/deploy.yml` file (ensure branch is `main`).
    

### Phase C: Server Registration (The Runner)

_This is the ONLY manual step on the server._

1.  Open `C:\miravaz-stack\docker-compose.yml`.
    
2.  Add the new service block. **Note:** Always map internal port `8000` to a unique Host Port if you want local LAN access, or keep it internal only.
    
    YAML
    
        sentinel:
          image: ghcr.io/pedromiravaz/miravaz-sentinel:latest
          container_name: sentinel
          restart: always
          command: uvicorn main:app --host 0.0.0.0 --port 8000
          networks:
            - miravaz-net
          # Optional: Only needed if you want to access http://localhost:8001 on the server
          ports:
            - "8001:8000"
    
3.  Run: `docker-compose up -d`.
    

### Phase D: Ingress (The Gateway)

1.  **Cloudflare Dashboard:** Access > Tunnels > Config > Public Hostname.
    
2.  **Add Route:** `sentinel.miravaz.com` → `http://sentinel:8000`.
    

* * *

5\. Troubleshooting Checklist
-----------------------------

If a service is **Restating / Crashing**:

1.  **Check Config:** Did you forget the `command:` line in `docker-compose.yml`?
    
2.  **Check Volume:** Did you leave a broken `volumes:` mount pointing to a file that doesn't exist?
    
3.  **Check Logs:** Run `docker logs [container_name]`.
    

* * *