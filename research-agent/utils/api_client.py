import time
import requests
from typing import Callable, Any, Dict
from requests.exceptions import Timeout, ConnectionError, RequestException


class RobustAPIClient:
    """API client with retry logic and timeout management."""

    def __init__(self, max_retries: int = 3, timeout: int = 30):
        self.max_retries = max_retries
        self.timeout = timeout

    def call_with_retry(self, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """
        Call function with exponential backoff retry logic.

        Args:
            func: Callable to execute
            *args, **kwargs: Arguments to pass to func

        Returns:
            Result from func or error dict if all retries fail
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Timeout:
                if attempt == self.max_retries:
                    return {"error": "API timeout after retries", "attempt": attempt}
                wait_time = 2 ** attempt
                time.sleep(wait_time)
            except ConnectionError:
                if attempt == self.max_retries:
                    return {"error": "Connection failed after retries", "attempt": attempt}
                wait_time = 2 ** attempt
                time.sleep(wait_time)
            except RequestException as e:
                if attempt == self.max_retries:
                    return {"error": f"Request failed: {str(e)}", "attempt": attempt}
                wait_time = 2 ** attempt
                time.sleep(wait_time)

    @staticmethod
    def get(url: str, headers: Dict = None, params: Dict = None, timeout: int = 30) -> Dict[str, Any]:
        """Make GET request with error handling."""
        try:
            response = requests.get(url, headers=headers, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.JSONDecodeError:
            return {"text": response.text, "status_code": response.status_code}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_text(url: str, headers: Dict = None, params: Dict = None, timeout: int = 30) -> str:
        """Make GET request and return text content."""
        try:
            response = requests.get(url, headers=headers, params=params, timeout=timeout)
            response.raise_for_status()
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"
