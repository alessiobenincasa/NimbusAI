FROM postgres:13-alpine

# Copy initialization scripts
COPY init/ /docker-entrypoint-initdb.d/

# Set environment variables
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres
ENV POSTGRES_DB=llmchatbot

# Expose the port
EXPOSE 5432

# Set healthcheck
HEALTHCHECK --interval=5s --timeout=5s --retries=3 \
  CMD pg_isready -U postgres -d llmchatbot || exit 1 