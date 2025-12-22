"""Template system for Speckit Editor"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TemplateVariable:
    """Variable placeholder in a template"""
    name: str  # Variable name (e.g., "feature_name", "feature_id")
    description: str  # Human-readable description
    default: str = ""  # Default value
    required: bool = True  # Whether variable must be provided
    pattern: Optional[str] = None  # Regex pattern for validation
    
    def validate(self, value: str) -> bool:
        """Validate value against pattern if defined"""
        if self.pattern:
            return bool(re.match(self.pattern, value))
        return True


@dataclass
class Template:
    """Speckit document template"""
    name: str  # Template name (e.g., "spec", "plan", "tasks")
    path: Path  # Template file path
    content: str = ""  # Template content with {{variables}}
    description: str = ""  # Template description
    version: str = "1.0.0"  # Template version
    variables: List[TemplateVariable] = field(default_factory=list)
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    author: Optional[str] = None
    
    @classmethod
    def load(cls, template_path: Path) -> "Template":
        """Load template from file"""
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        logger.info(f"Loading template: {template_path}")
        
        content = template_path.read_text(encoding="utf-8")
        name = template_path.stem
        
        # Extract metadata from frontmatter if present
        metadata = cls._extract_metadata(content)
        
        # Extract variables from template content
        variables = cls._extract_variables(content)
        
        return cls(
            name=name,
            path=template_path,
            content=content,
            description=metadata.get("description", ""),
            version=metadata.get("version", "1.0.0"),
            variables=variables,
            author=metadata.get("author"),
            created_at=datetime.fromtimestamp(template_path.stat().st_ctime),
            updated_at=datetime.fromtimestamp(template_path.stat().st_mtime),
        )
    
    @staticmethod
    def _extract_metadata(content: str) -> Dict[str, Any]:
        """Extract YAML frontmatter from template"""
        metadata = {}
        
        # Check for YAML frontmatter (--- at start and end)
        if content.startswith("---\n"):
            parts = content.split("---\n", 2)
            if len(parts) >= 3:
                # Parse simple key: value pairs (not full YAML)
                frontmatter = parts[1]
                for line in frontmatter.split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        metadata[key.strip()] = value.strip()
        
        return metadata
    
    @classmethod
    def _extract_variables(cls, content: str) -> List[TemplateVariable]:
        """Extract [VARIABLE] and {{variable}} placeholders from template content"""
        variables = []
        seen = set()
        
        # Find all {{variable}} and [VARIABLE] patterns
        patterns = [
            re.compile(r"\{\{([^}]+)\}\}"),  # {{variable}} format
            re.compile(r"\[([A-Z_][A-Z0-9_]*)\]"),  # [VARIABLE] format (uppercase with underscores)
        ]
        
        for pattern in patterns:
            for match in pattern.finditer(content):
                var_name = match.group(1).strip().lower().replace(" ", "_")
                
                # Skip duplicates
                if var_name in seen:
                    continue
                seen.add(var_name)
                
                # Create variable with sensible defaults
                variable = TemplateVariable(
                    name=var_name,
                    description=cls._humanize_variable_name(var_name),
                    default="",
                    required=True,
                )
                
                # Add validation pattern and defaults for known variable types
                if var_name == "feature_id" or var_name.endswith("_id"):
                    variable.pattern = r"^\d{3}$"
                    variable.description = "Feature ID (3 digits, e.g., 001)"
                elif var_name == "date" or var_name == "done_date":
                    variable.default = datetime.now().strftime("%Y-%m-%d")
                    variable.required = False
                elif var_name == "author" or var_name.endswith("_implementer"):
                    variable.required = False
                elif var_name == "branch":
                    variable.required = False
                    variable.default = "main"
                
                variables.append(variable)
        
        return variables
    
    @staticmethod
    def _humanize_variable_name(name: str) -> str:
        """Convert variable_name to Human Readable Name"""
        return name.replace("_", " ").title()
    
    def instantiate(self, values: Dict[str, str]) -> str:
        """Create document from template with variable substitution"""
        logger.info(f"Instantiating template: {self.name}")
        
        # Validate required variables
        for var in self.variables:
            if var.required and var.name not in values:
                raise ValueError(f"Required variable missing: {var.name}")
            
            # Validate against pattern
            if var.name in values and not var.validate(values[var.name]):
                raise ValueError(
                    f"Invalid value for {var.name}: {values[var.name]} "
                    f"(expected pattern: {var.pattern})"
                )
        
        # Substitute variables - support both {{variable}} and [VARIABLE] formats
        result = self.content
        for var in self.variables:
            value = values.get(var.name, var.default)
            
            # Replace {{variable}} format (case-insensitive)
            result = re.sub(
                r"\{\{" + re.escape(var.name) + r"\}\}",
                value,
                result,
                flags=re.IGNORECASE
            )
            
            # Replace [VARIABLE] format (uppercase)
            upper_name = var.name.upper().replace("_", " ")
            result = result.replace(f"[{upper_name}]", value)
            result = result.replace(f"[{var.name.upper()}]", value)
        
        logger.debug(f"Template instantiated with {len(values)} variables")
        return result
    
    def save(self, output_path: Path) -> None:
        """Save template to file"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.content, encoding="utf-8")
        logger.info(f"Template saved: {output_path}")


class TemplateManager:
    """Manages template loading and caching"""
    
    def __init__(self, templates_dir: Path):
        self.templates_dir = templates_dir
        self.template_dir = templates_dir  # Alias for tests
        self._cache: Dict[str, Template] = {}
        self.templates: Dict[str, Template] = {}  # For tests
    
    def load_templates(self) -> None:
        """Load all templates from directory"""
        self.templates.clear()
        self._cache.clear()
        
        if not self.templates_dir.exists():
            logger.warning(f"Templates directory not found: {self.templates_dir}")
            return
        
        for path in self.templates_dir.glob("*.md"):
            try:
                template = Template.load(path)
                self.templates[template.name] = template
                self._cache[template.name] = template
            except Exception as e:
                logger.error(f"Failed to load template {path}: {e}")
    
    def list_templates(self) -> List[Template]:
        """List available templates"""
        if not self.templates:
            self.load_templates()
        return list(self.templates.values())
    
    def get_template(self, name: str, force_reload: bool = False) -> Optional[Template]:
        """Load template by name with caching"""
        if not force_reload and name in self._cache:
            return self._cache[name]
        
        template_path = self.templates_dir / f"{name}.md"
        if not template_path.exists():
            return None
        
        template = Template.load(template_path)
        self._cache[name] = template
        
        return template
    
    def create_template(self, name: str, content: str,
                       description: str = "") -> Template:
        """Create new template"""
        template_path = self.templates_dir / f"{name}.md"
        
        if template_path.exists():
            raise FileExistsError(f"Template already exists: {name}")
        
        template = Template(
            name=name,
            path=template_path,
            content=content,
            description=description,
        )
        
        template.save(template_path)
        self._cache[name] = template
        
        return template
