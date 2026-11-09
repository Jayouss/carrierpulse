"""Abstract Business Data Provider Interface and Record Definition."""

from abc import ABC, abstractmethod
import asyncio
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BusinessRecord(BaseModel):
    """Unified internal representation of a discovered business listing."""

    id: str = Field(description="Unique internal identifier (e.g. Place ID or UUID)")
    name: str = Field(description="Official business name")
    address: str = Field(default="", description="Full physical street address")
    raw_phone: Optional[str] = Field(default=None, description="Phone number string from provider")
    website: Optional[str] = Field(default=None, description="Business website URL if available")
    category: str = Field(default="General", description="Human-readable business category")
    category_id: str = Field(default="general", description="Category system identifier")
    provider_source: str = Field(default="unknown", description="Source provider tag")
    place_id: Optional[str] = Field(default=None, description="Google Place ID if applicable")
    allows_export: bool = Field(default=False, description="Whether source licensing permits bulk CSV export")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class BaseBusinessProvider(ABC):
    """Abstract interface implemented by all business discovery providers."""

    provider_id: str
    provider_name: str
    allows_csv_export: bool
    attribution_text: str

    @abstractmethod
    async def discover(
        self,
        category_ids: List[str],
        max_results: int,
        cancel_event: Optional[asyncio.Event] = None,
    ) -> List[BusinessRecord]:
        """Discover businesses in Fresno, CA matching requested categories up to max_results."""
        pass
