"""
Workflow Enhancements - Error Handling and Batch Processing Improvements

This module provides enhanced error handling for the main workflow and
improved batch processing with partial failure recovery.
"""

import logging
import traceback
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import time

logger = logging.getLogger(__name__)


# ============================================================================
# Error Handling Decorators
# ============================================================================

def with_error_handling(
    default_return: Any = None,
    log_traceback: bool = True,
    reraise: bool = False
):
    """
    Decorator to add error handling to workflow functions.

    Args:
        default_return: Value to return on error
        log_traceback: Whether to log full traceback
        reraise: Whether to re-raise exception after logging

    Example:
        @with_error_handling(default_return={}, log_traceback=True)
        def process_data_dictionary(self, source_data):
            # Your code here
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                if log_traceback:
                    logger.error(f"Traceback: {traceback.format_exc()}")

                if reraise:
                    raise

                return default_return
        return wrapper
    return decorator


# ============================================================================
# Batch Processing Status
# ============================================================================

class BatchItemStatus(str, Enum):
    """Status for individual batch items."""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class BatchItem:
    """Individual item in a batch."""
    item_id: str
    data: Any
    status: BatchItemStatus = BatchItemStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    retry_count: int = 0

    @property
    def duration(self) -> Optional[float]:
        """Get processing duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


@dataclass
class BatchResult:
    """Result of batch processing."""
    batch_id: str
    total_items: int
    successful: int = 0
    failed: int = 0
    skipped: int = 0
    items: List[BatchItem] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    errors: List[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_items == 0:
            return 0.0
        return self.successful / self.total_items

    @property
    def duration(self) -> Optional[float]:
        """Get total processing duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def get_summary(self) -> Dict[str, Any]:
        """Get human-readable summary."""
        return {
            'batch_id': self.batch_id,
            'total_items': self.total_items,
            'successful': self.successful,
            'failed': self.failed,
            'skipped': self.skipped,
            'success_rate': f"{self.success_rate * 100:.1f}%",
            'duration_seconds': self.duration,
            'errors': self.errors[:5]  # First 5 errors
        }


# ============================================================================
# Enhanced Batch Processor
# ============================================================================

class EnhancedBatchProcessor:
    """
    Enhanced batch processor with partial failure recovery.

    Features:
    - Item-level status tracking
    - Partial failure recovery (continues on errors)
    - Retry logic for failed items
    - Progress callbacks
    - Detailed result reporting
    """

    def __init__(
        self,
        max_retries: int = 2,
        retry_delay: float = 1.0,
        continue_on_error: bool = True
    ):
        """
        Initialize batch processor.

        Args:
            max_retries: Maximum retry attempts per item
            retry_delay: Delay between retries in seconds
            continue_on_error: Continue processing if item fails
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.continue_on_error = continue_on_error

    def process_batch(
        self,
        items: List[Any],
        processor_func: Callable[[Any], Any],
        batch_id: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> BatchResult:
        """
        Process a batch of items with error handling.

        Args:
            items: List of items to process
            processor_func: Function to process each item
            batch_id: Optional batch identifier
            progress_callback: Optional callback(current, total) for progress

        Returns:
            BatchResult with detailed status

        Example:
            >>> processor = EnhancedBatchProcessor()
            >>> result = processor.process_batch(
            ...     items=fields,
            ...     processor_func=lambda f: agent.process(f),
            ...     progress_callback=lambda cur, total: print(f"{cur}/{total}")
            ... )
            >>> print(f"Success rate: {result.success_rate * 100}%")
        """
        batch_id = batch_id or f"batch_{int(time.time())}"
        result = BatchResult(
            batch_id=batch_id,
            total_items=len(items)
        )

        batch_items = [
            BatchItem(item_id=f"item_{i}", data=item)
            for i, item in enumerate(items)
        ]

        for idx, batch_item in enumerate(batch_items):
            # Progress callback
            if progress_callback:
                progress_callback(idx + 1, len(batch_items))

            # Process item with retry logic
            self._process_item(batch_item, processor_func, result)

            # Add to result
            result.items.append(batch_item)

            # Update counters
            if batch_item.status == BatchItemStatus.SUCCESS:
                result.successful += 1
            elif batch_item.status == BatchItemStatus.FAILED:
                result.failed += 1
                if not self.continue_on_error:
                    logger.warning("Stopping batch due to error (continue_on_error=False)")
                    # Mark remaining as skipped
                    for remaining_item in batch_items[idx + 1:]:
                        remaining_item.status = BatchItemStatus.SKIPPED
                        result.items.append(remaining_item)
                        result.skipped += 1
                    break
            elif batch_item.status == BatchItemStatus.SKIPPED:
                result.skipped += 1

        result.end_time = datetime.now()
        return result

    def _process_item(
        self,
        batch_item: BatchItem,
        processor_func: Callable,
        batch_result: BatchResult
    ):
        """Process a single batch item with retry logic."""
        batch_item.status = BatchItemStatus.PROCESSING
        batch_item.start_time = datetime.now()

        for attempt in range(self.max_retries + 1):
            try:
                # Process item
                batch_item.result = processor_func(batch_item.data)
                batch_item.status = BatchItemStatus.SUCCESS
                batch_item.end_time = datetime.now()
                return

            except Exception as e:
                error_msg = f"Error processing {batch_item.item_id}: {e}"
                logger.error(error_msg)

                batch_item.retry_count = attempt + 1

                if attempt < self.max_retries:
                    logger.info(f"Retrying {batch_item.item_id} (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(self.retry_delay)
                else:
                    # Max retries exceeded
                    batch_item.status = BatchItemStatus.FAILED
                    batch_item.error = str(e)
                    batch_item.end_time = datetime.now()
                    batch_result.errors.append(error_msg)
                    return


# ============================================================================
# Workflow Error Context Manager
# ============================================================================

class WorkflowErrorHandler:
    """
    Context manager for workflow error handling.

    Provides structured error handling with automatic cleanup and status updates.

    Example:
        with WorkflowErrorHandler(job_id, db) as handler:
            # Your workflow code
            result = orchestrator.process_data_dictionary(...)

            # Set success
            handler.set_success(result)

        # Errors are automatically caught and logged
        # Job status is automatically updated
    """

    def __init__(
        self,
        job_id: str,
        db_manager,
        cleanup_callback: Optional[Callable] = None
    ):
        """
        Initialize error handler.

        Args:
            job_id: Job ID to update on error
            db_manager: Database manager instance
            cleanup_callback: Optional cleanup function
        """
        self.job_id = job_id
        self.db = db_manager
        self.cleanup_callback = cleanup_callback
        self.success = False
        self.result = None
        self.error = None

    def __enter__(self):
        """Enter context."""
        logger.info(f"Starting workflow for job {self.job_id}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context with error handling."""
        if exc_type is not None:
            # Error occurred
            self.error = str(exc_val)
            logger.error(f"Workflow failed for job {self.job_id}: {exc_val}")
            logger.error(f"Traceback: {traceback.format_exc()}")

            # Update job status to Failed
            try:
                self.db.execute_update(
                    "UPDATE Jobs SET status = 'Failed', metadata = json_set(metadata, '$.error', ?) WHERE job_id = ?",
                    (self.error, self.job_id)
                )
                logger.info(f"✓ Updated job {self.job_id} status to Failed")
            except Exception as db_error:
                logger.error(f"✗ Failed to update job status: {db_error}")

            # Run cleanup
            if self.cleanup_callback:
                try:
                    self.cleanup_callback()
                except Exception as cleanup_error:
                    logger.error(f"Cleanup failed: {cleanup_error}")

            # Don't suppress exception
            return False

        else:
            # Success
            if self.success:
                logger.info(f"✓ Workflow completed successfully for job {self.job_id}")
                try:
                    self.db.execute_update(
                        "UPDATE Jobs SET status = 'Completed' WHERE job_id = ?",
                        (self.job_id,)
                    )
                except Exception as db_error:
                    logger.error(f"✗ Failed to update job status: {db_error}")
            else:
                logger.warning(f"Workflow finished but success not set for job {self.job_id}")

            return True

    def set_success(self, result: Any = None):
        """Mark workflow as successful."""
        self.success = True
        self.result = result


# ============================================================================
# Utility Functions
# ============================================================================

def safe_workflow_execution(
    workflow_func: Callable,
    job_id: str,
    db_manager,
    *args,
    **kwargs
) -> tuple[bool, Any, Optional[str]]:
    """
    Execute a workflow function with comprehensive error handling.

    Args:
        workflow_func: The workflow function to execute
        job_id: Job ID for tracking
        db_manager: Database manager instance
        *args: Arguments for workflow_func
        **kwargs: Keyword arguments for workflow_func

    Returns:
        Tuple of (success: bool, result: Any, error: Optional[str])

    Example:
        >>> success, result, error = safe_workflow_execution(
        ...     orchestrator.process_data_dictionary,
        ...     job_id="job_123",
        ...     db_manager=db,
        ...     source_data=data
        ... )
        >>> if success:
        ...     print(f"Success: {result}")
        >>> else:
        ...     print(f"Error: {error}")
    """
    with WorkflowErrorHandler(job_id, db_manager) as handler:
        try:
            result = workflow_func(*args, **kwargs)
            handler.set_success(result)
            return True, result, None
        except Exception as e:
            return False, None, str(e)


def create_progress_tracker(total: int) -> Callable[[int], None]:
    """
    Create a simple progress tracker.

    Args:
        total: Total number of items

    Returns:
        Function to call with current progress

    Example:
        >>> track = create_progress_tracker(100)
        >>> for i in range(100):
        ...     track(i + 1)  # Prints progress every 10%
    """
    last_percentage = 0

    def track(current: int):
        nonlocal last_percentage
        percentage = int((current / total) * 100)

        # Log every 10%
        if percentage >= last_percentage + 10:
            logger.info(f"Progress: {percentage}% ({current}/{total})")
            last_percentage = percentage

    return track

