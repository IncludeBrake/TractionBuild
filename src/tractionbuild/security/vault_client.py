"""
HashiCorp Vault integration for tractionbuild.
Provides secure secret management with zero-trust architecture.
"""

import os, logging
from typing import Dict, Any, Optional
import json
from datetime import datetime, timedelta

try:
    import hvac
    VAULT_AVAILABLE = True
except ImportError:
    VAULT_AVAILABLE = False
    print("Warning: hvac not available. Vault integration disabled.")

try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    print("Warning: PyJWT not available. Service account token authentication disabled.")

logger = logging.getLogger(__name__)

class VaultClient:
    """Lazy, env-gated Vault client. Never connects at import time."""
    def __init__(self):
        self._enabled = str(os.getenv("ZTS_VAULT_ENABLED", "0")).lower() in ("1","true","yes")
        self._client = None  # defer actual client init

    def _ensure(self):
        if not self._enabled:
            return False
        if self._client is not None:
            return True
        try:
            import hvac
            addr = os.getenv("VAULT_ADDR", "")
            token = os.getenv("VAULT_TOKEN", "")
            if not addr or not token:
                logger.warning("Vault disabled: missing VAULT_ADDR/VAULT_TOKEN")
                self._enabled = False
                return False
            self._client = hvac.Client(url=addr, token=token)
            return True
        except Exception as e:
            logger.warning("Vault disabled: %s", e)
            self._enabled = False
            self._client = None
            return False

    def get_secret(self, path: str):
        if not self._ensure():
            return None
        try:
            return self._client.secrets.kv.v2.read_secret_version(path=path)["data"]["data"]
        except Exception as e:
            logger.warning("Vault read failed for %s: %s", path, e)
            return None
    
    def set_secret(self, path: str, secret_data: Dict[str, Any]) -> bool:
        """Store a secret in Vault."""
        if not self._ensure():
            logger.error("Cannot store secret - not authenticated")
            return False
        
        try:
            response = self._client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=secret_data
            )
            
            if response:
                logger.info(f"Successfully stored secret at path: {path}")
                return True
            else:
                logger.error(f"Failed to store secret at path: {path}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to store secret at {path}: {e}")
            return False
    
    def get_database_credentials(self, database_name: str) -> Optional[Dict[str, str]]:
        """Get dynamic database credentials from Vault."""
        if not self._ensure():
            return None
        
        try:
            # Request dynamic credentials from database engine
            response = self._client.secrets.database.generate_credentials(name=database_name)
            
            if response and 'data' in response:
                credentials = response['data']
                logger.info(f"Retrieved dynamic credentials for database: {database_name}")
                return {
                    'username': credentials.get('username'),
                    'password': credentials.get('password'),
                    'lease_id': response.get('lease_id'),
                    'lease_duration': response.get('lease_duration')
                }
            else:
                logger.error(f"Failed to generate credentials for database: {database_name}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get database credentials: {e}")
            return None
    
    def get_pki_certificate(self, common_name: str, alt_names: list = None) -> Optional[Dict[str, str]]:
        """Generate a certificate from Vault PKI engine."""
        if not self._ensure():
            return None
        
        try:
            pki_path = os.getenv('VAULT_PKI_PATH', 'pki')
            role_name = os.getenv('VAULT_PKI_ROLE', 'tractionbuild')
            
            cert_data = {
                'common_name': common_name,
                'ttl': '24h'
            }
            
            if alt_names:
                cert_data['alt_names'] = ','.join(alt_names)
            
            response = self._client.secrets.pki.generate_certificate(
                name=role_name,
                mount_point=pki_path,
                extra_params=cert_data
            )
            
            if response and 'data' in response:
                cert_info = response['data']
                logger.info(f"Generated certificate for: {common_name}")
                return {
                    'certificate': cert_info.get('certificate'),
                    'private_key': cert_info.get('private_key'),
                    'ca_chain': cert_info.get('ca_chain'),
                    'serial_number': cert_info.get('serial_number')
                }
            else:
                logger.error(f"Failed to generate certificate for: {common_name}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to generate certificate: {e}")
            return None
    
    def get_encryption_key(self, key_name: str) -> Optional[str]:
        """Get or create an encryption key from Vault transit engine."""
        if not self._ensure():
            return None
        
        try:
            transit_path = os.getenv('VAULT_TRANSIT_PATH', 'transit')
            
            # Try to read the key first
            try:
                response = self._client.secrets.transit.read_key(
                    name=key_name,
                    mount_point=transit_path
                )
                if response:
                    logger.info(f"Retrieved encryption key: {key_name}")
                    return key_name  # Return key name for encryption operations
            except:
                pass  # Key doesn't exist, create it
            
            # Create the key if it doesn't exist
            self._client.secrets.transit.create_key(
                name=key_name,
                mount_point=transit_path,
                key_type='aes256-gcm96'
            )
            
            logger.info(f"Created new encryption key: {key_name}")
            return key_name
            
        except Exception as e:
            logger.error(f"Failed to get encryption key: {e}")
            return None
    
    def encrypt_data(self, key_name: str, plaintext: str) -> Optional[str]:
        """Encrypt data using Vault transit engine."""
        if not self._ensure():
            return None
        
        try:
            transit_path = os.getenv('VAULT_TRANSIT_PATH', 'transit')
            
            response = self._client.secrets.transit.encrypt_data(
                name=key_name,
                mount_point=transit_path,
                plaintext=plaintext
            )
            
            if response and 'data' in response:
                ciphertext = response['data'].get('ciphertext')
                logger.debug(f"Successfully encrypted data with key: {key_name}")
                return ciphertext
            else:
                logger.error(f"Failed to encrypt data with key: {key_name}")
                return None
                
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return None
    
    def decrypt_data(self, key_name: str, ciphertext: str) -> Optional[str]:
        """Decrypt data using Vault transit engine."""
        if not self._ensure():
            return None
        
        try:
            transit_path = os.getenv('VAULT_TRANSIT_PATH', 'transit')
            
            response = self._client.secrets.transit.decrypt_data(
                name=key_name,
                mount_point=transit_path,
                ciphertext=ciphertext
            )
            
            if response and 'data' in response:
                plaintext = response['data'].get('plaintext')
                logger.debug(f"Successfully decrypted data with key: {key_name}")
                return plaintext
            else:
                logger.error(f"Failed to decrypt data with key: {key_name}")
                return None
                
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return None
    
    def read_llm_secrets(self, provider: str = "openai") -> Optional[Dict[str, str]]:
        """Read LLM provider secrets from Vault.
        
        Args:
            provider: LLM provider name (e.g., 'openai', 'anthropic', 'ollama')
            
        Returns:
            Dictionary containing API keys and configuration
        """
        if not self._ensure():
            logger.error("Cannot read LLM secrets - not authenticated")
            return None
        
        try:
            # Read secrets from the LLM secrets path
            secret_path = f"tractionbuild/llm/{provider}"
            secrets = self.get_secret(secret_path)
            
            if secrets:
                logger.info(f"Successfully retrieved {provider} LLM secrets from Vault")
                return secrets
            else:
                logger.warning(f"No {provider} LLM secrets found in Vault at {secret_path}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to read {provider} LLM secrets: {e}")
            return None
    
    def health_check(self) -> Dict[str, Any]:
        """Check Vault health and authentication status."""
        health_info = {
            'vault_enabled': self._enabled,
            'vault_url': os.getenv('VAULT_ADDR', 'N/A'),
            'authenticated': self._client is not None and self._client.is_authenticated(),
            'auth_method': 'token', # Assuming token auth for this check
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if self._enabled and self._client:
            try:
                health_response = self._client.sys.read_health_status()
                health_info.update({
                    'vault_initialized': health_response.get('initialized', False),
                    'vault_sealed': health_response.get('sealed', True),
                    'vault_version': health_response.get('version', 'unknown')
                })
            except Exception as e:
                health_info['vault_error'] = str(e)
        
        return health_info


# Global Vault client instance
vault_client = VaultClient()