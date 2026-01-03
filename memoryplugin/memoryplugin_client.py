# memoryplugin_client.py

from __future__ import annotations

import time
import logging
from typing import Any, Dict, List, Optional, Union

import requests

logger = logging.getLogger(__name__)


class MemoryPluginError(Exception):
    """Base exception for MemoryPlugin client errors."""


class MemoryPluginRateLimitError(MemoryPluginError):
    """Raised when we hit a rate limit and give up after retries."""


class MemoryPluginClient:
    """
    Generic HTTP client for MemoryPlugin's API.

    NOTE:
      - The endpoint paths below are *placeholders*.
      - Replace them with the exact paths from:
        https://help.memoryplugin.com / https://memoryplugin.mintlify.app

      This class is designed so that you only need to fix the URLs, not the logic.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.memoryplugin.com",
        timeout: int = 15,
        max_retries: int = 3,
        backoff_factor: float = 1.5,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    # ------------------------------------------------------------------
    # Low-level request helper
    # ------------------------------------------------------------------
    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Wrapper around requests with:
          - Bearer auth
          - Basic retry with exponential backoff on 429/5xx
        """
        url = f"{self.base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        attempt = 0
        while True:
            attempt += 1
            try:
                resp = requests.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    params=params,
                    json=json,
                    timeout=self.timeout,
                )
            except requests.RequestException as e:
                if attempt > self.max_retries:
                    raise MemoryPluginError(f"Network error calling {url}: {e}") from e
                sleep_s = self.backoff_factor ** (attempt - 1)
                logger.warning("Network error, retrying in %.2fs: %s", sleep_s, e)
                time.sleep(sleep_s)
                continue

            if resp.status_code == 429 or 500 <= resp.status_code < 600:
                # Rate limit or server error
                if attempt > self.max_retries:
                    raise MemoryPluginRateLimitError(
                        f"Failed after {self.max_retries} retries. "
                        f"Status={resp.status_code}, body={resp.text[:500]}"
                    )
                sleep_s = self.backoff_factor ** (attempt - 1)
                logger.warning(
                    "MemoryPlugin %s: status=%s, retrying in %.2fs",
                    url,
                    resp.status_code,
                    sleep_s,
                )
                time.sleep(sleep_s)
                continue

            if not resp.ok:
                raise MemoryPluginError(
                    f"HTTP {resp.status_code} calling {url}: {resp.text[:500]}"
                )

            try:
                return resp.json()
            except ValueError:
                # Not JSON
                return resp.text

    # ------------------------------------------------------------------
    # Buckets
    # ------------------------------------------------------------------
    def list_buckets(self) -> List[Dict[str, Any]]:
        """
        List buckets / memory containers.

        TODO: Replace '/v1/buckets' with the actual path from the docs.
        """
        return self._request("GET", "/v1/buckets")

    def create_bucket(
        self,
        name: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new bucket.

        TODO: Replace path & payload shape as per MemoryPlugin docs.
        """
        payload: Dict[str, Any] = {"name": name}
        if description:
            payload["description"] = description
        if metadata:
            payload["metadata"] = metadata
        return self._request("POST", "/v1/buckets", json=payload)

    def delete_bucket(self, bucket_id: str) -> Dict[str, Any]:
        """
        Delete a bucket by ID.

        TODO: Replace path param style as per docs.
        """
        return self._request("DELETE", f"/v1/buckets/{bucket_id}")

    # ------------------------------------------------------------------
    # Memories
    # ------------------------------------------------------------------
    def create_memory(
        self,
        content: str,
        *,
        bucket_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a memory.

        Typical fields (to align with MemoryPlugin concepts):
          - content: raw text
          - bucket_id: which bucket to attach to
          - tags: keywords
          - metadata: arbitrary JSON
          - source: e.g., 'chatgpt', 'claude', 'notion', 'github', etc.

        TODO: Confirm field names with official API.
        """
        payload: Dict[str, Any] = {"content": content}
        if bucket_id:
            payload["bucket_id"] = bucket_id
        if tags:
            payload["tags"] = tags
        if metadata:
            payload["metadata"] = metadata
        if source:
            payload["source"] = source

        return self._request("POST", "/v1/memories", json=payload)

    def get_memory(self, memory_id: str) -> Dict[str, Any]:
        """
        Fetch a memory by ID.
        """
        return self._request("GET", f"/v1/memories/{memory_id}")

    def search_memories(
        self,
        query: str,
        *,
        bucket_id: Optional[str] = None,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Semantic / full-text search.

        TODO: Confirm query parameter names & filters with docs.
        """
        params: Dict[str, Any] = {"q": query, "limit": limit}
        if bucket_id:
            params["bucket_id"] = bucket_id
        return self._request("GET", "/v1/memories/search", params=params)

    def update_memory(
        self,
        memory_id: str,
        *,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Partial update of a memory.

        TODO: Confirm whether PATCH is supported and field names.
        """
        payload: Dict[str, Any] = {}
        if content is not None:
            payload["content"] = content
        if tags is not None:
            payload["tags"] = tags
        if metadata is not None:
            payload["metadata"] = metadata

        return self._request("PATCH", f"/v1/memories/{memory_id}", json=payload)

    def delete_memory(self, memory_id: str) -> Dict[str, Any]:
        """
        Delete a memory by ID.
        """
        return self._request("DELETE", f"/v1/memories/{memory_id}")
