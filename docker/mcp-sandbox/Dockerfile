FROM python:3.13-slim

RUN useradd --create-home --uid 10001 mcp
USER 10001
WORKDIR /home/mcp

# Deployments must extend this image with the approved MCP server packages.
# The execution worker supplies the command and arguments; this image never
# receives host mounts, application credentials, or network access by default.
ENTRYPOINT []
