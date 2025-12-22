"""Core package for Speckit Editor business logic"""

from .document import (
    DocumentChange,
    DocumentType,
    Requirement,
    RequirementType,
    Section,
    SpeckitDocument,
)
from .project import FeatureBranch, SpeckitProject
from .search import DocumentIndex
from .template import Template, TemplateManager, TemplateVariable
from .validator import DocumentValidator, ProjectValidator, ValidationError, ValidationResult

__all__ = [
    # Document models
    "SpeckitDocument",
    "DocumentType",
    "Section",
    "Requirement",
    "RequirementType",
    "DocumentChange",
    # Project models
    "SpeckitProject",
    "FeatureBranch",
    # Search
    "DocumentIndex",
    # Templates
    "Template",
    "TemplateManager",
    "TemplateVariable",
    # Validation
    "DocumentValidator",
    "ProjectValidator",
    "ValidationResult",
    "ValidationError",
]
