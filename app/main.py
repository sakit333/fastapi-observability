from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import Response, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
import time
import random
import logging
from pythonjsonlogger import jsonlogger
import asyncio

import httpx

from prometheus_client import Counter, Histogram, generate_latest

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

import os
from pathlib import Path

# Import config first to set up environment
import config as config_module
from config import settings
from db import get_db, redis_client, engine, Base
from models import User, Product
from schema import SignupRequest, LoginRequest, TokenResponse, UserResponse
from auth import create_access_token, get_current_user, blacklist_token
import os
import uuid
# lgtm realtime practice: python/fastapi-logging-tracing
from prometheus_client import Counter

# print("PWD:", os.getcwd())
# print("FILES:", os.listdir("."))
# print("TEMPLATES EXISTS:", os.path.exists("templates"))
# Ensure log directory exists
log_dir = Path(settings.LOG_PATH).parent
log_dir.mkdir(parents=True, exist_ok=True)

tempo_endpoint = settings.TEMPO_ENDPOINT
log_level_str = settings.LOG_LEVEL
log_path =  settings.LOG_PATH 
log_level = getattr(logging, log_level_str, logging.INFO)

# ---- OpenTelemetry Setup (Tempo) ----
# Define the resource
resource = Resource(attributes={
    SERVICE_NAME: "fastapi-observability"
})
# Set up the tracer provider with the resource
trace.set_tracer_provider(TracerProvider(resource=resource))
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

# Templates
templates = Jinja2Templates(directory="./templates")

USER_REQUEST_COUNT = Counter(
    "user_request_count",
    "Requests per user",
    ["user_id"]
)

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)

        # Rename level
        if "levelname" in log_record:
            log_record["level"] = log_record.pop("levelname")

        # Add clean message field
        log_record["message"] = record.getMessage()

        # Add trace info
        span = trace.get_current_span()
        if span.is_recording():
            ctx = span.get_span_context()
            log_record["trace_id"] = format(ctx.trace_id, "032x")
            log_record["span_id"] = format(ctx.span_id, "016x")

# formatter = CustomJsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
formatter = CustomJsonFormatter(
    '%(asctime)s %(levelname)s %(name)s %(message)s',
    rename_fields={"levelname": "level"}
)
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

# ---- Prometheus Metrics ----
REQUEST_COUNT = Counter("request_count", "Total Request Count")
INFO_COUNT = Counter("demo_info_count", "Count of /demo/info requests")
ERROR_COUNT = Counter("demo_error_count", "Count of /demo/error requests")
WORK_DURATION = Histogram("demo_work_duration_seconds", "Duration of /demo/work requests")

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
# Middleware for logging and tracing
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    with tracer.start_as_current_span(f"http-{request.method}-{request.url.path}") as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", str(request.url))
        span.set_attribute("request_id", request_id)
        start_time = time.time()
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            span.set_attribute("http.status_code", response.status_code)
            logger.info(
                "Request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration": process_time
                }
            )
            # span.set_attribute("http.response_time", process_time)
            # logger.info(f"Request: {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.2f}s")
            return response
        except Exception:
            logger.error(
                "Request failed",
                exc_info=True,
                extra={"request_id": request_id}
            )
            raise
        # except Exception as e:
        #     logger.error("An error occurred while processing the request", exc_info=True)
        #     raise e
        

# Simulated payment flow with multiple spans, attributes, and error handling to demonstrate tracing and logging in a realistic scenario

@app.get("/phonepe/payment/{amount}")
def payment_simulation(amount: float):
    with tracer.start_as_current_span("payment-api-span") as parent_span:
        trace_id = format(parent_span.get_span_context().trace_id, "032x")
        REQUEST_COUNT.inc()

        logger.info(f"Payment request received | amount={amount} | trace_id={trace_id}")

        try:
            # Step 1: Validate payment
            with tracer.start_as_current_span("validate-payment") as validate_span:
                validate_span.set_attribute("payment.amount", amount)
                validate_span.set_attribute("service.type", "payment-processing")
                time.sleep(random.uniform(0.1, 0.7))
                logger.info("Payment validation completed")

            # Step 2: Call PhonePe (external service simulation)
            phonepe_response = call_phonepe_service(amount)

            # Step 3: Final processing
            with tracer.start_as_current_span("finalize-payment") as finalize_span:
                finalize_span.set_attribute("service.type", "payment-processing")
                finalize_span.set_attribute("payment.amount", amount)
                time.sleep(random.uniform(0.1, 0.4))
                logger.info("Payment finalized successfully")

            return {
                "status": "success",
                "trace_id": trace_id,
                "phonepe_status": phonepe_response
            }

        except Exception as e:
            ERROR_COUNT.inc()
            logger.error(f"Payment failed | error={str(e)} | trace_id={trace_id}")
            raise HTTPException(status_code=500, detail=f"Payment failed | trace_id={trace_id}")

def call_phonepe_service(amount: float):
    with tracer.start_as_current_span("phonepe-service") as span:
        # Add attributes (VERY IMPORTANT for tracing)
        span.set_attribute("service.name", "phonepe")
        span.set_attribute("payment.amount", amount)

        logger.info(f"Calling PhonePe service | amount={amount}")

        # Simulate latency
        time.sleep(random.uniform(0.3, 0.8))

        # Simulate success/failure
        if random.choice([True, False]):
            logger.info("PhonePe payment success")
            return "success"
        else:
            logger.error("PhonePe payment failed")
            raise Exception("PhonePe service error")


# swiggy order flow simulation with multiple spans and error handling

@app.get("/swiggy/order/{user_id}/{amount}")
def swiggy_order_flow(user_id: int, amount: float):
    with tracer.start_as_current_span("swiggy-order-flow") as parent_span:
        parent_span.set_attribute("app.service", "swiggy")
        parent_span.set_attribute("app.component", "order-service")
        parent_span.set_attribute("user.id", user_id)
        parent_span.set_attribute("payment.amount", amount)
        trace_id = format(parent_span.get_span_context().trace_id, "032x")
        REQUEST_COUNT.inc()

        logger.info(f"Order received | user_id={user_id} | trace_id={trace_id}")

        try:
            # Step 1: Order Confirmation
            with tracer.start_as_current_span("order-confirmation") as confirm_span:
                confirm_span.set_attribute("user.id", user_id)
                confirm_span.set_attribute("payment.amount", amount)
                time.sleep(random.uniform(0.1, 0.3))
                logger.info("Order confirmed")

            # Step 2: Food Preparation
            with tracer.start_as_current_span("food-preparation") as prep_span:
                prep_span.set_attribute("user.id", user_id)
                prep_span.set_attribute("payment.amount", amount)
                prep_time = random.uniform(0.5, 1.5)
                time.sleep(prep_time)
                logger.info(f"Food preparation completed in {prep_time:.2f}s")

            # Step 3: Food Ready
            with tracer.start_as_current_span("food-ready") as ready_span:
                ready_span.set_attribute("user.id", user_id)
                ready_span.set_attribute("payment.amount", amount)
                time.sleep(0.2)
                logger.info("Food is ready for pickup")

            # Step 4: Assign Delivery Partner
            with tracer.start_as_current_span("assign-delivery-partner") as assign_span:
                assign_span.set_attribute("user.id", user_id)
                assign_span.set_attribute("payment.amount", amount)
                time.sleep(random.uniform(0.2, 0.5))
                partner_id = random.randint(1000, 9999)
                logger.info(f"Delivery partner assigned | partner_id={partner_id}")

            # Step 5: Delivery in Progress
            with tracer.start_as_current_span("delivery-in-progress") as delivery_span:
                delivery_span.set_attribute("user.id", user_id)
                delivery_span.set_attribute("payment.amount", amount)
                delivery_time = random.uniform(0.5, 1.5)
                time.sleep(delivery_time)
                logger.info(f"Delivery in progress | ETA={delivery_time:.2f}s")

            # Step 6: Delivered
            with tracer.start_as_current_span("order-delivered") as delivered_span:
                delivered_span.set_attribute("user.id", user_id)
                delivered_span.set_attribute("payment.amount", amount)
                time.sleep(0.2)
                logger.info("Order delivered successfully")

            # Step 7: Payment
            payment_status = process_payment(amount)

            return {
                "status": "completed",
                "trace_id": trace_id,
                "payment_status": payment_status
            }

        except Exception as e:
            ERROR_COUNT.inc()
            logger.error(f"Order failed | error={str(e)} | trace_id={trace_id}")
            raise HTTPException(status_code=500, detail=f"Order failed | trace_id={trace_id}")
        
def process_payment(amount: float):
    with tracer.start_as_current_span("payment-service") as span:
        span.set_attribute("service.name", "phonepe")
        span.set_attribute("payment.amount", amount)

        logger.info(f"Processing payment | amount={amount}")

        time.sleep(random.uniform(0.3, 0.7))

        if random.choice([True, True, False]):  # more success rate
            logger.info("Payment successful")
            return "success"
        else:
            logger.error("Payment failed")
            raise Exception("Payment failure")
        
# User metric endpoint to demonstrate user-specific metrics and tracing

@app.get("/demo/user-metric/{user_id}")
def user_metric(user_id: str):
    with tracer.start_as_current_span("user-metric-span") as span:
        trace_id = format(span.get_span_context().trace_id, "032x")
        USER_REQUEST_COUNT.labels(user_id=user_id).inc()
        logger.info("User metric recorded", extra={"user_id": user_id, "trace_id": trace_id, "endpoint": f"/demo/user-metric/{user_id}"})
        return {"user_id": user_id, "trace_id": trace_id, "endpoint": f"/demo/user-metric/{user_id}"}

@app.get("/demo/tenant/{tenant_id}")
def tenant_demo(tenant_id: str):
    with tracer.start_as_current_span("tenant-span") as span:
        span.set_attribute("tenant.id", tenant_id)
        trace_id = format(span.get_span_context().trace_id, "032x")
        logger.info(
            "Tenant request",
            extra={"tenant_id": tenant_id, "trace_id": trace_id, "endpoint": f"/demo/tenant/{tenant_id}"}
        )

        return {"tenant": tenant_id, "trace_id": trace_id, "endpoint": f"/demo/tenant/{tenant_id}"}

@app.get("/demo/load")
async def generate_load():
    with tracer.start_as_current_span("load-test-span") as span:
        trace_id = format(span.get_span_context().trace_id, "032x")
        tasks = []
        for _ in range(50):
            tasks.append(asyncio.sleep(random.uniform(0.1, 0.5)))
        await asyncio.gather(*tasks)

        logger.warning("Load spike generated")
        return {"status": "load generated", "trace_id": trace_id, "endpoint": "/demo/load"}

@app.get("/demo/background")
async def background_task():
    async def task():
        with tracer.start_as_current_span("background-job") as span:
            trace_id = format(span.get_span_context().trace_id, "032x")
            logger.info("Background job started")
            await asyncio.sleep(2)
            logger.info("Background job finished")

    asyncio.create_task(task())

    return {"status": "background job started", "trace_id": task.trace_id, "endpoint": "/demo/background"}

@app.get("/demo/dependency-failure")
async def dependency_failure():
    with tracer.start_as_current_span("dependency-call") as span:
        trace_id = format(span.get_span_context().trace_id, "032x")
        try:
            async with httpx.AsyncClient(timeout=1) as client:
                await client.get("https://httpbin.org/delay/3")
        except Exception as e:
            logger.error("External dependency failed", exc_info=True)
            raise HTTPException(status_code=502, detail=f"Dependency failure and trace_id: {trace_id}")

        return {"status": "ok", "trace_id": trace_id, "endpoint": "/demo/dependency-failure"}

@app.get("/demo/cache/{key}")
async def cache_demo(key: str):
    with tracer.start_as_current_span("cache-span") as span:
        trace_id = format(span.get_span_context().trace_id, "032x")
        value = await redis_client.get(key)

        if value:
            span.set_attribute("cache.hit", True)
            logger.info("Cache hit", extra={"key": key})
            return {"key": key, "value": value, "cache": "hit", "trace_id": trace_id, "endpoint": f"/demo/cache/{key}"}

        await redis_client.set(key, "cached_value", ex=60)
        span.set_attribute("cache.hit", False)
        logger.warning("Cache miss", extra={"key": key})

        return {"key": key, "value": "cached_value", "cache": "miss", "trace_id": trace_id, "endpoint": f"/demo/cache/{key}"}

@app.get("/demo/alert")
def trigger_alert():
    with tracer.start_as_current_span("alert-span") as span:
        trace_id = format(span.get_span_context().trace_id, "032x")
        for _ in range(20):
            ERROR_COUNT.inc()

        logger.critical("Alert condition triggered!")
        return {"status": "alert triggered", "trace_id": trace_id, "endpoint": "/demo/alert"}
    
@app.get("/demo/retry")
async def retry_demo(attempt: int = 1):
    with tracer.start_as_current_span("retry-span") as span:
        span.set_attribute("retry.attempt", attempt)
        trace_id = format(span.get_span_context().trace_id, "032x")

        if attempt < 3:
            logger.warning(f"Retry attempt {attempt}")
            raise HTTPException(status_code=500, detail=f"Retry needed and trace_id: {trace_id}")

        return {"status": "success after retry", "trace_id": trace_id, "endpoint": "/demo/retry"}

@app.get("/demo/session")
def session_demo(request: Request):
    session_id = request.headers.get("X-Session-ID", str(uuid.uuid4()))

    with tracer.start_as_current_span("session-span") as span:
        span.set_attribute("session.id", session_id)
        trace_id = format(span.get_span_context().trace_id, "032x")

        logger.info(
            "Session activity",
            extra={"session_id": session_id}
        )

        return {"session_id": session_id, "trace_id": trace_id, "endpoint": "/demo/session"}

# Demo endpoints
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    REQUEST_COUNT.inc()
    await asyncio.sleep(0.2)

    with tracer.start_as_current_span("root-span") as span:
        trace_id = format(span.get_span_context().trace_id, "032x")
        span.set_attribute("demo.endpoint", "/")
        logger.info("Root endpoint accessed", extra={"trace_id": trace_id})
        logger.info("This is a demo info log")

    return templates.TemplateResponse(
        request,               # ✅ FIRST
        "index.html",          # ✅ SECOND
        {"request": request}   # ✅ THIRD
    )

@app.get("/metrics")
def metrics():
    with tracer .start_as_current_span("metrics-span") as span:
        trace_id = format(span.get_span_context().trace_id, "032x")
        REQUEST_COUNT.inc()
        time.sleep(0.7)
        logger.info("Metrics requested", extra={"trace_id": trace_id})
    return Response(generate_latest(), media_type="text/plain")

@app.get("/demo/info")
def demo_info():
    with tracer.start_as_current_span("demo-info-span") as span:
        trace_id = format(span.get_span_context().trace_id, "032x")
        INFO_COUNT.inc()
        logger.info("This is a demo info log, showing a successful operation.")
        return {"status": "success", "message": "Info logged safely!", "trace_id": trace_id, "endpoint": "/demo/info"}

@app.get("/demo/error")
def demo_error():
    with tracer.start_as_current_span("demo-error-span") as span:
        trace_id = format(span.get_span_context().trace_id, "032x")
        ERROR_COUNT.inc()
        try:
            # Simulate a crash
            1 / 0
        except ZeroDivisionError as e:
            logger.error("A critical error occurred while doing math!", exc_info=True)
            span.record_exception(e)
            # Marking span as error
            span.set_status(Status(StatusCode.ERROR, "Division by zero"))
            return {"status": "error", "message": "Check the logs, something broke!", "trace_id": trace_id, "endpoint": "/demo/error"}

@app.get("/demo/work")
@WORK_DURATION.time()
def demo_work():
    with tracer.start_as_current_span("demo-work-parent-span") as parent_span:
        parent_span.set_attribute("demo.work_type", "complex_process")
        trace_id = format(parent_span.get_span_context().trace_id, "032x")
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
        return {"status": "success", "message": "Work completed with traces.", "trace_id": trace_id,    "endpoint": "/demo/work"}

@app.get("/test-trace")
def test_trace():
    with tracer.start_as_current_span("test-span") as span:
        trace_id = format(span.get_span_context().trace_id, "032x")
        logger.info("Test trace started", extra={"trace_id": trace_id})
        time.sleep(1)
        logger.info("Test trace finished", extra={"trace_id": trace_id})
        return {"status": "trace sent", "trace_id": trace_id, "endpoint": "/test-trace"}

# Auth endpoints
@app.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    return templates.TemplateResponse(request, "signup.html", {"request": request})

@app.post("/signup")
async def signup(request: SignupRequest, db: AsyncSession = Depends(get_db)):
    with tracer.start_as_current_span("signup-span") as span:
        trace_id = format(span.get_span_context().trace_id, "032x")
        logger.info(f"Signup attempt for user: {request.username}", extra={"trace_id": trace_id})
        hashed_password = User.hash_password(request.password)
        user = User(
            username=request.username,
            email=request.email,
            phone_number=request.phone_number,
            password=hashed_password
        )
        try:
            db.add(user)
            await db.commit()
            await db.refresh(user)
            logger.info(f"User {request.username} signed up successfully")
            return RedirectResponse(url="/login", status_code=303, headers={"X-Trace-ID": trace_id})
        except IntegrityError:
            await db.rollback()
            logger.warning(f"Signup failed for {request.username}: user already exists")
            raise HTTPException(status_code=400, detail="User already exists", headers={"X-Trace-ID": trace_id})

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"request": request})

@app.post("/login")
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    with tracer.start_as_current_span("login-span"):
        logger.info(f"Login attempt for user: {request.username}")
        result = await db.execute(select(User).where(User.username == request.username))
        user = result.scalars().first()
        if not user or not user.verify_password(request.password):
            logger.warning(
                "Invalid login attempt",
                extra={"username": request.username}
            )
            # logger.warning(f"Login failed for {request.username}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        access_token = create_access_token(data={"sub": user.username})
        # logger.info(f"User {request.username} logged in successfully")
        logger.info(
            "User login success",
            extra={"username": request.username}
        )
        response = RedirectResponse(url=f"/home/{user.id}", status_code=303)
        response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
        return response

@app.get("/home/{user_id}", response_class=HTMLResponse)
async def home(user_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return templates.TemplateResponse(
        request,
        "home.html",
        {"request": request, "user": user}
    )


@app.post("/logout")
async def logout(request: Request):
    token = request.cookies.get("access_token")
    if token:
        token = token.replace("Bearer ", "")
        await blacklist_token(token)
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token")
    return response

@app.get("/demo/product-trace")
async def demo_product_trace(db: AsyncSession = Depends(get_db)):
    with tracer.start_as_current_span("product-lifecycle-parent") as parent_span:
        trace_id = format(parent_span.get_span_context().trace_id, "032x")
        
        try:
            # STEP 1: Ensure Table Exists (The "First Time" Trace)
            with tracer.start_as_current_span("db-ensure-table"):
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
            
            # STEP 2: Create a Product
            with tracer.start_as_current_span("db-product-insert") as span:
                new_product = Product(name="Gaming Laptop", price=1200.99)
                db.add(new_product)
                await db.commit()
                await db.refresh(new_product)
                span.set_attribute("product.id", new_product.id)
                span.set_attribute("product.name", "Gaming Laptop")

            # STEP 3: Search for the Product
            with tracer.start_as_current_span("db-product-query"):
                result = await db.execute(select(Product).where(Product.name == "Gaming Laptop"))
                product = result.scalars().first()

            return {
                "status": "success",
                "trace_id": trace_id,
                "data": {"id": product.id, "name": product.name}
            }

        except Exception as e:
            parent_span.set_status(Status(StatusCode.ERROR))
            parent_span.record_exception(e)
            return {"status": "error", "trace_id": trace_id, "detail": str(e)}

@app.on_event("startup")
async def startup_event():
    with tracer.start_as_current_span("startup-span") as span:
        logger.info("Application starting up")
        
        try:
            # Create tables
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created")
            
            # Test DB connection
            async with get_db() as db:
                result = await db.execute(select(1))
                await result.fetchone()
            logger.info("Database connection successful")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            logger.warning("App starting without database connectivity")
        
        try:
            # Test Redis connection
            await redis_client.ping()
            logger.info("Redis connection successful")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            logger.warning("App starting without Redis connectivity")
        
        span.set_attribute("app.start_time", time.time())
        span.set_attribute("app.name", "fastapi-observability")
        span.set_attribute("app.version", "1.0.0")
        logger.info("Application startup completed")

@app.on_event("shutdown")
def shutdown_event():
    with tracer.start_as_current_span("shutdown-span") as span:
        logger.info("Application shutting down")
        span.set_attribute("app.shutdown_time", time.time())
        span.set_attribute("app.name", "fastapi-observability")
        span.set_attribute("app.version", "1.0.0")

@app.get("/check-tempo")
async def check_tempo_api():
    # Use the container name 'tempo' as defined in your docker-compose
    tempo_url = "http://tempo:3200" 
    
    async with httpx.AsyncClient() as client:
        try:
            # 1. Check if Tempo is 'ready' (Storage + Ingester status)
            ready_resp = await client.get(f"{tempo_url}/ready")
            
            # 2. Check if the Query API is responding
            echo_resp = await client.get(f"{tempo_url}/api/echo")
            
            return {
                "tempo_status": "online",
                "readiness": ready_resp.text.strip(),
                "echo_response": echo_resp.text.strip(),
                "ready_code": ready_resp.status_code
            }
        except Exception as e:
            return {
                "tempo_status": "offline",
                "error": str(e),
                "hint": "Check if Tempo container is running and 'tempo' hostname is correct."
            }

@app.get("/demo/slo")
def slo_test(success: bool = True):
    with tracer.start_as_current_span("slo-test-span") as span:
        trace_id = format(span.get_span_context().trace_id, "032x")
        REQUEST_COUNT.inc()

        if not success:
            ERROR_COUNT.inc()
            logger.error("SLO failure triggered")
            raise HTTPException(status_code=500, detail=f"SLO failure and trace_id: {trace_id}")

        logger.info("SLO success")
        return {"status": "success", "trace_id": trace_id, "endpoint": "/demo/slo"}