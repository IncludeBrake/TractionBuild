"""
Configuration utilities for ZeroToShip.
"""

import os
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config(BaseModel):
    """Main configuration class."""
    
    # Core settings
    project_name: str = Field(default="ZeroToShip", description="Project name")
    environment: str = Field(default="development", description="Environment")
    debug: bool = Field(default=False, description="Debug mode")
    
    # AI Provider settings
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    openai_model: str = Field(default="gpt-4-turbo-preview", description="OpenAI model")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    anthropic_model: str = Field(default="claude-3-sonnet-20240229", description="Anthropic model")
    
    # Database settings
    neo4j_uri: Optional[str] = Field(default=None, description="Neo4j URI")
    neo4j_user: str = Field(default="neo4j", description="Neo4j username")
    neo4j_password: Optional[str] = Field(default=None, description="Neo4j password")
    
    # Logging settings
    log_level: str = Field(default="INFO", description="Log level")
    crewai_log_level: str = Field(default="INFO", description="CrewAI log level")
    
    # Token budget settings
    max_tokens_per_agent: int = Field(default=10000, description="Max tokens per agent")
    max_tokens_per_run: int = Field(default=50000, description="Max tokens per run")
    max_tokens_per_project: int = Field(default=200000, description="Max tokens per project")
    
    # Safety settings
    enable_drift_detection: bool = Field(default=True, description="Enable drift detection")
    enable_token_budgeting: bool = Field(default=True, description="Enable token budgeting")
    enable_fallback_plans: bool = Field(default=True, description="Enable fallback plans")
    enable_multi_tenant_safety: bool = Field(default=True, description="Enable multi-tenant safety")
    
    # Memory settings
    memory_file_path: str = Field(default="data/project_memory.json", description="Memory file path")
    max_memory_entries_per_type: int = Field(default=1000, description="Max memory entries per type")
    memory_retention_days: int = Field(default=365, description="Memory retention in days")
    
    # Output validation settings
    enable_hallucination_detection: bool = Field(default=True, description="Enable hallucination detection")
    enable_security_checks: bool = Field(default=True, description="Enable security checks")
    enable_format_validation: bool = Field(default=True, description="Enable format validation")
    max_content_length: int = Field(default=50000, description="Maximum content length")
    
    def __init__(self, **data):
        """Initialize configuration with environment variables."""
        # Load from environment variables
        env_data = {}
        
        # Core settings
        env_data["project_name"] = os.getenv("PROJECT_NAME", "ZeroToShip")
        env_data["environment"] = os.getenv("ENVIRONMENT", "development")
        env_data["debug"] = os.getenv("DEBUG", "false").lower() == "true"
        
        # AI Provider settings
        env_data["openai_api_key"] = os.getenv("OPENAI_API_KEY")
        env_data["openai_model"] = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        env_data["anthropic_api_key"] = os.getenv("ANTHROPIC_API_KEY")
        env_data["anthropic_model"] = os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")
        
        # Database settings
        env_data["neo4j_uri"] = os.getenv("NEO4J_URI")
        env_data["neo4j_user"] = os.getenv("NEO4J_USER", "neo4j")
        env_data["neo4j_password"] = os.getenv("NEO4J_PASSWORD")
        
        # Logging settings
        env_data["log_level"] = os.getenv("LOG_LEVEL", "INFO")
        env_data["crewai_log_level"] = os.getenv("CREWAI_LOG_LEVEL", "INFO")
        
        # Token budget settings
        env_data["max_tokens_per_agent"] = int(os.getenv("MAX_TOKENS_PER_AGENT", "10000"))
        env_data["max_tokens_per_run"] = int(os.getenv("MAX_TOKENS_PER_RUN", "50000"))
        env_data["max_tokens_per_project"] = int(os.getenv("MAX_TOKENS_PER_PROJECT", "200000"))
        
        # Safety settings
        env_data["enable_drift_detection"] = os.getenv("ENABLE_DRIFT_DETECTION", "true").lower() == "true"
        env_data["enable_token_budgeting"] = os.getenv("ENABLE_TOKEN_BUDGETING", "true").lower() == "true"
        env_data["enable_fallback_plans"] = os.getenv("ENABLE_FALLBACK_PLANS", "true").lower() == "true"
        env_data["enable_multi_tenant_safety"] = os.getenv("ENABLE_MULTI_TENANT_SAFETY", "true").lower() == "true"
        
        # Memory settings
        env_data["memory_file_path"] = os.getenv("MEMORY_FILE_PATH", "data/project_memory.json")
        env_data["max_memory_entries_per_type"] = int(os.getenv("MAX_MEMORY_ENTRIES_PER_TYPE", "1000"))
        env_data["memory_retention_days"] = int(os.getenv("MEMORY_RETENTION_DAYS", "365"))
        
        # Output validation settings
        env_data["enable_hallucination_detection"] = os.getenv("ENABLE_HALLUCINATION_DETECTION", "true").lower() == "true"
        env_data["enable_security_checks"] = os.getenv("ENABLE_SECURITY_CHECKS", "true").lower() == "true"
        env_data["enable_format_validation"] = os.getenv("ENABLE_FORMAT_VALIDATION", "true").lower() == "true"
        env_data["max_content_length"] = int(os.getenv("MAX_CONTENT_LENGTH", "50000"))
        
        # Merge with provided data
        env_data.update(data)
        
        super().__init__(**env_data)
    
    def validate_required_settings(self) -> bool:
        """Validate that required settings are present."""
        missing_settings = []
        
        if not self.openai_api_key and not self.anthropic_api_key:
            missing_settings.append("Either OPENAI_API_KEY or ANTHROPIC_API_KEY must be set")
        
        if self.environment == "production":
            if not self.neo4j_uri:
                missing_settings.append("NEO4J_URI is required in production")
            if not self.neo4j_password:
                missing_settings.append("NEO4J_PASSWORD is required in production")
        
        if missing_settings:
            raise ValueError(f"Missing required settings: {', '.join(missing_settings)}")
        
        return True
    
    def get_ai_provider_config(self) -> Dict[str, Any]:
        """Get AI provider configuration."""
        if self.openai_api_key:
            return {
                "provider": "openai",
                "api_key": self.openai_api_key,
                "model": self.openai_model
            }
        elif self.anthropic_api_key:
            return {
                "provider": "anthropic",
                "api_key": self.anthropic_api_key,
                "model": self.anthropic_model
            }
        else:
            raise ValueError("No AI provider configured")
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        return {
            "uri": self.neo4j_uri,
            "user": self.neo4j_user,
            "password": self.neo4j_password
        }
    
    def get_safety_config(self) -> Dict[str, Any]:
        """Get safety configuration."""
        return {
            "enable_drift_detection": self.enable_drift_detection,
            "enable_token_budgeting": self.enable_token_budgeting,
            "enable_fallback_plans": self.enable_fallback_plans,
            "enable_multi_tenant_safety": self.enable_multi_tenant_safety,
            "max_tokens_per_agent": self.max_tokens_per_agent,
            "max_tokens_per_run": self.max_tokens_per_run,
            "max_tokens_per_project": self.max_tokens_per_project
        }


# Global config instance
config = Config() 