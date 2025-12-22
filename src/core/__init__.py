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
    # Validation
    "DocumentValidator",
    "ProjectValidator",
    "ValidationResult",
    "ValidationError",
]
