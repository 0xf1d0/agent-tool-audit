# All base images MUST be supplied by digest by scripts/build_mistral_images.py.
ARG BUN_IMAGE
ARG PYTHON_IMAGE
FROM ${BUN_IMAGE} AS build
ARG FRAMEWORK_COMMIT
ARG FRAMEWORK_VERSION
ENV OPENCODE_VERSION=${FRAMEWORK_VERSION} OPENCODE_CHANNEL=audit
ADD opencode.tar /src/
WORKDIR /src/opencode
RUN bun install --frozen-lockfile
RUN bun run --cwd packages/cli script/build.ts --target=opencode-linux-x64-baseline --skip-install --skip-web-ui

FROM ${PYTHON_IMAGE} AS task-base
RUN apt-get update && apt-get install -y --no-install-recommends graphviz git ripgrep libstdc++6 \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir graphviz==0.20.3 pytest==8.3.4 pytest-json-ctrf==0.3.6
RUN mkdir -p /work && ln -s /work /app
ENV HOME=/tmp/home XDG_DATA_HOME=/tmp/data XDG_CONFIG_HOME=/tmp/config \
    XDG_CACHE_HOME=/tmp/cache XDG_STATE_HOME=/tmp/state
WORKDIR /work
USER 1000:1000

FROM task-base AS agent
ARG FRAMEWORK_COMMIT
LABEL org.opencontainers.image.revision=${FRAMEWORK_COMMIT}
COPY --from=build /src/opencode/packages/cli/dist/cli-linux-x64-baseline/bin/opencode /usr/local/libexec/opencode
COPY --chmod=0755 opencode-launch /usr/local/bin/opencode
COPY opencode.json /etc/opencode/opencode.json
ENV OPENCODE_CONFIG=/etc/opencode/opencode.json OPENCODE_CONFIG_PROJECT_DISABLE=true \
    OPENCODE_DISABLE_AUTOUPDATE=true OPENCODE_DISABLE_MODELS_FETCH=true OPENCODE_DISABLE_FFF=true \
    OPENCODE_DISABLE_FILEWATCHER=true
ENTRYPOINT ["opencode"]

# Controller-only verifier. Never run this target as the acting agent.
FROM task-base AS verifier
COPY verifier /verifier
ENV PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
ENTRYPOINT ["python", "-I", "-m", "pytest", "-c", "/dev/null", "--confcutdir=/verifier", "-p", "no:cacheprovider", "-p", "ctrf", "--ctrf", "/reports/ctrf.json", "/verifier/test_outputs.py", "-rA", "-v"]

# Trusted gateway alone has provider credentials and external connectivity.
FROM ${PYTHON_IMAGE} AS gateway
COPY auditlab /opt/controller/auditlab
COPY gateway.json /opt/controller/gateway.json
ENV PYTHONPATH=/opt/controller PYTHONDONTWRITEBYTECODE=1
WORKDIR /opt/controller
USER 1000:1000
ENTRYPOINT ["python", "-m", "auditlab", "model-gateway", "--config", "/opt/controller/gateway.json", "--out", "/evidence/session", "--host", "0.0.0.0", "--port", "8080", "--execute", "--confirm-free-only"]
