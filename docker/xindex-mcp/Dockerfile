FROM node:22-bookworm-slim

# Python for the MCP server (stdlib only — no pip deps); supergateway
# (Node) for the stdio→streamableHttp transport bridge so non-Claude-Code
# MCP clients (Obot, the Caddy-fronted /mcp endpoint) can speak HTTP.
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends python3 ca-certificates && \
    npm install -g supergateway && \
    rm -rf /var/lib/apt/lists/* /root/.npm

RUN groupadd -r mcp && useradd -r -g mcp -m -d /home/mcp mcp

COPY app/ /opt/xindex-mcp/app/
RUN chown -R mcp:mcp /opt/xindex-mcp
USER mcp

ENV XINDEX_BASE_URL=http://xindex:8000
ENV XINDEX_HTTP_TIMEOUT=10

EXPOSE 8096

# supergateway converts the python stdio MCP server into streamableHttp on :8096
CMD ["supergateway", "--stdio", "python3 /opt/xindex-mcp/app/server.py", \
     "--outputTransport", "streamableHttp", \
     "--port", "8096", "--cors", "--healthEndpoint", "/healthz"]
