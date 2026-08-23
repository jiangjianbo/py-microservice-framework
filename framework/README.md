# Logical Microservice Runtime

Python Logical Microservice Runtime for building microservices that can run in-process or remotely without code changes.

## Features

- Service Contract with Protocol/ABC
- Service Registry with Stevedore
- InProcess and gRPC Transport
- Service Proxy with location transparency
- Interceptor pipeline for cross-cutting concerns
- Lifecycle management
- Dependency Injection
- Litestar integration
- OpenTelemetry support

## Installation

```bash
uv sync
```

## Development

```bash
uv run pytest
uv build
```

## License

MIT