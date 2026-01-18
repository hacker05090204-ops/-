"""
Execution Layer Request/Response Logging

Comprehensive logging of all API requests and responses.
NO sensitive data (API keys, tokens) is logged.

OBSERVE ONLY — NO STEALTH, NO EVASION, NO BYPASS.

This system assists humans. It does not autonomously hunt, judge, or earn.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Union
import secrets


@dataclass(frozen=True)
class RequestLog:
    """Log entry for API request."""
    request_id: str
    timestamp: datetime
    endpoint: str
    method: str
    execution_id: Optional[str] = None


@dataclass(frozen=True)
class ResponseLog:
    """Log entry for API response."""
    request_id: str
    response_id: Optional[str]
    status_code: int
    response_time_ms: float
    timestamp: datetime


class RequestLogger:
    """Log API requests and responses.
    
    SECURITY: NO sensitive data (API keys, tokens) is logged.
    
    OBSERVE ONLY — NO STEALTH, NO EVASION, NO BYPASS.
    """
    
    def __init__(self) -> None:
        self._logs: list[Union[RequestLog, ResponseLog]] = []

    def log_request(
        self,
        endpoint: str,
        method: str,
        execution_id: Optional[str] = None,
    ) -> str:
        """Log request and return request_id.
        
        SECURITY: NO sensitive data is logged.
        """
        request_id = secrets.token_urlsafe(16)
        log_entry = RequestLog(
            request_id=request_id,
            timestamp=datetime.now(timezone.utc),
            endpoint=endpoint,
            method=method,
            execution_id=execution_id,
        )
        self._logs.append(log_entry)
        return request_id
    
    def log_response(
        self,
        request_id: str,
        status_code: int,
        response_time_ms: float,
        response_id: Optional[str] = None,
    ) -> None:
        """Log response for request_id.
        
        SECURITY: NO sensitive data is logged.
        """
        log_entry = ResponseLog(
            request_id=request_id,
            response_id=response_id,
            status_code=status_code,
            response_time_ms=response_time_ms,
            timestamp=datetime.now(timezone.utc),
        )
        self._logs.append(log_entry)
    
    def get_logs_for_execution(
        self,
        execution_id: str,
    ) -> list[Union[RequestLog, ResponseLog]]:
        """Get all logs for an execution."""
        result: list[Union[RequestLog, ResponseLog]] = []
        request_ids: set[str] = set()
        
        # Find all request logs for this execution
        for log in self._logs:
            if isinstance(log, RequestLog) and log.execution_id == execution_id:
                result.append(log)
                request_ids.add(log.request_id)
        
        # Find all response logs for those requests
        for log in self._logs:
            if isinstance(log, ResponseLog) and log.request_id in request_ids:
                result.append(log)
        
        return sorted(result, key=lambda x: x.timestamp)
    
    def get_all_logs(self) -> list[Union[RequestLog, ResponseLog]]:
        """Get all logs for audit."""
        return list(self._logs)
    
    def clear_logs(self) -> None:
        """Clear all logs."""
        self._logs.clear()
