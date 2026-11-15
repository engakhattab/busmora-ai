"""Typed settings, one class per process role, validated at startup.

Each role class declares only the stores that role is allowed to use (SYS §4.2), so a
role cannot be configured to reach a store outside its boundary. Invalid or missing
settings stop the process (BTD §9.2).
"""

from typing import Literal

from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR"]


class ServerSettings(BaseModel):
    host: str = "127.0.0.1"
    port: int = Field(ge=1, le=65535)


class PostgresSettings(BaseModel):
    dsn: SecretStr


class QdrantSettings(BaseModel):
    url: str
    api_key: SecretStr | None = None


class RedisSettings(BaseModel):
    url: SecretStr


class ObjectStorageSettings(BaseModel):
    endpoint_url: str | None = None
    """None means the provider's default endpoint; set it for S3-compatible stores."""
    region: str = "us-east-1"
    bucket: str
    access_key_id: SecretStr
    secret_access_key: SecretStr


class TemporalSettings(BaseModel):
    address: str = "127.0.0.1:7233"
    namespace: str = "default"
    api_key: SecretStr | None = None
    """One key per process role in Temporal Cloud (ADR-011). Enables TLS when set."""


class RoleSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="BUSMORA_AI_",
        env_nested_delimiter="__",
        env_file=".env",
        extra="ignore",
    )

    environment: Literal["local", "test", "staging", "production"] = "local"
    log_level: LogLevel = "INFO"
    log_format: Literal["json", "console"] = "json"
    health_check_timeout_seconds: float = Field(default=2.0, gt=0, le=30)


class HttpRoleSettings(RoleSettings):
    """ai-http: internal FastAPI for quick replies and Brain retrieval."""

    server: ServerSettings = ServerSettings(port=8100)
    postgres: PostgresSettings
    qdrant: QdrantSettings


class AgentRoleSettings(RoleSettings):
    """ai-agent: Temporal activity worker for the Director's graph and indexing."""

    health_server: ServerSettings = ServerSettings(port=8101)
    temporal: TemporalSettings = TemporalSettings()
    postgres: PostgresSettings
    qdrant: QdrantSettings
    redis: RedisSettings
    object_storage: ObjectStorageSettings


class CrawlRoleSettings(RoleSettings):
    """ai-crawl: Temporal activity worker for bounded crawling."""

    health_server: ServerSettings = ServerSettings(port=8102)
    temporal: TemporalSettings = TemporalSettings()
    redis: RedisSettings
    object_storage: ObjectStorageSettings
