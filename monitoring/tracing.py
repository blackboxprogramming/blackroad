"""
Distributed Tracing System - Jaeger integration for request tracing
"""

import json
import time
import random
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import logging


class SpanKind(Enum):
    """Types of spans."""
    INTERNAL = "INTERNAL"
    SERVER = "SERVER"
    CLIENT = "CLIENT"
    PRODUCER = "PRODUCER"
    CONSUMER = "CONSUMER"


class SpanStatus(Enum):
    """Span execution status."""
    UNSET = "UNSET"
    OK = "OK"
    ERROR = "ERROR"


class TraceSpan:
    """Represents a trace span."""
    
    def __init__(self, trace_id: str, span_id: str, parent_span_id: Optional[str],
                 operation_name: str, kind: SpanKind):
        self.trace_id = trace_id
        self.span_id = span_id
        self.parent_span_id = parent_span_id
        self.operation_name = operation_name
        self.kind = kind
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.duration_ms: Optional[float] = None
        self.status = SpanStatus.UNSET
        self.attributes: Dict[str, Any] = {}
        self.events: List[Dict] = []
        self.tags: Dict[str, str] = {}
    
    def set_attribute(self, key: str, value: Any) -> None:
        """Set span attribute."""
        self.attributes[key] = value
    
    def add_event(self, name: str, attributes: Dict[str, Any] = None) -> None:
        """Add event to span."""
        self.events.append({
            'name': name,
            'timestamp': datetime.utcnow().isoformat(),
            'attributes': attributes or {}
        })
    
    def finish(self) -> None:
        """Finish span."""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
    
    def set_error(self, message: str, exception_type: str = None) -> None:
        """Mark span as error."""
        self.status = SpanStatus.ERROR
        self.set_attribute('error', True)
        self.set_attribute('error.kind', exception_type or 'Exception')
        self.set_attribute('error.message', message)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'traceID': self.trace_id,
            'spanID': self.span_id,
            'parentSpanID': self.parent_span_id,
            'operationName': self.operation_name,
            'kind': self.kind.value,
            'startTime': int(self.start_time * 1e6),
            'duration': int(self.duration_ms * 1000) if self.duration_ms else 0,
            'status': self.status.value,
            'attributes': self.attributes,
            'events': self.events,
            'tags': self.tags,
        }


class Trace:
    """Represents a complete trace."""
    
    def __init__(self, trace_id: str, service_name: str):
        self.trace_id = trace_id
        self.service_name = service_name
        self.spans: List[TraceSpan] = []
        self.start_time = datetime.utcnow()
        self.tags: Dict[str, str] = {}
    
    def add_span(self, span: TraceSpan) -> None:
        """Add span to trace."""
        self.spans.append(span)
    
    def get_root_span(self) -> Optional[TraceSpan]:
        """Get root span."""
        for span in self.spans:
            if span.parent_span_id is None:
                return span
        return None
    
    def get_duration_ms(self) -> float:
        """Get total trace duration."""
        if not self.spans:
            return 0
        
        min_start = min(s.start_time for s in self.spans)
        max_end = max(s.end_time or s.start_time for s in self.spans)
        return (max_end - min_start) * 1000
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'traceID': self.trace_id,
            'serviceName': self.service_name,
            'spans': [s.to_dict() for s in self.spans],
            'duration': int(self.get_duration_ms() * 1000),
            'startTime': self.start_time.isoformat(),
        }


class DistributedTracer:
    """Distributed tracing system."""
    
    def __init__(self, service_name: str = "platform"):
        self.service_name = service_name
        self.traces: Dict[str, Trace] = {}
        self.active_spans: Dict[str, TraceSpan] = {}
        self.logger = logging.getLogger(__name__)
    
    def start_trace(self) -> str:
        """Start new trace."""
        trace_id = str(uuid.uuid4()).replace('-', '')
        trace = Trace(trace_id, self.service_name)
        self.traces[trace_id] = trace
        return trace_id
    
    def start_span(self, trace_id: str, operation_name: str,
                  kind: SpanKind = SpanKind.INTERNAL,
                  parent_span_id: Optional[str] = None) -> TraceSpan:
        """Start new span."""
        span_id = str(uuid.uuid4()).replace('-', '')[:16]
        
        span = TraceSpan(trace_id, span_id, parent_span_id, operation_name, kind)
        
        if trace_id in self.traces:
            self.traces[trace_id].add_span(span)
        
        self.active_spans[span_id] = span
        return span
    
    def finish_span(self, span_id: str) -> None:
        """Finish span."""
        if span_id in self.active_spans:
            span = self.active_spans[span_id]
            span.finish()
            del self.active_spans[span_id]
    
    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Get trace."""
        return self.traces.get(trace_id)
    
    def get_traces_for_service(self, service: str = None) -> List[Trace]:
        """Get all traces for service."""
        if service is None:
            service = self.service_name
        
        return [t for t in self.traces.values() if t.service_name == service]
    
    def find_slow_traces(self, threshold_ms: float = 1000) -> List[Trace]:
        """Find traces slower than threshold."""
        return [t for t in self.traces.values() if t.get_duration_ms() > threshold_ms]
    
    def find_error_traces(self) -> List[Trace]:
        """Find traces with errors."""
        error_traces = []
        for trace in self.traces.values():
            if any(s.status == SpanStatus.ERROR for s in trace.spans):
                error_traces.append(trace)
        return error_traces
    
    def export_jaeger_format(self) -> str:
        """Export in Jaeger JSON format."""
        data = {
            'data': [t.to_dict() for t in self.traces.values()],
            'total': len(self.traces),
            'limit': len(self.traces),
            'offset': 0,
            'errors': []
        }
        return json.dumps(data, indent=2)
    
    def get_trace_statistics(self) -> Dict:
        """Get trace statistics."""
        traces = list(self.traces.values())
        if not traces:
            return {}
        
        durations = [t.get_duration_ms() for t in traces]
        
        return {
            'total_traces': len(traces),
            'avg_duration_ms': sum(durations) / len(durations),
            'min_duration_ms': min(durations),
            'max_duration_ms': max(durations),
            'error_traces': len([t for t in traces if any(s.status == SpanStatus.ERROR for s in t.spans)]),
            'total_spans': sum(len(t.spans) for t in traces),
        }


class TraceContextPropagator:
    """Propagate trace context across services."""
    
    @staticmethod
    def inject(trace_id: str, span_id: str) -> Dict[str, str]:
        """Inject trace context into headers."""
        return {
            'traceparent': f'00-{trace_id}-{span_id}-01',
            'baggage': f'userId=user123,sessionId=session456',
        }
    
    @staticmethod
    def extract(headers: Dict[str, str]) -> tuple:
        """Extract trace context from headers."""
        traceparent = headers.get('traceparent', '')
        if traceparent:
            parts = traceparent.split('-')
            if len(parts) >= 4:
                trace_id = parts[1]
                span_id = parts[2]
                return trace_id, span_id
        
        return None, None


class TracingMiddleware:
    """Middleware for automatic tracing."""
    
    def __init__(self, tracer: DistributedTracer):
        self.tracer = tracer
    
    def trace_request(self, method: str, path: str, headers: Dict[str, str]) -> TraceSpan:
        """Trace incoming request."""
        trace_id, parent_span_id = TraceContextPropagator.extract(headers)
        
        if not trace_id:
            trace_id = self.tracer.start_trace()
        
        span = self.tracer.start_span(
            trace_id,
            f"{method} {path}",
            SpanKind.SERVER,
            parent_span_id
        )
        
        span.set_attribute('http.method', method)
        span.set_attribute('http.url', path)
        span.set_attribute('http.scheme', 'https')
        
        return span
    
    def trace_database_call(self, trace_id: str, query: str,
                           parent_span_id: str) -> TraceSpan:
        """Trace database call."""
        span = self.tracer.start_span(
            trace_id,
            "db.query",
            SpanKind.CLIENT,
            parent_span_id
        )
        
        span.set_attribute('db.system', 'postgresql')
        span.set_attribute('db.operation', 'query')
        span.set_attribute('db.statement', query[:100])
        
        return span
    
    def trace_external_call(self, trace_id: str, url: str,
                           parent_span_id: str) -> TraceSpan:
        """Trace external API call."""
        span = self.tracer.start_span(
            trace_id,
            "http.client",
            SpanKind.CLIENT,
            parent_span_id
        )
        
        span.set_attribute('http.url', url)
        span.set_attribute('http.client', 'requests')
        
        return span
