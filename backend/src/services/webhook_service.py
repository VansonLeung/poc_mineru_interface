from __future__ import annotations

import httpx
from loguru import logger


class WebhookService:
    """Fire-and-forget webhook notifications."""

    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout

    async def notify(self, url: str, payload: dict) -> None:
        """Send webhook notification without retries."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                if response.is_success:
                    logger.info(f"Webhook delivered successfully to {url}")
                else:
                    logger.warning(
                        f"Webhook to {url} returned {response.status_code}: {response.text[:200]}"
                    )
        except httpx.RequestError as exc:
            logger.warning(f"Webhook to {url} failed with error: {exc}")
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Unexpected error sending webhook to {url}: {exc}")
