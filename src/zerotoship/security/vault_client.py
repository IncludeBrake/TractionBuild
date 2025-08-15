"""
HashiCorp Vault integration for ZeroToShip.
Provides secure secret management with zero-trust architecture.
"""

import os
import logging
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
    """Secure secrets management using HashiCorp Vault."""
    
    def __init__(self, vault_url: str = None, auth_method: str = "kubernetes"):
        self.vault_url = vault_url or os.getenv('VAULT_ADDR', 'https://vault.zerotoship.ai')
        self.auth_method = auth_method
        self.client = None
        self.authenticated = False
        self.token_expiry = None
        self.enabled = VAULT_AVAILABLE
        
        if not self.enabled:
            logger.warning("Vault integration disabled - hvac not available")
            return
        
        self._initialize_client()
        logger.info(f"Vault client initialized for {self.vault_url}")
    
    def _initialize_client(self):
        """Initialize the Vault client."""
        if not VAULT_AVAILABLE:
            return
        
        try:
            self.client = hvac.Client(url=self.vault_url)
            
            # Verify Vault is accessible
            if self.client.sys.is_initialized() and not self.client.sys.is_sealed():
                logger.info("Vault server is accessible and unsealed")
            else:
                logger.error("Vault server is not accessible or sealed")
                self.enabled = False
                
        except Exception as e:
            logger.error(f"Failed to initialize Vault client: {e}")
            self.enabled = False
    
    def authenticate(self) -> bool:
        """Authenticate with Vault using the configured method."""
        if not self.enabled:
            return False
        
        try:
            if self.auth_method == "kubernetes":
                return self._authenticate_kubernetes()
            elif self.auth_method == "token":
                return self._authenticate_token()
            else:
                logger.error(f"Unsupported authentication method: {self.auth_method}")
                return False
                
        except Exception as e:
            logger.error(f"Vault authentication failed: {e}")
            return False
    
    def _authenticate_kubernetes(self) -> bool:
        """Authenticate using Kubernetes service account token."""
        try:
            # Read the service account token
            token_path = "/var/run/secrets/kubernetes.io/serviceaccount/token"
            if not os.path.exists(token_path):
                logger.error("Kubernetes service account token not found")
                return False
            
            with open(token_path, 'r') as f:
                jwt_token = f.read().strip()
            
            # Authenticate with Vault
            auth_path = os.getenv('VAULT_AUTH_PATH', 'auth/kubernetes')
            role = os.getenv('VAULT_ROLE', 'zerotoship')
            
            response = self.client.auth.kubernetes.login(
                role=role,
                jwt=jwt_token,
                mount_point=auth_path.replace('auth/', '')
            )
            
            if response and response.get('auth'):
                self.authenticated = True
                # Calculate token expiry
                lease_duration = response['auth'].get('lease_duration', 3600)
                self.token_expiry = datetime.utcnow() + timedelta(seconds=lease_duration - 300)  # 5 min buffer
                
                logger.info(f"Successfully authenticated with Vault (expires: {self.token_expiry})")
                return True
            else:
                logger.error("Vault authentication response invalid")
                return False
                
        except Exception as e:
            logger.error(f"Kubernetes authentication failed: {e}")
            return False
    
    def _authenticate_token(self) -> bool:
        """Authenticate using Vault token."""
        try:
            token = os.getenv('VAULT_TOKEN')
            if not token:
                logger.error("VAULT_TOKEN environment variable not set")
                return False
            
            self.client.token = token
            
            # Verify token is valid
            if self.client.is_authenticated():
                self.authenticated = True
                logger.info("Successfully authenticated with Vault using token")
                return True
            else:
                logger.error("Vault token is invalid")
                return False
                
        except Exception as e:
            logger.error(f"Token authentication failed: {e}")
            return False
    
    def _ensure_authenticated(self) -> bool:
        """Ensure we have a valid authentication token."""
        if not self.enabled:
            return False
        
        # Check if we need to re-authenticate
        if not self.authenticated or (self.token_expiry and datetime.utcnow() > self.token_expiry):
            return self.authenticate()
        
        return self.authenticated
    
    def get_secret(self, path: str, key: str = None) -> Optional[Dict[str, Any]]:
        """Retrieve a secret from Vault."""
        if not self._ensure_authenticated():
            logger.error("Cannot retrieve secret - not authenticated")
            return None
        
        try:
            # Read secret from KV v2 engine
            response = self.client.secrets.kv.v2.read_secret_version(path=path)
            
            if response and 'data' in response and 'data' in response['data']:
                secret_data = response['data']['data']
                
                if key:
                    return secret_data.get(key)
                else:
                    return secret_data
            else:
                logger.error(f"Secret not found at path: {path}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to retrieve secret from {path}: {e}")
            return None
    
    def set_secret(self, path: str, secret_data: Dict[str, Any]) -> bool:
        """Store a secret in Vault."""
        if not self._ensure_authenticated():
            logger.error("Cannot store secret - not authenticated")
            return False
        
        try:
            response = self.client.secrets.kv.v2.create_or_update_secret(
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
        if not self._ensure_authenticated():
            return None
        
        try:
            # Request dynamic credentials from database engine
            response = self.client.secrets.database.generate_credentials(name=database_name)
            
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
        if not self._ensure_authenticated():
            return None
        
        try:
            pki_path = os.getenv('VAULT_PKI_PATH', 'pki')
            role_name = os.getenv('VAULT_PKI_ROLE', 'zerotoship')
            
            cert_data = {
                'common_name': common_name,
                'ttl': '24h'
            }
            
            if alt_names:
                cert_data['alt_names'] = ','.join(alt_names)
            
            response = self.client.secrets.pki.generate_certificate(
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
        if not self._ensure_authenticated():
            return None
        
        try:
            transit_path = os.getenv('VAULT_TRANSIT_PATH', 'transit')
            
            # Try to read the key first
            try:
                response = self.client.secrets.transit.read_key(
                    name=key_name,
                    mount_point=transit_path
                )
                if response:
                    logger.info(f"Retrieved encryption key: {key_name}")
                    return key_name  # Return key name for encryption operations
            except:
                pass  # Key doesn't exist, create it
            
            # Create the key if it doesn't exist
            self.client.secrets.transit.create_key(
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
        if not self._ensure_authenticated():
            return None
        
        try:
            transit_path = os.getenv('VAULT_TRANSIT_PATH', 'transit')
            
            response = self.client.secrets.transit.encrypt_data(
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
        if not self._ensure_authenticated():
            return None
        
        try:
            transit_path = os.getenv('VAULT_TRANSIT_PATH', 'transit')
            
            response = self.client.secrets.transit.decrypt_data(
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
        if not self._ensure_authenticated():
            logger.error("Cannot read LLM secrets - not authenticated")
            return None
        
        try:
            # Read secrets from the LLM secrets path
            secret_path = f"zerotoship/llm/{provider}"
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
            'vault_enabled': self.enabled,
            'vault_url': self.vault_url,
            'authenticated': self.authenticated,
            'auth_method': self.auth_method,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if self.enabled and self.client:
            try:
                health_response = self.client.sys.read_health_status()
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