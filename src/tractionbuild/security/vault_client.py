import logging

logger = logging.getLogger(__name__)

class MockVaultClient:
    def __init__(self):
        self.enabled = False
        logger.info('Mock Vault client initialized - encryption keys will be generated locally')

    def get_encryption_key(self, key_name: str):
        return None  # Force local key generation

    def get_secret(self, secret_path: str):
        """Mock get_secret method that returns None to force environment variable fallback."""
        logger.debug(f'Mock Vault: get_secret called for {secret_path}, returning None for env fallback')
        return None

    def encrypt(self, data: str) -> str:
        """Mock encrypt method for compatibility."""
        logger.debug('Mock Vault: encrypt called, returning data unchanged')
        return data

    def decrypt(self, encrypted_data: str) -> str:
        """Mock decrypt method for compatibility."""
        logger.debug('Mock Vault: decrypt called, returning data unchanged')
        return encrypted_data

    def log_audit(self, action: str, details: str = "") -> None:
        """Mock audit logging method for compatibility."""
        logger.info(f"Audit log: {action} - {details}")

vault_client = MockVaultClient()

# Alias for compatibility
VaultClient = MockVaultClient
