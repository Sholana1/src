# ----------------------------
# Base Python image
# ----------------------------
ARG PYTHON_VERSION=3.13.7
FROM python:${PYTHON_VERSION}-slim-bookworm AS base

# ----------------------------
# Build stage: compile wheels
# ----------------------------
FROM base AS build-stage

# Install build dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY ./backend/requirements.txt .

# Build wheels
RUN pip wheel --wheel-dir /wheels -r requirements.txt --no-cache-dir

# Install runtime Python tools (uvicorn, watchfiles)
RUN pip install --no-cache-dir uvicorn watchfiles

# ----------------------------
# Runtime stage
# ----------------------------
FROM base AS runtime-stage

ARG APP_HOME=/src
ARG APP_USER=fastapi
ARG APP_GROUP=fastapi

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR ${APP_HOME}

# Install runtime system dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
    libpq5 \
    libffi8 \
    libssl3 \
    git \
    nano \
    gettext \
    ssh \
    bash-completion \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*

# Create user
RUN groupadd -r ${APP_GROUP} && useradd -r -g ${APP_GROUP} -d ${APP_HOME} -m ${APP_USER}

# App logs
RUN mkdir -p ${APP_HOME}/backend/app/logs && \
    chown -R ${APP_USER}:${APP_GROUP} ${APP_HOME}/backend/app/logs && \
    chmod 775 ${APP_HOME}/backend/app/logs

# Copy wheels from build stage
COPY --from=build-stage /wheels /wheels/

# Install all wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* && rm -rf /wheels/

# Copy startup scripts
COPY --chown=${APP_USER}:${APP_GROUP} ./backend/docker/local/fastapi/entrypoint.sh /entrypoint.sh
COPY --chown=${APP_USER}:${APP_GROUP} ./backend/docker/local/fastapi/start.sh /start.sh
COPY --chown=${APP_USER}:${APP_GROUP} ./backend/docker/local/fastapi/celery/worker/start.sh /start-celeryworker.sh
COPY --chown=${APP_USER}:${APP_GROUP} ./backend/docker/local/fastapi/celery/beat/start.sh /start-celerybeat.sh
COPY --chown=${APP_USER}:${APP_GROUP} ./backend/docker/local/fastapi/celery/flower/start.sh /start-flower.sh

RUN sed -i 's/\r$//g' /entrypoint.sh /start.sh /start-celeryworker.sh /start-celerybeat.sh /start-flower.sh && \
    chmod +x /entrypoint.sh /start.sh /start-celeryworker.sh /start-celerybeat.sh /start-flower.sh

# Copy application code
COPY --chown=${APP_USER}:${APP_GROUP} . ${APP_HOME}

USER ${APP_USER}

ENTRYPOINT ["/entrypoint.sh"]
