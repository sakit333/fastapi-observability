from fastapi import FastAPI
from fastapi.responses import Response
import time
import random
import logging
from pythonjsonlogger import jsonlogger

from prometheus_client import Counter, Histogram, generate_latest

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
import os

tempo_endpoint = os.environ.get("TEMPO_ENDPOINT", "http://tempo:4317")
log_level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
log_path = os.environ.get("LOG_PATH", "/app/logs/app.log")  
log_level = getattr(logging, log_level_str, logging.INFO)

# ---- OpenTelemetry Setup (Tempo) ----
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

otlp_exporter = OTLPSpanExporter(endpoint=tempo_endpoint, insecure=True)
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# ---- Python Logging with JSON and Trace IDs ----
logger = logging.getLogger("app")
logger.setLevel(log_level)

# Create file handler ensuring the directory matches our docker-compose volume (/app/logs)
logHandler = logging.FileHandler(log_path)
logHandler.setLevel(log_level)

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        span = trace.get_current_span()
        if span.is_recording():
            ctx = span.get_span_context()
            # Loki can use these trace_id fields for correlation
            log_record["trace_id"] = format(ctx.trace_id, "032x")
            log_record["span_id"] = format(ctx.span_id, "016x")

formatter = CustomJsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

# ---- Prometheus Metrics ----
REQUEST_COUNT = Counter("request_count", "Total Request Count")
INFO_COUNT = Counter("demo_info_count", "Count of /demo/info requests")
ERROR_COUNT = Counter("demo_error_count", "Count of /demo/error requests")
WORK_DURATION = Histogram("demo_work_duration_seconds", "Duration of /demo/work requests")

app = FastAPI()

@app.get("/")
def read_root():
    with tracer.start_as_current_span("root-span"):
        REQUEST_COUNT.inc()
        time.sleep(0.2)
        logger.info("This is a demo info log, showing a successful operation.")
        return {"message": "Hello Observability 🚀"}

@app.get("/metrics")
def metrics():
    with tracer .start_as_current_span("metrics-span"):
        REQUEST_COUNT.inc()
        time.sleep(0.7)
        logger.info("Metrics requested")
    return Response(generate_latest(), media_type="text/plain")

@app.get("/demo/info")
def demo_info():
    with tracer.start_as_current_span("demo-info-span"):
        INFO_COUNT.inc()
        logger.info("This is a demo info log, showing a successful operation.")
        return {"status": "success", "message": "Info logged safely!", "endpoint": "/demo/info"}

@app.get("/demo/error")
def demo_error():
    with tracer.start_as_current_span("demo-error-span") as span:
        ERROR_COUNT.inc()
        try:
            # Simulate a crash
            1 / 0
        except ZeroDivisionError as e:
            logger.error("A critical error occurred while doing math!", exc_info=True)
            span.record_exception(e)
            # Marking span as error
            span.set_status(Status(StatusCode.ERROR, "Division by zero"))
            return {"status": "error", "message": "Check the logs, something broke!"}

@app.get("/demo/work")
@WORK_DURATION.time()
def demo_work():
    with tracer.start_as_current_span("demo-work-parent-span") as parent_span:
        logger.info("Starting a complex multi-step work process.")
        
        # Step 1
        with tracer.start_as_current_span("demo-work-db-query") as child_span_1:
            logger.info("Querying the database (simulated)...")
            time.sleep(random.uniform(0.1, 0.4))
            child_span_1.set_attribute("db.system", "postgresql")
            child_span_1.set_attribute("db.statement", "SELECT * FROM users")

        # Step 2
        with tracer.start_as_current_span("demo-work-api-call") as child_span_2:
            logger.warning("External API call might be slow today.")
            time.sleep(random.uniform(0.2, 0.8))
            child_span_2.set_attribute("http.url", "https://api.example.com/data")
            
        logger.info("Complex work process finished.")
        return {"status": "success", "message": "Work completed with traces.", "endpoint": "/demo/work"}

@app.get("/test-trace")
def test_trace():
    with tracer.start_as_current_span("test-span"):
        logger.info("Test trace started")
        time.sleep(1)
        logger.info("Test trace finished")
        return {"status": "trace sent"}

@app.on_event("startup")
def startup_event():
    with tracer.start_as_current_span("startup-span") as span:
        logger.info(f"Application started at {time.time()}")
        span.set_attribute("app.start_time", time.time())
        span.set_attribute("app.name", "fastapi-observability")
        span.set_attribute("app.version", "1.0.0")

@app.on_event("shutdown")
def shutdown_event():
    with tracer.start_as_current_span("shutdown-span") as span:
        logger.info(f"Application shutting down at {time.time()}")
        span.set_attribute("app.shutdown_time", time.time())
        span.set_attribute("app.name", "fastapi-observability")
        span.set_attribute("app.version", "1.0.0")