"""YAML-driven provider & model registry for PyClaw."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class ModelDef(BaseModel):
    id: str
    display_name: str


class ProviderDef(BaseModel):
    key: str
    display_name: str
    langchain_provider: str
    api_key_env: str = ""
    needs_api_key: bool = True
    base_url: str = ""
    models: list[ModelDef] = Field(default_factory=list)


class ModelRegistry(BaseModel):
    providers: list[ProviderDef] = Field(default_factory=list)

    def get_provider(self, key: str) -> ProviderDef | None:
        """Look up a provider by its key (e.g. 'deepseek')."""
        for p in self.providers:
            if p.key == key:
                return p
        return None

    def get_provider_for_model_string(self, model_string: str) -> tuple[ProviderDef | None, str]:
        """Parse 'provider_key:model_id' and return (ProviderDef, model_id).

        Returns (None, model_string) if not found.
        """
        if ":" not in model_string:
            return None, model_string
        provider_key, model_id = model_string.split(":", 1)
        provider = self.get_provider(provider_key)
        return provider, model_id


_MODELS_YML = Path(__file__).parent / "models.yml"


@lru_cache(maxsize=1)
def load_model_registry(path: str | None = None) -> ModelRegistry:
    """Load the provider/model registry from YAML.

    Uses *path* (as a string for lru_cache hashability) or the default
    ``models.yml`` bundled with the package.
    """
    yml_path = Path(path) if path else _MODELS_YML
    data = yaml.safe_load(yml_path.read_text(encoding="utf-8"))
    return ModelRegistry.model_validate(data)
