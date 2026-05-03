FROM netdata/netdata:stable

# Disable alarm streaming for read-only mode
ENV NETDATA_DISABLE_ALARM_STREAMING=1

# Expose Prometheus metrics exporter port
EXPOSE 19999

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:19999/api/v1/prometheus.metrics || exit 1
