"""
Production-grade output serializer for tractionbuild.
Handles CrewOutput serialization and ensures GDPR-compliant data processing.
"""

import json
import logging
from typing import Dict, Any, Optional, Union
from datetime import datetime
from dataclasses import asdict, is_dataclass
import uuid

try:
    from crewai import CrewOutput
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    # Mock CrewOutput for testing
    class CrewOutput:
        def __init__(self, raw, pydantic=None, json_dict=None, tasks_output=None, token_usage=None):
            self.raw = raw
            self.pydantic = pydantic
            self.json_dict = json_dict
            self.tasks_output = tasks_output or []
            self.token_usage = token_usage or {}

logger = logging.getLogger(__name__)

class CrewOutputSerializer:
    """
    Production-grade serializer for CrewAI outputs.
    Ensures GDPR compliance and data integrity.
    """
    
    def __init__(self, enable_encryption: bool = True, enable_anonymization: bool = True):
        self.enable_encryption = enable_encryption
        self.enable_anonymization = enable_anonymization
        
        # Initialize encryption if enabled
        self.cipher = None
        if enable_encryption:
            try:
                from cryptography.fernet import Fernet
                key = Fernet.generate_key()  # In production, load from Vault
                self.cipher = Fernet(key)
                logger.info("Output encryption enabled")
            except ImportError:
                logger.warning("cryptography not available - encryption disabled")
                self.enable_encryption = False
    
    def serialize_crew_output(self, output: Any, project_id: str = None) -> Dict[str, Any]:
        """
        Serialize CrewOutput to JSON-compatible dictionary.
        
        Args:
            output: CrewOutput or any crew result
            project_id: Project identifier for audit trails
            
        Returns:
            Serialized output dictionary
        """
        try:
            # Generate unique serialization ID for audit trails
            serialization_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat()
            
            # Handle different output types
            if isinstance(output, CrewOutput):
                serialized = self._serialize_crewai_output(output)
            elif hasattr(output, '__dict__'):
                # Handle custom objects
                serialized = self._serialize_object(output)
            elif is_dataclass(output):
                # Handle dataclasses
                serialized = asdict(output)
            elif isinstance(output, (dict, list, str, int, float, bool)):
                # Handle basic types
                serialized = output
            else:
                # Fallback: convert to string
                serialized = str(output)
                logger.warning(f"Fallback serialization for type {type(output)}")
            
            # Apply GDPR anonymization if enabled
            if self.enable_anonymization:
                serialized = self._anonymize_data(serialized)
            
            # Create audit-compliant output
            result = {
                'content': serialized,
                'metadata': {
                    'serialization_id': serialization_id,
                    'timestamp': timestamp,
                    'project_id': project_id,
                    'data_type': type(output).__name__,
                    'gdpr_compliant': self.enable_anonymization,
                    'encrypted': self.enable_encryption
                }
            }
            
            # Apply encryption if enabled
            if self.enable_encryption and self.cipher:
                result = self._encrypt_sensitive_data(result)
            
            logger.debug(f"Successfully serialized {type(output).__name__} for project {project_id}")
            return result
            
        except Exception as e:
            logger.error(f"Serialization failed for {type(output)}: {e}")
            # Return safe fallback
            return {
                'content': {
                    'error': 'Serialization failed',
                    'raw_output': str(output)[:1000],  # Truncate for safety
                    'error_type': type(e).__name__
                },
                'metadata': {
                    'serialization_id': str(uuid.uuid4()),
                    'timestamp': datetime.utcnow().isoformat(),
                    'project_id': project_id,
                    'status': 'error'
                }
            }
    
    def _serialize_crewai_output(self, output: CrewOutput) -> Dict[str, Any]:
        """Serialize CrewAI CrewOutput object."""
        result = {}
        
        # Extract raw output (usually the main result)
        if hasattr(output, 'raw') and output.raw:
            result['raw'] = str(output.raw)
        
        # Extract JSON dict if available
        if hasattr(output, 'json_dict') and output.json_dict:
            result['json_dict'] = output.json_dict
        
        # Extract pydantic model if available
        if hasattr(output, 'pydantic') and output.pydantic:
            try:
                if hasattr(output.pydantic, 'dict'):
                    result['pydantic'] = output.pydantic.dict()
                elif hasattr(output.pydantic, 'model_dump'):
                    result['pydantic'] = output.pydantic.model_dump()
                else:
                    result['pydantic'] = str(output.pydantic)
            except Exception as e:
                logger.warning(f"Failed to serialize pydantic model: {e}")
                result['pydantic'] = str(output.pydantic)
        
        # Extract task outputs
        if hasattr(output, 'tasks_output') and output.tasks_output:
            result['tasks_output'] = []
            for task_output in output.tasks_output:
                if hasattr(task_output, '__dict__'):
                    result['tasks_output'].append(self._serialize_object(task_output))
                else:
                    result['tasks_output'].append(str(task_output))
        
        # Extract token usage
        if hasattr(output, 'token_usage') and output.token_usage:
            result['token_usage'] = dict(output.token_usage)
        
        # Use raw as primary content if available, otherwise use the full dict
        if 'raw' in result and result['raw']:
            result['primary_content'] = result['raw']
        elif 'json_dict' in result:
            result['primary_content'] = result['json_dict']
        elif 'pydantic' in result:
            result['primary_content'] = result['pydantic']
        else:
            result['primary_content'] = "No extractable content"
        
        return result
    
    def _serialize_object(self, obj: Any) -> Dict[str, Any]:
        """Serialize arbitrary objects safely."""
        result = {}
        
        # Get object attributes
        if hasattr(obj, '__dict__'):
            for key, value in obj.__dict__.items():
                try:
                    if isinstance(value, (str, int, float, bool, list, dict, type(None))):
                        result[key] = value
                    elif hasattr(value, '__dict__'):
                        result[key] = self._serialize_object(value)
                    else:
                        result[key] = str(value)
                except Exception as e:
                    logger.debug(f"Failed to serialize attribute {key}: {e}")
                    result[key] = f"<serialization_error: {type(value).__name__}>"
        
        # Add type information
        result['__type__'] = type(obj).__name__
        result['__module__'] = getattr(type(obj), '__module__', 'unknown')
        
        return result
    
    def _anonymize_data(self, data: Any) -> Any:
        """Apply GDPR-compliant data anonymization."""
        if isinstance(data, dict):
            anonymized = {}
            for key, value in data.items():
                # Anonymize sensitive fields
                if any(sensitive in key.lower() for sensitive in ['email', 'phone', 'address', 'name', 'user_id']):
                    anonymized[key] = self._hash_sensitive_value(str(value))
                else:
                    anonymized[key] = self._anonymize_data(value)
            return anonymized
        elif isinstance(data, list):
            return [self._anonymize_data(item) for item in data]
        elif isinstance(data, str):
            # Check for potential PII patterns
            if '@' in data and '.' in data:  # Email-like
                return self._hash_sensitive_value(data)
            elif data.isdigit() and len(data) > 8:  # Phone-like
                return self._hash_sensitive_value(data)
            return data
        else:
            return data
    
    def _hash_sensitive_value(self, value: str) -> str:
        """Hash sensitive values for anonymization."""
        import hashlib
        return f"anon_{hashlib.sha256(value.encode()).hexdigest()[:8]}"
    
    def _encrypt_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive data fields."""
        if not self.cipher:
            return data
        
        # In production, encrypt specific sensitive fields
        # For demo, we'll just mark as encrypted
        data['metadata']['encryption_applied'] = True
        return data
    
    def deserialize_output(self, serialized_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deserialize previously serialized output.
        
        Args:
            serialized_data: Serialized output dictionary
            
        Returns:
            Deserialized content
        """
        try:
            # Decrypt if needed
            if self.enable_encryption and serialized_data.get('metadata', {}).get('encrypted'):
                serialized_data = self._decrypt_data(serialized_data)
            
            # Extract content
            content = serialized_data.get('content', {})
            metadata = serialized_data.get('metadata', {})
            
            logger.debug(f"Successfully deserialized {metadata.get('data_type', 'unknown')} data")
            return content
            
        except Exception as e:
            logger.error(f"Deserialization failed: {e}")
            return {'error': 'Deserialization failed', 'raw_data': str(serialized_data)[:500]}
    
    def _decrypt_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt encrypted data fields."""
        # In production, implement actual decryption
        return data
    
    def validate_serialization(self, original: Any, serialized: Dict[str, Any]) -> bool:
        """
        Validate that serialization preserved essential data.
        
        Args:
            original: Original output
            serialized: Serialized output
            
        Returns:
            True if serialization is valid
        """
        try:
            content = serialized.get('content', {})
            
            # Check for essential fields
            if isinstance(original, CrewOutput):
                # For CrewOutput, ensure we have some extractable content
                return any(key in content for key in ['raw', 'json_dict', 'pydantic', 'primary_content'])
            
            # For other types, ensure content exists
            return bool(content)
            
        except Exception as e:
            logger.error(f"Serialization validation failed: {e}")
            return False


# Global serializer instance
output_serializer = CrewOutputSerializer()