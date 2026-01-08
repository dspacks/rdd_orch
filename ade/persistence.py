import json
import os
import glob
import logging
from typing import List, Dict, Optional
from .models import ProcessingCheckpoint

logger = logging.getLogger('ADE.Persistence')

class ProgressPersistenceManager:
    """
    Manages progress persistence for long-running jobs.

    Features:
    - Save checkpoint after each variable
    - Resume from last checkpoint on interruption
    - Multiple checkpoint types (after each pipeline stage)
    - Checkpoint file management
    """

    def __init__(self, checkpoint_dir: str = "./checkpoints"):
        self.checkpoint_dir = checkpoint_dir
        os.makedirs(checkpoint_dir, exist_ok=True)
        self.logger = logger

    def save_checkpoint(self, checkpoint: ProcessingCheckpoint) -> str:
        """
        Save a processing checkpoint to disk.

        Args:
            checkpoint: The checkpoint data to save

        Returns:
            Path to the saved checkpoint file
        """
        checkpoint_file = f"{self.checkpoint_dir}/{checkpoint.job_id}_{checkpoint.stage}.json"

        checkpoint_data = {
            'job_id': checkpoint.job_id,
            'checkpoint_time': checkpoint.checkpoint_time,
            'stage': checkpoint.stage,
            'variables_processed': checkpoint.variables_processed,
            'total_variables': checkpoint.total_variables,
            'parsed_data': checkpoint.parsed_data,
            'analyzed_data': checkpoint.analyzed_data,
            'processed_variables': checkpoint.processed_variables or []
        }

        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)

        self.logger.info(f"Saved checkpoint: {checkpoint_file}")
        # print(f"💾 Checkpoint saved: {checkpoint.stage} ({checkpoint.variables_processed}/{checkpoint.total_variables} vars)")

        return checkpoint_file

    def load_checkpoint(self, job_id: str, stage: str = None) -> Optional[ProcessingCheckpoint]:
        """
        Load a checkpoint from disk.

        Args:
            job_id: The job ID to load
            stage: Specific stage to load, or None for latest

        Returns:
            ProcessingCheckpoint if found, None otherwise
        """
        if stage:
            checkpoint_file = f"{self.checkpoint_dir}/{job_id}_{stage}.json"
            if not os.path.exists(checkpoint_file):
                return None
        else:
            # Find latest checkpoint for this job
            pattern = f"{self.checkpoint_dir}/{job_id}_*.json"
            checkpoint_files = glob.glob(pattern)

            if not checkpoint_files:
                return None

            # Get most recent file
            checkpoint_file = max(checkpoint_files, key=os.path.getmtime)

        try:
            with open(checkpoint_file, 'r') as f:
                data = json.load(f)

            checkpoint = ProcessingCheckpoint(
                job_id=data['job_id'],
                checkpoint_time=data['checkpoint_time'],
                stage=data['stage'],
                variables_processed=data['variables_processed'],
                total_variables=data['total_variables'],
                parsed_data=data.get('parsed_data'),
                analyzed_data=data.get('analyzed_data'),
                processed_variables=data.get('processed_variables', []),
                checkpoint_file=checkpoint_file
            )

            self.logger.info(f"Loaded checkpoint: {checkpoint_file}")
            # print(f"📂 Checkpoint loaded: {checkpoint.stage} ({checkpoint.variables_processed}/{checkpoint.total_variables} vars)")

            return checkpoint

        except Exception as e:
            self.logger.error(f"Failed to load checkpoint: {e}")
            return None

    def list_checkpoints(self, job_id: str = None) -> List[Dict]:
        """List available checkpoints."""
        pattern = f"{self.checkpoint_dir}/{job_id}_*.json" if job_id else f"{self.checkpoint_dir}/*.json"
        files = glob.glob(pattern)
        checkpoints = []
        for f in files:
            try:
                with open(f, 'r') as fh:
                    data = json.load(fh)
                    checkpoints.append({
                        'file': f,
                        'job_id': data.get('job_id'),
                        'stage': data.get('stage'),
                        'time': data.get('checkpoint_time')
                    })
            except:
                pass
        return sorted(checkpoints, key=lambda x: x['time'], reverse=True)
