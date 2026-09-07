"""
GameHub Backend API Client.

Decouples the LangGraph assistant layer, tools, and agents from direct database,
repository, service, and vector store dependencies. All agent interactions flow
through this client to consume GameHub's HTTP REST endpoints.
"""

import time
import logging
from typing import List, Dict, Any, Optional
import httpx
from app.config import settings

logger = logging.getLogger("gamehub.api_client")


class BackendApiClient:
    """
    Production-quality HTTP client for communicating with GameHub Backend APIs.

    Features:
    - Dual transport support:
        1. In-process ASGI transport (default for monolithic runtime & unit tests):
           Executes HTTP requests directly through FastAPI's ASGI router in memory
           with dependency injection, status code handling, and schema validation.
        2. Real HTTP transport (microservices mode):
           Connects over TCP/HTTP to an external GameHub backend service.
    - Automatic retries with exponential backoff for transient 5xx / connection errors.
    - Configurable timeout handling.
    - Structured telemetry logging (method, endpoint, status code, latency).
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        use_asgi: Optional[bool] = None,
    ):
        self.base_url = (base_url or settings.BACKEND_API_BASE_URL).rstrip("/")
        self.timeout = timeout or settings.API_CLIENT_TIMEOUT
        self.max_retries = max_retries if max_retries is not None else settings.API_CLIENT_MAX_RETRIES
        self.use_asgi = use_asgi if use_asgi is not None else settings.API_CLIENT_USE_ASGI
        self._client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        """Lazily initialize client to avoid circular imports during module loading."""
        if self._client is None or self._client.is_closed:
            client_timeout = httpx.Timeout(
                connect=5.0,
                read=self.timeout,
                write=5.0,
                pool=10.0,
            )
            if self.use_asgi:
                try:
                    from fastapi.testclient import TestClient
                    from app.main import app
                    self._client = TestClient(
                        app=app,
                        base_url="http://testserver/api",
                    )
                    logger.debug("BackendApiClient initialized with in-process ASGI TestClient.")
                except Exception as e:
                    logger.warning(
                        f"Failed to initialize in-process ASGI TestClient: {e}. Falling back to HTTP transport ({self.base_url})."
                    )
                    self._client = httpx.Client(base_url=self.base_url, timeout=client_timeout)
            else:
                self._client = httpx.Client(base_url=self.base_url, timeout=client_timeout)
                logger.debug(f"BackendApiClient initialized with network transport: {self.base_url}")
        return self._client

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        """Executes an HTTP request with retry logic, telemetry, and error logging."""
        endpoint = "/" + endpoint.lstrip("/")
        client = self._get_client()

        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            start_time = time.perf_counter()
            try:
                logger.debug(f"API Request [{method} {endpoint}] attempt {attempt}/{self.max_retries}")
                response = client.request(
                    method=method,
                    url=endpoint,
                    params=params,
                    json=json_data,
                )
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                logger.info(
                    f"API Response: {method} {endpoint} -> {response.status_code} ({elapsed_ms:.1f}ms)"
                )

                # Retry on 5xx server errors
                if 500 <= response.status_code < 600 and attempt < self.max_retries:
                    backoff = 0.2 * (2 ** (attempt - 1))
                    logger.warning(
                        f"API 5xx error ({response.status_code}) on {endpoint}. Retrying in {backoff:.2f}s..."
                    )
                    time.sleep(backoff)
                    continue

                return response

            except (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout, httpx.TransportError) as e:
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                last_exception = e
                logger.warning(
                    f"API Network/Transport error on {method} {endpoint}: {e} ({elapsed_ms:.1f}ms). "
                    f"Attempt {attempt}/{self.max_retries}"
                )
                if attempt < self.max_retries:
                    backoff = 0.2 * (2 ** (attempt - 1))
                    time.sleep(backoff)
                else:
                    raise

        if last_exception:
            raise last_exception
        raise RuntimeError(f"Request failed after {self.max_retries} attempts.")

    # -------------------------------------------------------------------------
    # Catalog & Games APIs
    # -------------------------------------------------------------------------

    def get_games(
        self,
        genre: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        max_duration: Optional[float] = None,
        min_rating: Optional[float] = None,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        user_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """GET /games: Search and filter games in the catalog."""
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if genre:
            params["genre"] = genre
        if min_price is not None:
            params["min_price"] = min_price
        if max_price is not None:
            params["max_price"] = max_price
        if max_duration is not None:
            params["max_duration"] = max_duration
        if min_rating is not None:
            params["min_rating"] = min_rating
        if search:
            params["search"] = search
        if sort_by:
            params["sort_by"] = sort_by
        if user_id is not None:
            params["user_id"] = user_id

        res = self._request("GET", "/games", params=params)
        if res.is_success:
            return res.json()
        logger.error(f"get_games failed: {res.status_code} {res.text}")
        return []

    def get_game(self, game_id: int, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """GET /games/{game_id}: Retrieve single game full details."""
        params = {"user_id": user_id} if user_id is not None else None
        res = self._request("GET", f"/games/{game_id}", params=params)
        if res.status_code == 200:
            return res.json()
        if res.status_code == 404:
            return None
        logger.warning(f"get_game({game_id}) returned unexpected status: {res.status_code}")
        return None

    def get_genres(self) -> List[str]:
        """GET /games/genres: Retrieve distinct genres."""
        res = self._request("GET", "/games/genres")
        if res.is_success:
            return res.json()
        return []

    def semantic_search(
        self,
        query: str,
        limit: int = 8,
        genre: Optional[str] = None,
        max_price: Optional[float] = None,
        user_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """GET /games/semantic-search: Vector similarity search with database enrichment."""
        params: Dict[str, Any] = {"query": query, "limit": limit}
        if genre:
            params["genre"] = genre
        if max_price is not None:
            params["max_price"] = max_price
        if user_id is not None:
            params["user_id"] = user_id

        res = self._request("GET", "/games/semantic-search", params=params)
        if res.is_success:
            return res.json()
        logger.error(f"semantic_search failed: {res.status_code} {res.text}")
        return []

    # -------------------------------------------------------------------------
    # User Profile & Library APIs
    # -------------------------------------------------------------------------

    def get_user(self, user_id: int) -> Dict[str, Any]:
        """GET /users/{user_id}: Retrieve user profile and wallet balance."""
        res = self._request("GET", f"/users/{user_id}")
        if res.status_code == 200:
            data = res.json()
            data["found"] = True
            return data
        return {"user_id": user_id, "wallet_balance": 0.0, "found": False}

    def get_user_library(self, user_id: int) -> List[Dict[str, Any]]:
        """GET /users/{user_id}/library: Retrieve all games owned by user."""
        res = self._request("GET", f"/users/{user_id}/library")
        if res.is_success:
            return res.json()
        logger.error(f"get_user_library({user_id}) failed: {res.status_code} {res.text}")
        return []

    # -------------------------------------------------------------------------
    # Cart APIs
    # -------------------------------------------------------------------------

    def get_user_cart(self, user_id: int) -> Dict[str, Any]:
        """GET /users/{user_id}/cart: Retrieve shopping cart summary."""
        res = self._request("GET", f"/users/{user_id}/cart")
        if res.is_success:
            return res.json()
        return {
            "items": [],
            "item_count": 0,
            "total_price": 0.0,
            "user_wallet_balance": 0.0,
            "is_affordable": True,
        }

    def add_to_cart(self, user_id: int, game_id: int) -> Dict[str, Any]:
        """POST /users/{user_id}/cart: Add a game to shopping cart."""
        res = self._request("POST", f"/users/{user_id}/cart", json_data={"game_id": game_id})
        if res.is_success:
            return {"success": True, "game_id": game_id, "message": "Added to cart successfully."}
        try:
            detail = res.json().get("detail", res.text)
        except Exception:
            detail = res.text
        return {"success": False, "error": detail}

    def remove_from_cart(self, user_id: int, game_id: int) -> Dict[str, Any]:
        """DELETE /users/{user_id}/cart/{game_id}: Remove game from cart."""
        res = self._request("DELETE", f"/users/{user_id}/cart/{game_id}")
        return {"success": res.is_success, "game_id": game_id}

    def clear_cart(self, user_id: int) -> Dict[str, Any]:
        """DELETE /users/{user_id}/cart: Clear all cart items."""
        res = self._request("DELETE", f"/users/{user_id}/cart")
        return {"success": res.is_success}

    # -------------------------------------------------------------------------
    # Purchase APIs (Validation & Atomic Execution)
    # -------------------------------------------------------------------------

    def validate_purchase(self, user_id: int, game_ids: List[int]) -> Dict[str, Any]:
        """POST /purchases/validate: Pre-validate purchase conditions."""
        payload = {"user_id": user_id, "game_ids": game_ids}
        res = self._request("POST", "/purchases/validate", json_data=payload)
        if res.is_success:
            data = res.json()
            data["valid"] = True
            return data
        try:
            detail = res.json().get("detail", "Validation failed.")
        except Exception:
            detail = res.text or "Validation failed."
        return {
            "valid": False,
            "error": detail,
            "requires_approval": False,
        }

    def execute_purchase(self, user_id: int, game_ids: List[int]) -> Dict[str, Any]:
        """POST /purchases/execute: Commit atomic purchase transaction in backend."""
        payload = {"user_id": user_id, "game_ids": game_ids}
        res = self._request("POST", "/purchases/execute", json_data=payload)
        if res.is_success:
            data = res.json()
            # Extract purchased titles for backward compatibility
            purchased_titles = []
            for p in data.get("purchases", []):
                game = p.get("game")
                if game and game.get("title"):
                    purchased_titles.append(game["title"])
            return {
                "success": data.get("success", True),
                "message": data.get("message", "Purchase executed successfully!"),
                "new_wallet_balance": data.get("new_wallet_balance", 0.0),
                "purchased_games": purchased_titles,
            }
        try:
            detail = res.json().get("detail", "Transaction failed.")
        except Exception:
            detail = res.text or "Transaction failed."
        return {
            "success": False,
            "error": detail,
        }

    def close(self):
        """Close the underlying HTTP client session."""
        if self._client is not None and not self._client.is_closed:
            self._client.close()
            self._client = None


# Singleton instance for application-wide assistant layer usage
backend_api_client = BackendApiClient()
