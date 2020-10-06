FROM haproxy:1.9-alpine

ENTRYPOINT ["/magic-entrypoint", "/docker-entrypoint.sh"]
CMD ["haproxy", "-f", "/usr/local/etc/haproxy/haproxy.cfg"]

RUN apk add --no-cache python3 &&\
    pip3 install --no-cache-dir dnspython

COPY magic-entrypoint.py /magic-entrypoint

ENV TIMEOUT_CLIENT=5s \
    TIMEOUT_CLIENT_FIN=5s \
    TIMEOUT_CONNECT=5s \
    TIMEOUT_SERVER=5s \
    TIMEOUT_SERVER_FIN=5s \
    TIMEOUT_TUNNEL=5s \
    UDP=0 \
    VERBOSE=0

# Metadata
ARG VCS_REF
ARG BUILD_DATE
LABEL org.label-schema.schema-version="1.0" \
      org.label-schema.license=Apache-2.0 \
      org.label-schema.build-date="$BUILD_DATE" \
      org.label-schema.vcs-ref="$VCS_REF" \
      org.label-schema.vcs-url="https://github.com/gmelillo/docker-tcp-proxy"
