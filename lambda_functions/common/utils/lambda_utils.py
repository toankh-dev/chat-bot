"""
Utility functions for Lambda best practices
- Structured logging
- Error handling decorators
- Metrics and monitoring
- Cold start optimization
"""

import json
import logging
import time
import functools
from typing import Dict, Any, Callable, Optional
from datetime import datetime
from enum import Enum


class LogLevel(str, Enum):
    """Log levels for structured logging"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class StructuredLogger:
    """Structured JSON logger for Lambda functions"""

    def __init__(self, service_name: str, logger: Optional[logging.Logger] = None):
        self.service_name = service_name
        self.logger = logger or logging.getLogger()

    def _log(
        self,
        level: LogLevel,
        message: str,
        event_type: str = "log",
        **kwargs
    ):
        """Log structured message"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "service": self.service_name,
            "level": level.value,
            "message": message,
            "event_type": event_type,
            **kwargs
        }

        log_func = getattr(self.logger, level.value.lower())
        log_func(json.dumps(log_entry, default=str))

    def info(self, message: str, **kwargs):
        """Log info message"""
        self._log(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log error message"""
        if error:
            kwargs["error_type"] = type(error).__name__
            kwargs["error_message"] = str(error)
        self._log(LogLevel.ERROR, message, **kwargs)

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._log(LogLevel.DEBUG, message, **kwargs)

    def metric(self, metric_name: str, value: float, unit: str = "Count", **kwargs):
        """Log metric for monitoring"""
        self._log(
            LogLevel.INFO,
            f"Metric: {metric_name}",
            event_type="metric",
            metric_name=metric_name,
            metric_value=value,
            metric_unit=unit,
            **kwargs
        )


def lambda_handler_decorator(
    service_name: str,
    log_event: bool = False,
    log_response: bool = False,
    capture_errors: bool = True
):
    """
    Decorator for Lambda handlers with structured logging and error handling

    Args:
        service_name: Name of the service
        log_event: Whether to log the incoming event
        log_response: Whether to log the response
        capture_errors: Whether to catch and format errors

    Usage:
        @lambda_handler_decorator("my-service", log_event=True)
        def handler(event, context):
            return {"statusCode": 200, "body": "OK"}
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
            structured_logger = StructuredLogger(service_name)
            start_time = time.time()

            # Log invocation start
            structured_logger.info(
                f"Handler invoked: {func.__name__}",
                event_type="invocation_start",
                function_name=context.function_name if context else "unknown",
                request_id=context.aws_request_id if context else "unknown"
            )

            # Log event if requested
            if log_event:
                structured_logger.debug(
                    "Incoming event",
                    event_type="event",
                    event=event
                )

            try:
                # Execute handler
                response = func(event, context)

                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000

                # Log response if requested
                if log_response:
                    structured_logger.debug(
                        "Handler response",
                        event_type="response",
                        response=response
                    )

                # Log metrics
                structured_logger.metric(
                    "handler_duration",
                    duration_ms,
                    unit="Milliseconds",
                    status="success"
                )

                structured_logger.info(
                    f"Handler completed successfully",
                    event_type="invocation_end",
                    duration_ms=duration_ms,
                    status="success"
                )

                return response

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000

                # Log error
                structured_logger.error(
                    f"Handler failed: {str(e)}",
                    error=e,
                    event_type="invocation_error",
                    duration_ms=duration_ms,
                    status="error"
                )

                # Log error metric
                structured_logger.metric(
                    "handler_errors",
                    1,
                    unit="Count",
                    error_type=type(e).__name__
                )

                if capture_errors:
                    # Return formatted error response
                    return create_error_response(e, event, context)
                else:
                    # Re-raise for Lambda to handle
                    raise

        return wrapper
    return decorator


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for retrying functions with exponential backoff

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        exceptions: Tuple of exceptions to catch

    Usage:
        @retry_with_backoff(max_retries=3, base_delay=1.0)
        def my_function():
            # Code that might fail
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger()

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt >= max_retries:
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries} retries: {e}"
                        )
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)

                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {delay:.2f}s: {e}"
                    )

                    time.sleep(delay)

        return wrapper
    return decorator


def create_error_response(
    error: Exception,
    event: Dict[str, Any],
    context: Any,
    include_stacktrace: bool = False
) -> Dict[str, Any]:
    """
    Create standardized error response for API Gateway

    Args:
        error: Exception that occurred
        event: Lambda event
        context: Lambda context
        include_stacktrace: Whether to include stack trace (dev only)

    Returns:
        API Gateway response with error details
    """
    import traceback

    error_response = {
        "error": type(error).__name__,
        "message": str(error),
        "request_id": context.aws_request_id if context else "unknown",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    if include_stacktrace:
        error_response["stacktrace"] = traceback.format_exc()

    # Determine status code based on error type
    status_code = 500
    if "NotFound" in type(error).__name__:
        status_code = 404
    elif "Validation" in type(error).__name__ or "BadRequest" in type(error).__name__:
        status_code = 400
    elif "Unauthorized" in type(error).__name__ or "Forbidden" in type(error).__name__:
        status_code = 403
    elif "Timeout" in type(error).__name__:
        status_code = 504

    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "X-Request-Id": context.aws_request_id if context else "unknown"
        },
        "body": json.dumps(error_response, default=str)
    }


class ColdStartTracker:
    """Track and optimize Lambda cold starts"""

    def __init__(self):
        self.is_cold_start = True
        self.cold_start_duration = None
        self.warm_invocations = 0

    def record_cold_start(self, duration_ms: float):
        """Record cold start duration"""
        if self.is_cold_start:
            self.cold_start_duration = duration_ms
            self.is_cold_start = False
            logger = logging.getLogger()
            logger.info(
                json.dumps({
                    "event_type": "cold_start",
                    "duration_ms": duration_ms,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                })
            )

    def increment_warm_invocation(self):
        """Increment warm invocation counter"""
        if not self.is_cold_start:
            self.warm_invocations += 1


class CircuitBreaker:
    """
    Circuit breaker pattern for external service calls

    States:
    - CLOSED: Normal operation
    - OPEN: Failing fast, not attempting calls
    - HALF_OPEN: Testing if service recovered
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = "HALF_OPEN"
            else:
                raise Exception(f"Circuit breaker is OPEN for {func.__name__}")

        try:
            result = func(*args, **kwargs)

            # Success - reset if in HALF_OPEN
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0

            return result

        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                logger = logging.getLogger()
                logger.error(
                    f"Circuit breaker opened for {func.__name__} "
                    f"after {self.failure_count} failures"
                )

            raise


def measure_duration(operation_name: str):
    """
    Decorator to measure and log operation duration

    Usage:
        @measure_duration("database_query")
        def query_db():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000

                logger = logging.getLogger()
                logger.info(
                    json.dumps({
                        "event_type": "duration_metric",
                        "operation": operation_name,
                        "duration_ms": duration_ms,
                        "status": "success",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    })
                )

                return result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000

                logger = logging.getLogger()
                logger.error(
                    json.dumps({
                        "event_type": "duration_metric",
                        "operation": operation_name,
                        "duration_ms": duration_ms,
                        "status": "error",
                        "error_type": type(e).__name__,
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    })
                )

                raise

        return wrapper
    return decorator


# Global cold start tracker instance
cold_start_tracker = ColdStartTracker()
