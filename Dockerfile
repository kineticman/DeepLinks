#docker buildx build --platform linux/amd64,linux/arm64 -f Dockerfile -t bnhf/eplustv-ah4c:test . --push --no-cache
FROM alpine:3.20

RUN apk add --no-cache bash curl tzdata ca-certificates python3 py3-pip sqlite-libs

WORKDIR /app

# Copy all scripts into /app (including entrypoint)
COPY espn_scraper.py generate_guide.py hourly.sh nightly_scrape.sh serve_out.py entrypoint.sh ./

# Make shell scripts executable
RUN chmod +x hourly.sh nightly_scrape.sh entrypoint.sh

# Python dependencies
RUN python3 -m pip install --no-cache-dir --break-system-packages requests

# Create shared output folder
RUN mkdir -p /app/out
VOLUME ["/app/out"]

# Defaults (override at runtime)
ENV TZ=US/Mountain
ENV CRON_HOURLY="5 * * * *"
ENV CRON_NIGHTLY="15 3 * * *"

ENTRYPOINT ["/app/entrypoint.sh"]
