# Multi-stage build for Claude Code Orchestrator
FROM golang:1.21-alpine AS builder

# Install dependencies
RUN apk add --no-cache git make

WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build the application
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o orchestrator ./cmd/orchestrator

# Final stage
FROM alpine:latest

# Install ca-certificates for HTTPS
RUN apk --no-cache add ca-certificates

WORKDIR /app

# Copy binary from builder
COPY --from=builder /app/orchestrator .

# Create state directory
RUN mkdir -p /state/claude-orchestrator

# Copy configuration
COPY config/ /app/config/
COPY .env.example /app/.env.example

# Expose port
EXPOSE 8010

# Run the application
CMD ["./orchestrator"]
