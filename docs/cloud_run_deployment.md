# Google Cloud Run Deployment Guide

This guide describes how to build, deploy, and operate the Personal Finance backend on **Google Cloud Run** using **direct environment variables** (no Google Cloud Secret Manager required).

---

## 1. Architecture on Cloud Run

- **Compute**: Google Cloud Run (fully managed serverless container, autoscaling 0 to N).
- **WSGI Server**: Gunicorn running Python 3.12 with threads and worker timeouts.
- **Database**: Google Cloud SQL for MySQL connected via native Unix socket (`/cloudsql/INSTANCE_CONNECTION_NAME`).
- **Environment Variables & Secrets**: Attached directly to the Cloud Run service environment (via `env.yaml`, `--set-env-vars`, or the Google Cloud Console UI).
- **Static Files**: Pre-collected during build and served efficiently by **WhiteNoise** (no external static bucket needed).
- **File Storage**: Google Cloud Storage bucket for transaction statement uploads.
- **Health Probes**: Unauthenticated `/health/` endpoint for liveness and startup checks.

---

## 2. Prerequisites

1. Install and authenticate the Google Cloud SDK:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```
2. Enable required Google Cloud APIs (Secret Manager is **not** required):
   ```bash
   gcloud services enable \
     run.googleapis.com \
     sqladmin.googleapis.com \
     cloudbuild.googleapis.com \
     artifactregistry.googleapis.com
   ```

---

## 3. Environment Variables & Database Setup

### A. Get Cloud SQL Instance Connection Name
Find your Cloud SQL instance connection name:
```bash
gcloud sql instances describe YOUR_INSTANCE_NAME --format="value(connectionName)"
# Output format: PROJECT_ID:REGION:INSTANCE_NAME
```

### B. Prepare Environment Variables (`env.yaml`)
Copy the template [env.yaml.example](file:///Users/rajith/Documents/Projects/PersonalFinance/PFServer/personalfinance/env.yaml.example) to `env.yaml`:
```bash
cp env.yaml.example env.yaml
```

Fill in your actual production values in `env.yaml`:
```yaml
ENV: "prod"
DEBUG: "False"
SECRET_KEY: "your-secure-random-django-secret-key"
ALLOWED_HOSTS: "*"
CSRF_TRUSTED_ORIGINS: "https://*.a.run.app"

# Database Configuration (Cloud SQL Unix Socket)
DB_NAME: "personalfinance"
DB_USER: "root"
DB_PASSWORD: "YOUR_CLOUD_SQL_PASSWORD"
DB_HOST: "/cloudsql/YOUR_PROJECT_ID:YOUR_REGION:YOUR_INSTANCE_NAME"

# Cloud Storage
BUCKET_NAME: "YOUR_GCS_BUCKET_NAME"
GOOGLE_CLOUD_PROJECT: "YOUR_PROJECT_ID"
```

> [!NOTE]
> `env.yaml` is added to `.gitignore`, `.dockerignore`, and `.gcloudignore` so your secrets will never be committed to Git or baked into the Docker image.

---

## 4. Deploying to Cloud Run

Deploy directly from source using Google Cloud Build with your `env.yaml`:

```bash
gcloud run deploy coincraftservice \
  --source . \
  --region asia-northeast1 \
  --platform managed \
  --allow-unauthenticated \
  --add-cloudsql-instances YOUR_PROJECT_ID:YOUR_REGION:YOUR_INSTANCE_NAME \
  --env-vars-file=env.yaml \
  --min-instances 0 \
  --max-instances 5 \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300
```

### Alternative 1: Using `--set-env-vars` CLI flag
If you prefer not using a YAML file, pass variables inline:
```bash
gcloud run deploy coincraftservice \
  --source . \
  --region asia-northeast1 \
  --platform managed \
  --allow-unauthenticated \
  --add-cloudsql-instances YOUR_PROJECT_ID:YOUR_REGION:YOUR_INSTANCE_NAME \
  --set-env-vars ENV="prod",DEBUG="False",SECRET_KEY="YOUR_KEY",ALLOWED_HOSTS="*",CSRF_TRUSTED_ORIGINS="https://*.a.run.app",DB_NAME="personalfinance",DB_USER="root",DB_PASSWORD="YOUR_PASSWORD",DB_HOST="/cloudsql/YOUR_PROJECT_ID:YOUR_REGION:YOUR_INSTANCE_NAME",BUCKET_NAME="YOUR_BUCKET",GOOGLE_CLOUD_PROJECT="YOUR_PROJECT_ID" \
  --min-instances 0 \
  --max-instances 5 \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300
```

### Alternative 2: Using Google Cloud Console UI
You can also attach or edit environment variables anytime via the browser:
1. Open **Google Cloud Console** > **Cloud Run** > select `coincraftservice`.
2. Click **Edit & Deploy New Revision**.
3. Under the **Variables & Secrets** tab, click **Add Variable** for each setting (`SECRET_KEY`, `DB_PASSWORD`, `DB_HOST`, `DB_USER`, `DB_NAME`, etc.).
4. Under the **Cloud SQL connections** section, ensure your Cloud SQL instance is selected.
5. Click **Deploy**.

---

## 5. Verifying Deployment

Once deployment completes, Cloud Run outputs the service URL (e.g. `https://coincraftservice-xyz-an.a.run.app`).

1. **Verify Health Check**:
   ```bash
   curl https://coincraftservice-xyz-an.a.run.app/health/
   # Expected response:
   # {"status": "healthy", "service": "coincraftservice"}
   ```

2. **Verify Admin Static Files**:
   Navigate to `https://coincraftservice-xyz-an.a.run.app/admin/` to verify that WhiteNoise is serving CSS and JavaScript properly.

3. **Check Cloud Run Logs**:
   ```bash
   gcloud beta run services logs tail coincraftservice --region asia-northeast1
   ```

---

## 6. How Environment Variables Work in Django

- The container entrypoint executes `gunicorn --bind 0.0.0.0:$PORT core.wsgi:application`.
- Django's `core/settings.py` reads from `os.environ` via `python-decouple` (`config(...)`).
- Because Cloud Run injects the attached environment variables directly into the container process's `os.environ`, Django picks them up automatically without requiring API calls or external secret client libraries.
- The Cloud SQL socket (`/cloudsql/PROJECT:REGION:INSTANCE`) is automatically mounted by Cloud Run when `--add-cloudsql-instances` is specified, allowing MySQL to connect via low-latency local Unix socket.
