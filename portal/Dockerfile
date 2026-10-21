FROM python:3.14.5-alpine3.22@sha256:6b91e66ab2a880ce9ca5a1b91c70f45963ff71ff68268df056336e1a657d5efd AS package
WORKDIR /src
COPY . .
RUN python scripts/package.py

FROM python:3.14.5-alpine3.22@sha256:6b91e66ab2a880ce9ca5a1b91c70f45963ff71ff68268df056336e1a657d5efd
ARG APP_UID=1000
ARG APP_GID=1000
WORKDIR /app
COPY portal/requirements.lock /app/requirements.lock
RUN pip install --no-cache-dir --require-hashes -r requirements.lock
COPY portal /app/portal
COPY scripts/update.py /app/portal/install.py
COPY scripts/install.sh /app/portal/install.sh
COPY scripts/install.ps1 /app/portal/install.ps1
COPY --from=package /src/dist /releases
RUN mkdir -p /data /backups && chown -R ${APP_UID}:${APP_GID} /data /backups /releases
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 BOTTIFACT_DATA=/data
USER ${APP_UID}:${APP_GID}
EXPOSE 8080
CMD ["uvicorn", "portal.app:app", "--host", "0.0.0.0", "--port", "8080", "--no-proxy-headers", "--no-access-log"]
