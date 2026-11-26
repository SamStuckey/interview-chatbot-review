"""OpenTelemetry setup and plain logging.

Traces go over OTLP HTTP to the local trace viewer. Message content is never
recorded: the agent's instrumentation runs with content capture off, and the
turn span carries counts, IDs and timings only.
"""

import logging

from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

SERVICE_NAME = "capper"


def configure_logging() -> None:
    """Plain stdout logging for startup and unexpected errors."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def create_tracer_provider(otlp_endpoint: str | None, *, app_version: str) -> TracerProvider:
    """A provider exporting to `otlp_endpoint`; with none, spans are created but not exported."""
    provider = TracerProvider(
        resource=Resource.create({"service.name": SERVICE_NAME, "service.version": app_version})
    )
    if otlp_endpoint:
        exporter = OTLPSpanExporter(endpoint=f"{otlp_endpoint.rstrip('/')}/v1/traces")
        provider.add_span_processor(BatchSpanProcessor(exporter))
    return provider
