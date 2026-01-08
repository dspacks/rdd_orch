from dataclasses import dataclass




@dataclass
class APIConfig:
    """Configuration for API rate limits and retry behavior."""
    requests_per_minute: int = 5
    max_retries: int = 3
    base_retry_delay: float = 6.0
    model_name: str = "gemini-2.5-flash-lite"
    batch_size: int = 3

    def __post_init__(self):
        self.min_delay = 60.0 / self.requests_per_minute

    def get_retry_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay for retry attempts."""
        # Exponential backoff: base_delay * (2 ^ attempt)
        return self.base_retry_delay * (2 ** attempt)


class APITier:
    """Predefined API configurations for different Gemini tiers."""
    FREE = APIConfig(
        requests_per_minute=10,
        max_retries=3,
        base_retry_delay=6.0,
        batch_size=7
    )

    PAYG = APIConfig(
        requests_per_minute=360,
        max_retries=3,
        base_retry_delay=2.0,
        batch_size=14
    )

    ENTERPRISE = APIConfig(
        requests_per_minute=1000,
        max_retries=2,
        base_retry_delay=1.0,
        batch_size=28
    )

    CONSERVATIVE = APIConfig(
        requests_per_minute=5,
        max_retries=5,
        base_retry_delay=30.0,
        batch_size=7
    )

    @staticmethod
    def custom(requests_per_minute: int, **kwargs) -> APIConfig:
        return APIConfig(requests_per_minute=requests_per_minute, **kwargs)


# Default configuration
# Set your tier here - use CONSERVATIVE for rate limit issues
API_CONFIG = APITier.CONSERVATIVE
