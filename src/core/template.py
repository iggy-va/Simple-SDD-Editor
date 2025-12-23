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
    
    def validate_variables(self) -> List[str]:
        """Validate template variable syntax and naming conventions
        
        Returns list of error messages, empty if all valid
        """
        errors = []
        
        # Check for malformed variable patterns
        content = self.content
        
        # Find potential malformed [VARIABLE] patterns (not uppercase)
        malformed_bracket = re.findall(r"\[([a-z][a-zA-Z0-9_]*)\]", content)
        for var in malformed_bracket:
            errors.append(
                f"Variable '[{var}]' should be uppercase: '[{var.upper()}]'"
            )
        
        # Find potential malformed {{variable}} patterns (has spaces without underscores)
        malformed_braces = re.findall(r"\{\{([^}]*\s[^}]*)\}\}", content)
        for var in malformed_braces:
            if var.strip():
                suggested = var.strip().lower().replace(" ", "_")
                errors.append(
                    f"Variable '{{{{ {var} }}}}' should use underscores: '{{{{ {suggested} }}}}'"
                )
        
        # Check for unmatched brackets/braces
        if content.count("{{") != content.count("}}"):
            errors.append("Unmatched {{ or }} braces in template")
        
        open_brackets = len(re.findall(r"\[[A-Z_][A-Z0-9_]*(?!\])", content))
        close_brackets = len(re.findall(r"(?<!\[)[A-Z_][A-Z0-9_]*\]", content))
        if open_brackets > 0 or close_brackets > 0:
            errors.append("Unmatched [ or ] brackets in template")
        
        return errors
    
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
    
    def check_compatibility(self, other: "Template") -> tuple[bool, List[str]]:
        """Check if this template is compatible with another template version
        
        Args:
            other: Another template (typically an older version)
            
        Returns:
            (is_compatible, warnings) - warnings list issues even if compatible
        """
        warnings = []
        is_compatible = True
        
        # Build sets of variable names
        self_vars = {v.name for v in self.variables}
        other_vars = {v.name for v in other.variables}
        
        # Check for removed required variables (breaking change)
        for var in other.variables:
            if var.required and var.name not in self_vars:
                warnings.append(
                    f"BREAKING: Required variable '{var.name}' was removed"
                )
                is_compatible = False
        
        # Check for newly required variables (breaking change)
        for var in self.variables:
            if var.required and var.name not in other_vars:
                warnings.append(
                    f"BREAKING: New required variable '{var.name}' added"
                )
                is_compatible = False
        
        # Check for changed variable patterns (potentially breaking)
        for var in self.variables:
            for other_var in other.variables:
                if var.name == other_var.name:
                    if var.pattern != other_var.pattern:
                        warnings.append(
                            f"Variable '{var.name}' validation pattern changed"
                        )
        
        # Check for optional changes (non-breaking)
        removed_optional = other_vars - self_vars
        if removed_optional:
            optional_removed = [
                v.name for v in other.variables 
                if v.name in removed_optional and not v.required
            ]
            if optional_removed:
                warnings.append(
                    f"Optional variables removed: {', '.join(optional_removed)}"
                )
        
        added_optional = self_vars - other_vars
        if added_optional:
            optional_added = [
                v.name for v in self.variables 
                if v.name in added_optional and not v.required
            ]
            if optional_added:
                warnings.append(
                    f"Optional variables added: {', '.join(optional_added)}"
                )
        
        return is_compatible, warnings
    
    @staticmethod
    def backup_document(document_path: Path) -> Path:
        """Create backup of document before migration
        
        Args:
            document_path: Path to document to backup
            
        Returns:
            Path to backup file
        """
        import shutil
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = document_path.parent / ".backups"
        backup_dir.mkdir(exist_ok=True)
        
        backup_name = f"{document_path.stem}_backup_{timestamp}{document_path.suffix}"
        backup_path = backup_dir / backup_name
        
        shutil.copy2(document_path, backup_path)
        logger.info(f"Created backup: {backup_path}")
        
        return backup_path
    
    def migrate_document(self, document_content: str, old_template: Optional["Template"] = None) -> tuple[str, List[str]]:
        """Migrate document content to new template structure
        
        Args:
            document_content: Content of document created from old template
            old_template: Previous template version (optional)
            
        Returns:
            (migrated_content, warnings) - new content and any issues encountered
        """
        warnings = []
        
        # If we have old template, check compatibility
        if old_template:
            is_compatible, compat_warnings = self.check_compatibility(old_template)
            warnings.extend(compat_warnings)
            
            if not is_compatible:
                warnings.append("WARNING: Template has breaking changes - manual review recommended")
        
        # Strategy: Preserve existing content sections, add new template structure
        # This is a basic implementation - can be enhanced based on document type
        
        # Extract existing content sections (between headers)
        import re
        
        sections = {}
        current_section = None
        current_content = []
        
        for line in document_content.split("\n"):
            # Check if line is a markdown header
            if line.startswith("#"):
                # Save previous section
                if current_section:
                    sections[current_section] = "\n".join(current_content)
                
                # Start new section
                current_section = line.strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_section:
            sections[current_section] = "\n".join(current_content)
        
        # Build new content from template, preserving existing sections
        migrated_lines = []
        current_section = None
        
        for line in self.content.split("\n"):
            if line.startswith("#"):
                current_section = line.strip()
                migrated_lines.append(line)
                
                # If we have content for this section, add it
                if current_section in sections:
                    # Preserve the original content
                    preserved_content = sections[current_section].strip()
                    if preserved_content:
                        migrated_lines.append(preserved_content)
                    # Remove from sections dict to track used sections
                    del sections[current_section]
            else:
                # Only add template line if it's not placeholder content
                # (skip template examples/placeholders)
                if line.strip() and not line.strip().startswith("{{") and not line.strip().startswith("["):
                    # Check if this looks like template placeholder text
                    if not any(keyword in line.lower() for keyword in ["example", "description goes", "content goes"]):
                        migrated_lines.append(line)
                else:
                    migrated_lines.append(line)
        
        # Add any sections from old document that weren't in new template
        if sections:
            warnings.append(f"Sections not in new template: {', '.join(sections.keys())}")
            migrated_lines.append("\n## Additional Content from Previous Version\n")
            for section, content in sections.items():
                migrated_lines.append(f"\n{section}")
                migrated_lines.append(content)
        
        migrated_content = "\n".join(migrated_lines)
        
        return migrated_content, warnings


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
        """List available templates, sorted by name"""
        if not self.templates:
            self.load_templates()
        return sorted(self.templates.values(), key=lambda t: t.name)
    
    def list_templates_by_type(self) -> Dict[str, List[Template]]:
        """List templates grouped by type (spec, plan, tasks, etc.)"""
        if not self.templates:
            self.load_templates()
        
        grouped: Dict[str, List[Template]] = {}
        for template in self.templates.values():
            # Extract type from name (e.g., "spec-template" -> "spec")
            type_name = template.name.split("-")[0] if "-" in template.name else "other"
            
            if type_name not in grouped:
                grouped[type_name] = []
            grouped[type_name].append(template)
        
        # Sort each group by name
        for type_name in grouped:
            grouped[type_name].sort(key=lambda t: t.name)
        
        return grouped
    
    def get_template_versions(self, base_name: str) -> List[Template]:
        """Get all versions of a template (e.g., spec-template, spec-template-v2)"""
        if not self.templates:
            self.load_templates()
        
        versions = []
        for name, template in self.templates.items():
            # Match base name exactly or with version suffix
            if name == base_name or name.startswith(f"{base_name}-v"):
                versions.append(template)
        
        # Sort by modification time (newest first)
        versions.sort(key=lambda t: t.updated_at or datetime.min, reverse=True)
        return versions
    
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
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        template.save(template_path)
        self._cache[name] = template
        self.templates[name] = template
        
        return template
    
    def save_template_version(self, base_name: str, content: str, 
                             description: str = "") -> Template:
        """Save new version of existing template"""
        # Find next version number
        versions = self.get_template_versions(base_name)
        
        if not versions:
            # No existing versions, create base template
            return self.create_template(base_name, content, description)
        
        # Extract version numbers from existing templates
        version_nums = [1]  # Base version is v1
        for template in versions:
            if "-v" in template.name:
                try:
                    v = int(template.name.split("-v")[-1])
                    version_nums.append(v)
                except ValueError:
                    pass
        
        next_version = max(version_nums) + 1
        new_name = f"{base_name}-v{next_version}"
        
        return self.create_template(new_name, content, description)
    
    def copy_template(self, source_name: str, new_name: str) -> Template:
        """Create copy of existing template with new name"""
        source = self.get_template(source_name)
        if not source:
            raise FileNotFoundError(f"Source template not found: {source_name}")
        
        return self.create_template(
            name=new_name,
            content=source.content,
            description=f"Copy of {source_name}"
        )
    
    def migrate_document_to_template(self, document_path: Path, 
                                    new_template_name: str,
                                    create_backup: bool = True) -> tuple[bool, List[str]]:
        """Migrate document to new template version
        
        Args:
            document_path: Path to document file
            new_template_name: Name of target template
            create_backup: Whether to create backup before migration
            
        Returns:
            (success, messages) - success status and list of info/warning messages
        """
        messages = []
        
        try:
            # Load new template
            new_template = self.get_template(new_template_name)
            if not new_template:
                return False, [f"Template '{new_template_name}' not found"]
            
            # Read current document
            if not document_path.exists():
                return False, [f"Document '{document_path}' not found"]
            
            current_content = document_path.read_text(encoding="utf-8")
            
            # Create backup if requested
            backup_path = None
            if create_backup:
                backup_path = Template.backup_document(document_path)
                messages.append(f"Backup created: {backup_path}")
            
            # Attempt to detect old template (basic heuristic)
            # Could be enhanced by storing template metadata in document frontmatter
            old_template = None
            base_name = new_template_name.split("-v")[0] if "-v" in new_template_name else new_template_name
            versions = self.get_template_versions(base_name)
            if len(versions) > 1:
                # Use the previous version as old template
                old_template = versions[1] if versions[0].name == new_template_name else versions[0]
                messages.append(f"Detected old template: {old_template.name}")
            
            # Migrate content
            migrated_content, migration_warnings = new_template.migrate_document(
                current_content, 
                old_template
            )
            messages.extend(migration_warnings)
            
            # Save migrated content
            document_path.write_text(migrated_content, encoding="utf-8")
            messages.append(f"Document migrated to template '{new_template_name}'")
            
            return True, messages
            
        except Exception as e:
            error_msg = f"Migration failed: {str(e)}"
            messages.append(error_msg)
            logger.error(error_msg, exc_info=True)
            return False, messages
