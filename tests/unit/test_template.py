"""Tests for template system"""

import re
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.core.template import Template, TemplateManager, TemplateVariable


class TestTemplateVariable:
    """Tests for TemplateVariable"""
    
    def test_variable_creation(self):
        """Test basic variable creation"""
        var = TemplateVariable(
            name="feature_id",
            description="Feature ID",
            default="001",
            required=True,
            pattern=r"^\d{3}$"
        )
        assert var.name == "feature_id"
        assert var.description == "Feature ID"
        assert var.default == "001"
        assert var.required is True
        assert var.pattern == r"^\d{3}$"
    
    def test_validate_with_pattern(self):
        """Test validation with regex pattern"""
        var = TemplateVariable(
            name="feature_id",
            description="Feature ID",
            pattern=r"^\d{3}$"
        )
        assert var.validate("001") is True
        assert var.validate("123") is True
        assert var.validate("abc") is False
        assert var.validate("1") is False
        assert var.validate("1234") is False
    
    def test_validate_without_pattern(self):
        """Test validation without pattern (always valid)"""
        var = TemplateVariable(name="name", description="Name")
        assert var.validate("anything") is True
        assert var.validate("") is True
        assert var.validate("123!@#") is True


class TestTemplate:
    """Tests for Template"""
    
    @pytest.fixture
    def temp_template(self, tmp_path):
        """Create temporary template file"""
        template_file = tmp_path / "test_template.md"
        content = """---
description: Test template
version: 1.0.0
author: Test Author
---

# {{feature_name}}

Feature ID: {{feature_id}}
Created: {{created_date}}

## Overview
{{description}}
"""
        template_file.write_text(content, encoding="utf-8")
        return template_file
    
    @pytest.fixture
    def simple_template(self, tmp_path):
        """Create simple template without frontmatter"""
        template_file = tmp_path / "simple.md"
        content = """# {{title}}

{{content}}
"""
        template_file.write_text(content, encoding="utf-8")
        return template_file
    
    def test_load_template(self, temp_template):
        """Test loading template from file"""
        template = Template.load(temp_template)
        
        assert template.name == "test_template"
        assert template.path == temp_template
        assert template.description == "Test template"
        assert template.version == "1.0.0"
        assert template.author == "Test Author"
        assert "{{feature_name}}" in template.content
        assert isinstance(template.created_at, datetime)
        assert isinstance(template.updated_at, datetime)
    
    def test_load_nonexistent_template(self, tmp_path):
        """Test loading non-existent template raises error"""
        with pytest.raises(FileNotFoundError):
            Template.load(tmp_path / "nonexistent.md")
    
    def test_extract_variables(self, temp_template):
        """Test extraction of variables from template"""
        template = Template.load(temp_template)
        
        var_names = {v.name for v in template.variables}
        assert "feature_name" in var_names
        assert "feature_id" in var_names
        assert "created_date" in var_names
        assert "description" in var_names
        assert len(template.variables) == 4
    
    def test_instantiate_template(self, temp_template):
        """Test template instantiation with values"""
        template = Template.load(temp_template)
        
        values = {
            "feature_name": "Test Feature",
            "feature_id": "001",
            "created_date": "2025-12-22",
            "description": "A test feature description"
        }
        
        result = template.instantiate(values)
        
        assert "# Test Feature" in result
        assert "Feature ID: 001" in result
        assert "Created: 2025-12-22" in result
        assert "A test feature description" in result
        assert "{{" not in result  # No unresolved variables
    
    def test_instantiate_partial_values(self, temp_template):
        """Test instantiation with partial values"""
        template = Template.load(temp_template)
        
        # Provide all required variables
        values = {
            "feature_name": "Test Feature",
            "feature_id": "001",
            "created_date": "2025-12-22",
            "description": "Test description"
        }
        
        result = template.instantiate(values)
        
        assert "Test Feature" in result
        assert "001" in result
    
    def test_extract_metadata_with_frontmatter(self, temp_template):
        """Test YAML frontmatter extraction"""
        content = temp_template.read_text(encoding="utf-8")
        metadata = Template._extract_metadata(content)
        
        assert metadata["description"] == "Test template"
        assert metadata["version"] == "1.0.0"
        assert metadata["author"] == "Test Author"
    
    def test_extract_metadata_without_frontmatter(self, simple_template):
        """Test metadata extraction from template without frontmatter"""
        content = simple_template.read_text(encoding="utf-8")
        metadata = Template._extract_metadata(content)
        
        assert metadata == {}
    
    def test_simple_template_load(self, simple_template):
        """Test loading simple template without frontmatter"""
        template = Template.load(simple_template)
        
        assert template.name == "simple"
        assert template.description == ""
        assert template.version == "1.0.0"  # Default
        assert len(template.variables) == 2
        var_names = {v.name for v in template.variables}
        assert "title" in var_names
        assert "content" in var_names


class TestTemplateManager:
    """Tests for TemplateManager"""
    
    @pytest.fixture
    def template_dir(self, tmp_path):
        """Create directory with multiple templates"""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        
        # Create spec template
        (template_dir / "spec.md").write_text("""---
description: Specification template
---
# {{feature_name}}
""", encoding="utf-8")
        
        # Create plan template
        (template_dir / "plan.md").write_text("""---
description: Plan template
---
# Implementation Plan: {{feature_name}}
""", encoding="utf-8")
        
        # Create tasks template
        (template_dir / "tasks.md").write_text("""# Tasks: {{feature_name}}
""", encoding="utf-8")
        
        return template_dir
    
    def test_manager_initialization(self, template_dir):
        """Test TemplateManager initialization"""
        manager = TemplateManager(template_dir)
        
        assert manager.template_dir == template_dir
        assert len(manager.templates) == 0  # Lazy loading
    
    def test_load_templates(self, template_dir):
        """Test loading all templates from directory"""
        manager = TemplateManager(template_dir)
        manager.load_templates()
        
        assert len(manager.templates) == 3
        assert "spec" in manager.templates
        assert "plan" in manager.templates
        assert "tasks" in manager.templates
    
    def test_get_template(self, template_dir):
        """Test getting specific template by name"""
        manager = TemplateManager(template_dir)
        manager.load_templates()
        
        spec = manager.get_template("spec")
        assert spec is not None
        assert spec.name == "spec"
        assert spec.description == "Specification template"
        
        plan = manager.get_template("plan")
        assert plan is not None
        assert plan.name == "plan"
    
    def test_get_nonexistent_template(self, template_dir):
        """Test getting non-existent template returns None"""
        manager = TemplateManager(template_dir)
        manager.load_templates()
        
        result = manager.get_template("nonexistent")
        assert result is None
    
    def test_list_templates(self, template_dir):
        """Test listing all available templates"""
        manager = TemplateManager(template_dir)
        manager.load_templates()
        
        templates = manager.list_templates()
        assert len(templates) == 3
        
        names = [t.name for t in templates]
        assert "spec" in names
        assert "plan" in names
        assert "tasks" in names
    
    def test_load_templates_empty_dir(self, tmp_path):
        """Test loading from empty directory"""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        
        manager = TemplateManager(empty_dir)
        manager.load_templates()
        
        assert len(manager.templates) == 0
        assert manager.list_templates() == []
    
    def test_load_templates_nonexistent_dir(self, tmp_path):
        """Test loading from non-existent directory"""
        nonexistent = tmp_path / "nonexistent"
        
        manager = TemplateManager(nonexistent)
        manager.load_templates()
        
        assert len(manager.templates) == 0
    
    def test_reload_templates(self, template_dir):
        """Test reloading templates"""
        manager = TemplateManager(template_dir)
        manager.load_templates()
        
        assert len(manager.templates) == 3
        
        # Add new template
        (template_dir / "new.md").write_text("# {{title}}", encoding="utf-8")
        
        # Reload
        manager.load_templates()
        assert len(manager.templates) == 4
        assert "new" in manager.templates
