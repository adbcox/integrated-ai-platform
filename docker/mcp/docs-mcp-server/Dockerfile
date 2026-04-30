FROM node:22-bookworm-slim
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends python3 make g++ && \
    npm install -g @arabold/docs-mcp-server supergateway && \
    rm -rf /root/.npm
RUN groupadd -r mcp && useradd -r -g mcp mcp && \
    mkdir -p /data && chown mcp:mcp /data
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
ENV PLAYWRIGHT_BROWSERS_PATH=0
USER mcp
VOLUME ["/data"]
EXPOSE 8093
ENTRYPOINT ["/bin/sh", "-c"]
CMD ["supergateway --stdio 'docs-mcp-server --store-path /data' --outputTransport streamableHttp --port 8093 --cors --healthEndpoint /healthz"]
