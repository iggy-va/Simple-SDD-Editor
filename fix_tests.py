"""Script to fix test files"""
from pathlib import Path
import re

# Fix test_editor.py
editor_test = Path("tests/unit/gui/test_editor.py")
content = editor_test.read_text()
# Replace create_new calls
content = re.sub(
    r'SpeckitDocument\.create_new\([^)]+\)',
    'sample_document',
    content
)
# Update function signatures
content = re.sub(
    r'(\w+\(self, qtbot: QtBot), tmp_path: Path\)',
    r'\1, sample_document: SpeckitDocument)',
    content
)
# Fix doc variable assignments that now conflict
content = re.sub(
    r'doc = sample_document\s+doc\.content',
    'sample_document.content',
    content
)
editor_test.write_text(content)
print("Fixed test_editor.py")

# Fix test_main_window.py
main_window_test = Path("tests/unit/gui/test_main_window.py")
content = main_window_test.read_text()
# Add QAction import
if "from PySide6.QtWidgets import" in content and "QAction" not in content:
    content = content.replace(
        "from PySide6.QtWidgets import",
        "from PySide6.QtWidgets import QAction,"
    )
# Fix API calls
content = re.sub(r'SpeckitDocument\.create_new\([^)]+\)', 'sample_document', content)
content = re.sub(r'SpeckitProject\.create_new\([^)]+\)', 'sample_project', content)
# Update signatures
content = re.sub(
    r'(def \w+\(self, qtbot: QtBot), tmp_path: Path\)',
    r'\1, sample_document: SpeckitDocument, sample_project: SpeckitProject)',
    content
)
main_window_test.write_text(content)
print("Fixed test_main_window.py")

# Fix test_git_panel.py
git_test = Path("tests/unit/gui/test_git_panel.py")
content = git_test.read_text()
# Fix attribute names
content = content.replace('panel.commit_btn', 'panel.commit_button')
content = content.replace('panel.pull_btn', 'panel.pull_button')  
content = content.replace('panel.push_btn', 'panel.push_button')
content = content.replace('assert panel.refresh_btn', 'assert panel.branch_combo')
content = content.replace('initial_count = panel.status_list.count()', 'initial_count = panel.file_list.count()')
content = content.replace('assert panel.status_list', 'assert panel.file_list')
# Fix API calls
content = re.sub(r'SpeckitProject\.create_new\([^)]+\)', 'git_project', content)
# Update signatures
content = re.sub(
    r'(def \w+\(self, qtbot: QtBot), tmp_path: Path\)',
    r'\1, git_project: SpeckitProject)',
    content
)
git_test.write_text(content)
print("Fixed test_git_panel.py")

# Fix test_mcp_panel.py
mcp_test = Path("tests/unit/gui/test_mcp_panel.py")
content = mcp_test.read_text()
# Fix attribute names
content = content.replace('panel.execute_btn', 'panel.execute_button')
content = content.replace('panel.export_btn', 'panel.export_button')
# Fix query types
content = content.replace('"JQL"', '"JQL (Jira)"')
content = content.replace("'JQL'", "'JQL (Jira)'")
mcp_test.write_text(content)
print("Fixed test_mcp_panel.py")

print("All test files fixed!")
