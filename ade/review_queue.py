from typing import List, Optional
import logging
from .database import DatabaseManager
from .models import ReviewItem

logger = logging.getLogger('ADE.ReviewQueue')

class ReviewQueueManager:
    """Manages the HITL review workflow."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def add_item(self, job_id: str, source_agent: str, source_data: str,
                 generated_content: str, target_agent: Optional[str] = None) -> int:
        """Add an item to the review queue."""
        query = """
        INSERT INTO ReviewQueue (job_id, source_agent, target_agent, source_data, generated_content)
        VALUES (?, ?, ?, ?, ?)
        """
        item_id = self.db.execute_update(
            query, (job_id, source_agent, target_agent, source_data, generated_content)
        )
        logger.info(f"Added review item {item_id} from {source_agent}")
        return item_id

    def get_pending_items(self, job_id: str) -> List[ReviewItem]:
        """Get all pending review items for a job."""
        query = "SELECT * FROM ReviewQueue WHERE job_id = ? AND status = 'Pending'"
        results = self.db.execute_query(query, (job_id,))
        return [
            ReviewItem(
                item_id=row['item_id'],
                job_id=row['job_id'],
                status=row['status'],
                source_agent=row['source_agent'],
                target_agent=row['target_agent'],
                source_data=row['source_data'],
                generated_content=row['generated_content'],
                approved_content=row['approved_content'],
                rejection_feedback=row['rejection_feedback']
            )
            for row in results
        ]

    def approve_item(self, item_id: int, approved_content: Optional[str] = None):
        """Approve a review item."""
        if approved_content:
            query = """
            UPDATE ReviewQueue
            SET status = 'Approved', approved_content = ?, updated_at = CURRENT_TIMESTAMP
            WHERE item_id = ?
            """
            self.db.execute_update(query, (approved_content, item_id))
        else:
            query = """
            UPDATE ReviewQueue
            SET status = 'Approved', approved_content = generated_content, updated_at = CURRENT_TIMESTAMP
            WHERE item_id = ?
            """
            self.db.execute_update(query, (item_id,))
        logger.info(f"Approved review item {item_id}")

    def reject_item(self, item_id: int, feedback: str):
        """Reject a review item with feedback."""
        query = """
        UPDATE ReviewQueue
        SET status = 'Rejected', rejection_feedback = ?, updated_at = CURRENT_TIMESTAMP
        WHERE item_id = ?
        """
        self.db.execute_update(query, (feedback, item_id))
        logger.info(f"Rejected review item {item_id}")

    def get_approved_items(self, job_id: str) -> List[ReviewItem]:
        """Get all approved items for a job."""
        query = "SELECT * FROM ReviewQueue WHERE job_id = ? AND status = 'Approved'"
        results = self.db.execute_query(query, (job_id,))
        return [
            ReviewItem(
                item_id=row['item_id'],
                job_id=row['job_id'],
                status=row['status'],
                source_agent=row['source_agent'],
                target_agent=row['target_agent'],
                source_data=row['source_data'],
                generated_content=row['generated_content'],
                approved_content=row['approved_content'],
                rejection_feedback=row['rejection_feedback']
            )
            for row in results
        ]
