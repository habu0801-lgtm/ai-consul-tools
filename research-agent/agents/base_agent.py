from abc import ABC, abstractmethod
from typing import Dict, Any
from datetime import datetime


class BaseAgent(ABC):
    """Base class for all research agents."""

    def __init__(self, agent_name: str):
        self.name = agent_name
        self.timeout = 35
        self.created_at = datetime.now()

    @abstractmethod
    def research(self, query: str) -> Dict[str, Any]:
        """
        Execute research on the given query.

        Args:
            query: Search query string

        Returns:
            dict with structure:
            {
                "source": "agent_name",
                "status": "success" | "error",
                "data": {...},
                "error": "error message if failed",
                "execution_time": float
            }
        """
        pass

    def _build_response(self, status: str, data: Dict[str, Any] = None, error: str = None) -> Dict[str, Any]:
        """Build standardized response object."""
        return {
            "source": self.name,
            "status": status,
            "data": data or {},
            "error": error,
            "timestamp": datetime.now().isoformat()
        }

    def _handle_error(self, error_msg: str) -> Dict[str, Any]:
        """Handle and return error response."""
        return self._build_response("error", error=error_msg)
