# Build stage
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache git make

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build the application
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o orchestrator ./cmd/orchestrator

# Production stage
FROM alpine:3.19

# Install ca-certificates for HTTPS
RUN apk --no-cache add ca-certificates curl

WORKDIR /app

# Copy the binary from builder
COPY --from=builder /app/orchestrator .

# Copy dashboard assets
COPY --from=builder /app/dashboard ./dashboard

# Copy policy configuration
COPY --from=builder /app/config ./config

# Create state directory
RUN mkdir -p /state/claude-orchestrator

# Non-root user
RUN addgroup -g 1000 orchestrator && \
    adduser -D -u 1000 -G orchestrator orchestrator && \
    chown -R orchestrator:orchestrator /app /state

USER orchestrator

# Expose ports
EXPOSE 8010

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8010/api/status || exit 1

# Run the application
CMD ["./orchestrator"]
