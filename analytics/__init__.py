"""Advanced Analytics & Real-Time Data Pipeline."""

__version__ = "1.0.0"

from .ingestion import EventIngestion, Event
from .warehouse import DataWarehouse, FactTable, DimensionTable
from .analytics import AnalyticsEngine
from .pipelines import ETLPipeline

__all__ = [
    'EventIngestion',
    'Event',
    'DataWarehouse',
    'FactTable',
    'DimensionTable',
    'AnalyticsEngine',
    'ETLPipeline',
]
