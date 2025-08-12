import copy
import json
import logging
import boto3
from botocore.exceptions import NoCredentialsError
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

class DataHandler:
    """
    Manages data cleansing, serialization, and offloading of large artifacts to S3.
    """
    def __init__(self, s3_bucket_name: str, s3_region: str = 'us-east-1'):
        self.s3_bucket_name = s3_bucket_name
        self.s3_client = boto3.client('s3', region_name=s3_region)
        # Keys in project_data that contain large artifacts to be moved to S3
        self.large_artifact_keys = [
            "marketing.generated_assets",
            "builder.code_archive",
            "validation.full_report_html"
        ]

    def cleanse_for_serialization(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a deep copy of the project data and removes any non-serializable
        runtime objects before storage.
        """
        clean_data = copy.deepcopy(project_data)
        
        # List of keys for runtime objects that should not be persisted
        transient_keys = ['registry', 'data_handler']
        
        for key in transient_keys:
            if key in clean_data:
                del clean_data[key]
        
        logger.info("Successfully cleansed project data for serialization.")
        return clean_data

    async def offload_large_artifacts_to_s3(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Finds large artifacts in project_data, uploads them to S3, and replaces
        them with an S3 URI pointer.
        """
        project_id = project_data['id']
        temp_dir = Path(f"/tmp/{project_id}")
        temp_dir.mkdir(parents=True, exist_ok=True)

        for key_path in self.large_artifact_keys:
            # Simple key access for now, can be expanded for nested keys
            if '.' in key_path: continue # Placeholder for nested logic
            
            if key_path in project_data and project_data[key_path]:
                artifact_data = project_data[key_path]
                artifact_filename = f"{key_path.replace('.', '_')}.json"
                local_path = temp_dir / artifact_filename
                s3_key = f"projects/{project_id}/artifacts/{artifact_filename}"

                # Write artifact to a temporary local file
                with open(local_path, 'w') as f:
                    json.dump(artifact_data, f, indent=2, default=str)
                
                # Upload to S3
                if self._upload_to_s3(str(local_path), self.s3_bucket_name, s3_key):
                    # Replace the large data with a pointer
                    project_data[key_path] = {'s3_uri': f"s3://{self.s3_bucket_name}/{s3_key}"}
                    logger.info(f"Offloaded artifact '{key_path}' to S3.")
        
        # Clean up temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)
        return project_data

    def _upload_to_s3(self, file_path: str, bucket_name: str, s3_key: str) -> bool:
        """Helper function to upload a single file to S3."""
        try:
            self.s3_client.upload_file(file_path, bucket_name, s3_key)
            return True
        except NoCredentialsError:
            logger.error("S3 credentials not found. Cannot upload artifact.")
            return False
        except Exception as e:
            logger.error(f"Error uploading file to S3: {e}")
            return False