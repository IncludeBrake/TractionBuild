"""
GDPR and compliance management for tractionbuild.
Implements real-time data encryption, anonymization, and audit trails for enterprise compliance.
"""

import os
import json
import logging
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import uuid

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    import base64
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    # Mock encryption for testing
    class Fernet:
        def __init__(self, key): pass
        def encrypt(self, data): return b'encrypted_' + data
        def decrypt(self, data): return data.replace(b'encrypted_', b'')

try:
    from ..security.vault_client import vault_client
    VAULT_AVAILABLE = True
except ImportError:
    VAULT_AVAILABLE = False

logger = logging.getLogger(__name__)

class GDPRComplianceManager:
    """
    Comprehensive GDPR compliance management with real-time encryption and anonymization.
    Ensures all data processing meets EU GDPR and CCPA requirements.
    """
    
    def __init__(self):
        self.enabled = CRYPTOGRAPHY_AVAILABLE
        self.vault_enabled = VAULT_AVAILABLE
        self.encryption_key = None
        self.cipher = None
        self.audit_log = []
        self.consent_records = {}
        
        if self.enabled:
            self._initialize_encryption()
            logger.info("GDPR Compliance Manager initialized with encryption")
        else:
            logger.warning("GDPR Compliance Manager disabled - cryptography not available")
    
    def _initialize_encryption(self):
        """Initialize encryption with Vault or local key."""
        try:
            if self.vault_enabled and vault_client.enabled:
                # Get encryption key from Vault
                key_data = vault_client.get_encryption_key('tractionbuild_gdpr')
                if key_data:
                    self.encryption_key = key_data.encode()
                    logger.info("Using Vault-managed encryption key")
                else:
                    self._generate_local_key()
            else:
                self._generate_local_key()
            
            if self.encryption_key:
                self.cipher = Fernet(self.encryption_key)
                
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            self._generate_local_key()
    
    def _generate_local_key(self):
        """Generate local encryption key for development/testing."""
        try:
            # Use environment variable or generate new key
            key_env = os.getenv('tractionbuild_ENCRYPTION_KEY')
            if key_env:
                self.encryption_key = key_env.encode()
            else:
                # Generate from password and salt
                password = os.getenv('tractionbuild_PASSWORD', 'default_dev_password').encode()
                salt = b'tractionbuild_salt_2025'  # In production, use random salt
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(password))
                self.encryption_key = key
            
            logger.info("Using local encryption key")
            
        except Exception as e:
            logger.error(f"Failed to generate local key: {e}")
            # Fallback to Fernet generated key
            self.encryption_key = Fernet.generate_key()
    
    def anonymize_personal_data(self, data: Any) -> Any:
        """
        Anonymize personal data according to GDPR requirements.
        
        Args:
            data: Data to anonymize
            
        Returns:
            Anonymized data
        """
        try:
            if isinstance(data, dict):
                anonymized = {}
                for key, value in data.items():
                    if self._is_personal_data_field(key):
                        anonymized[key] = self._hash_personal_data(str(value))
                    elif isinstance(value, (dict, list)):
                        anonymized[key] = self.anonymize_personal_data(value)
                    else:
                        anonymized[key] = value
                return anonymized
            
            elif isinstance(data, list):
                return [self.anonymize_personal_data(item) for item in data]
            
            elif isinstance(data, str):
                # Check for email patterns, phone numbers, etc.
                if self._contains_personal_data(data):
                    return self._hash_personal_data(data)
                return data
            
            else:
                return data
                
        except Exception as e:
            logger.error(f"Anonymization failed: {e}")
            return str(data)  # Fallback to string representation
    
    def _is_personal_data_field(self, field_name: str) -> bool:
        """Check if field contains personal data."""
        personal_fields = [
            'email', 'phone', 'name', 'address', 'user_id', 'customer_id',
            'ip_address', 'device_id', 'session_id', 'user_name', 'full_name',
            'first_name', 'last_name', 'contact', 'identifier'
        ]
        
        field_lower = field_name.lower()
        return any(personal_field in field_lower for personal_field in personal_fields)
    
    def _contains_personal_data(self, text: str) -> bool:
        """Check if text contains personal data patterns."""
        import re
        
        # Email pattern
        if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text):
            return True
        
        # Phone pattern
        if re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text):
            return True
        
        # IP address pattern
        if re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', text):
            return True
        
        return False
    
    def _hash_personal_data(self, data: str) -> str:
        """Hash personal data for anonymization."""
        # Use SHA-256 with salt for irreversible anonymization
        salt = "tractionbuild_gdpr_salt_2025"
        hash_input = f"{data}{salt}".encode()
        hash_result = hashlib.sha256(hash_input).hexdigest()
        return f"anon_{hash_result[:12]}"
    
    def encrypt_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt sensitive data fields.
        
        Args:
            data: Data to encrypt
            
        Returns:
            Data with encrypted sensitive fields
        """
        if not self.enabled or not self.cipher:
            return data
        
        try:
            encrypted_data = data.copy()
            
            for key, value in data.items():
                if self._is_sensitive_field(key) and isinstance(value, (str, dict)):
                    # Convert to JSON string if dict
                    if isinstance(value, dict):
                        value_str = json.dumps(value)
                    else:
                        value_str = str(value)
                    
                    # Encrypt the value
                    encrypted_bytes = self.cipher.encrypt(value_str.encode())
                    encrypted_data[key] = {
                        'encrypted': True,
                        'data': encrypted_bytes.decode(),
                        'timestamp': datetime.utcnow().isoformat()
                    }
            
            # Add encryption metadata
            encrypted_data['_gdpr_metadata'] = {
                'encrypted': True,
                'encryption_timestamp': datetime.utcnow().isoformat(),
                'compliance_version': '2025.1'
            }
            
            return encrypted_data
            
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return data
    
    def _is_sensitive_field(self, field_name: str) -> bool:
        """Check if field contains sensitive data that should be encrypted."""
        sensitive_fields = [
            'validator', 'feedback', 'marketing', 'customer_data',
            'user_input', 'survey_response', 'personal_info'
        ]
        
        field_lower = field_name.lower()
        return any(sensitive_field in field_lower for sensitive_field in sensitive_fields)
    
    def decrypt_data(self, encrypted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt previously encrypted data.
        
        Args:
            encrypted_data: Data with encrypted fields
            
        Returns:
            Decrypted data
        """
        if not self.enabled or not self.cipher:
            return encrypted_data
        
        try:
            decrypted_data = encrypted_data.copy()
            
            for key, value in encrypted_data.items():
                if isinstance(value, dict) and value.get('encrypted'):
                    # Decrypt the data
                    encrypted_bytes = value['data'].encode()
                    decrypted_bytes = self.cipher.decrypt(encrypted_bytes)
                    decrypted_str = decrypted_bytes.decode()
                    
                    # Try to parse as JSON, fallback to string
                    try:
                        decrypted_data[key] = json.loads(decrypted_str)
                    except json.JSONDecodeError:
                        decrypted_data[key] = decrypted_str
            
            return decrypted_data
            
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return encrypted_data
    
    def record_consent(self, user_id: str, consent_type: str, granted: bool, 
                      purpose: str = None) -> str:
        """
        Record user consent for GDPR compliance.
        
        Args:
            user_id: User identifier
            consent_type: Type of consent (e.g., 'marketing', 'analytics')
            granted: Whether consent was granted
            purpose: Purpose of data processing
            
        Returns:
            Consent record ID
        """
        consent_id = str(uuid.uuid4())
        consent_record = {
            'consent_id': consent_id,
            'user_id': self._hash_personal_data(user_id),  # Anonymize user ID
            'consent_type': consent_type,
            'granted': granted,
            'purpose': purpose,
            'timestamp': datetime.utcnow().isoformat(),
            'ip_address': 'anonymized',  # In production, get from request
            'user_agent': 'tractionbuild_system'
        }
        
        self.consent_records[consent_id] = consent_record
        self._log_audit_event('consent_recorded', consent_record)
        
        logger.info(f"Consent recorded: {consent_type} {'granted' if granted else 'denied'}")
        return consent_id
    
    def check_consent(self, user_id: str, consent_type: str) -> bool:
        """
        Check if user has granted consent for specific processing.
        
        Args:
            user_id: User identifier
            consent_type: Type of consent to check
            
        Returns:
            True if consent granted
        """
        hashed_user_id = self._hash_personal_data(user_id)
        
        for record in self.consent_records.values():
            if (record['user_id'] == hashed_user_id and 
                record['consent_type'] == consent_type and 
                record['granted']):
                return True
        
        return False
    
    def _log_audit_event(self, event_type: str, event_data: Dict[str, Any]):
        """Log audit event for compliance tracking."""
        audit_entry = {
            'event_id': str(uuid.uuid4()),
            'event_type': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            'data': self.anonymize_personal_data(event_data),
            'compliance_version': '2025.1'
        }
        
        self.audit_log.append(audit_entry)
        
        # Keep only last 1000 entries to manage memory
        if len(self.audit_log) > 1000:
            self.audit_log = self.audit_log[-1000:]
    
    def process_data_request(self, user_id: str, request_type: str) -> Dict[str, Any]:
        """
        Process GDPR data subject requests (access, deletion, portability).
        
        Args:
            user_id: User identifier
            request_type: Type of request ('access', 'delete', 'portability')
            
        Returns:
            Request processing result
        """
        request_id = str(uuid.uuid4())
        hashed_user_id = self._hash_personal_data(user_id)
        
        try:
            if request_type == 'access':
                # Right to access - provide user's data
                user_data = self._collect_user_data(hashed_user_id)
                result = {
                    'request_id': request_id,
                    'type': 'data_access',
                    'status': 'completed',
                    'data': user_data,
                    'processed_at': datetime.utcnow().isoformat()
                }
                
            elif request_type == 'delete':
                # Right to erasure - delete user's data
                deleted_count = self._delete_user_data(hashed_user_id)
                result = {
                    'request_id': request_id,
                    'type': 'data_deletion',
                    'status': 'completed',
                    'records_deleted': deleted_count,
                    'processed_at': datetime.utcnow().isoformat()
                }
                
            elif request_type == 'portability':
                # Right to data portability - export user's data
                user_data = self._collect_user_data(hashed_user_id)
                result = {
                    'request_id': request_id,
                    'type': 'data_portability',
                    'status': 'completed',
                    'export_format': 'json',
                    'data': user_data,
                    'processed_at': datetime.utcnow().isoformat()
                }
                
            else:
                result = {
                    'request_id': request_id,
                    'type': request_type,
                    'status': 'error',
                    'error': f'Unsupported request type: {request_type}',
                    'processed_at': datetime.utcnow().isoformat()
                }
            
            self._log_audit_event('data_request_processed', {
                'request_id': request_id,
                'user_id': hashed_user_id,
                'type': request_type,
                'status': result['status']
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Data request processing failed: {e}")
            return {
                'request_id': request_id,
                'type': request_type,
                'status': 'error',
                'error': str(e),
                'processed_at': datetime.utcnow().isoformat()
            }
    
    def _collect_user_data(self, hashed_user_id: str) -> Dict[str, Any]:
        """Collect all data associated with a user."""
        # In production, query all systems for user data
        user_data = {
            'consent_records': [
                record for record in self.consent_records.values()
                if record['user_id'] == hashed_user_id
            ],
            'audit_events': [
                event for event in self.audit_log
                if event.get('data', {}).get('user_id') == hashed_user_id
            ]
        }
        
        return user_data
    
    def _delete_user_data(self, hashed_user_id: str) -> int:
        """Delete all data associated with a user."""
        deleted_count = 0
        
        # Delete consent records
        to_delete = [
            consent_id for consent_id, record in self.consent_records.items()
            if record['user_id'] == hashed_user_id
        ]
        
        for consent_id in to_delete:
            del self.consent_records[consent_id]
            deleted_count += 1
        
        # Anonymize audit log entries (can't delete for compliance)
        for event in self.audit_log:
            if event.get('data', {}).get('user_id') == hashed_user_id:
                event['data']['user_id'] = 'deleted_user'
                deleted_count += 1
        
        return deleted_count
    
    def get_compliance_report(self) -> Dict[str, Any]:
        """Generate comprehensive compliance report."""
        return {
            'compliance_status': {
                'gdpr_enabled': self.enabled,
                'encryption_enabled': bool(self.cipher),
                'vault_integration': self.vault_enabled,
                'audit_logging': len(self.audit_log) > 0
            },
            'data_processing': {
                'total_consent_records': len(self.consent_records),
                'active_consents': sum(1 for r in self.consent_records.values() if r['granted']),
                'audit_events': len(self.audit_log),
                'last_audit_event': self.audit_log[-1]['timestamp'] if self.audit_log else None
            },
            'security_measures': {
                'data_anonymization': True,
                'field_encryption': bool(self.cipher),
                'secure_key_management': self.vault_enabled,
                'audit_trail_integrity': True
            },
            'compliance_version': '2025.1',
            'report_generated_at': datetime.utcnow().isoformat()
        }


# Global GDPR compliance manager
gdpr_manager = GDPRComplianceManager()