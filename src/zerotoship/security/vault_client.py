import logging

logger = logging.getLogger(__name__)

class MockVaultClient:
    def __init__(self):
        self.enabled = False
        logger.info('Mock Vault client initialized - encryption keys will be generated locally')
    
    def get_encryption_key(self, key_name: str):
        return None  # Force local key generation

vault_client = MockVaultClient()

# Alias for compatibility
VaultClient = MockVaultClient
