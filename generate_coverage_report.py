"""
Generate detailed coverage gaps report.
"""

from pathlib import Path
import subprocess
import json

def run_coverage():
    """Run pytest with coverage and generate JSON report"""
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/", "--cov=src", "--cov-report=json", "--cov-report=term", "-q"],
        capture_output=True,
        text=True
    )
    return result.stdout, result.returncode

def analyze_coverage():
    """Analyze coverage.json and identify gaps"""
    coverage_file = Path("coverage.json")
    
    if not coverage_file.exists():
        print("No coverage.json found. Running tests first...")
        run_coverage()
    
    with open(coverage_file) as f:
        data = json.load(f)
    
    files = data.get("files", {})
    
    gaps = {
        "critical_gaps": [],
        "gui_gaps": [],
        "mcp_gaps": [],
        "core_gaps": [],
        "summary": {}
    }
    
    for file_path, file_data in files.items():
        if "src\\" not in file_path and "src/" not in file_path:
            continue
        
        coverage_pct = file_data.get("summary", {}).get("percent_covered", 0)
        missing_lines = file_data.get("missing_lines", [])
        
        file_info = {
            "file": file_path,
            "coverage": f"{coverage_pct:.1f}%",
            "missing_lines": len(missing_lines),
            "critical_untested": []
        }
        
        # Identify critical untested code
        if "gui" in file_path:
            if coverage_pct < 50:
                gaps["gui_gaps"].append(file_info)
        elif "mcp" in file_path:
            if coverage_pct < 40:
                gaps["mcp_gaps"].append(file_info)
        elif "core" in file_path:
            if coverage_pct < 60:
                gaps["core_gaps"].append(file_info)
        
        if coverage_pct < 30:
            gaps["critical_gaps"].append(file_info)
    
    # Summary
    total_statements = data.get("totals", {}).get("num_statements", 0)
    covered_statements = data.get("totals", {}).get("covered_lines", 0)
    missing_statements = data.get("totals", {}).get("missing_lines", 0)
    overall_coverage = data.get("totals", {}).get("percent_covered", 0)
    
    gaps["summary"] = {
        "total_statements": total_statements,
        "covered": covered_statements,
        "missing": missing_statements,
        "coverage": f"{overall_coverage:.1f}%"
    }
    
    return gaps

def generate_report(gaps):
    """Generate markdown report"""
    report = []
    
    report.append("# Test Coverage Gaps Report")
    report.append("")
    report.append(f"**Generated**: {Path.cwd()}")
    report.append("")
    
    # Summary
    summary = gaps["summary"]
    report.append("## Overall Coverage")
    report.append("")
    report.append(f"- **Total Statements**: {summary['total_statements']}")
    report.append(f"- **Covered**: {summary['covered']}")
    report.append(f"- **Missing**: {summary['missing']}")
    report.append(f"- **Coverage**: {summary['coverage']}")
    report.append("")
    
    # Critical gaps (< 30%)
    report.append("## Critical Gaps (< 30% Coverage)")
    report.append("")
    if gaps["critical_gaps"]:
        report.append("| File | Coverage | Missing Lines |")
        report.append("|------|----------|---------------|")
        for gap in sorted(gaps["critical_gaps"], key=lambda x: float(x["coverage"].rstrip('%'))):
            report.append(f"| {gap['file']} | {gap['coverage']} | {gap['missing_lines']} |")
    else:
        report.append("✅ No files with critical coverage gaps!")
    report.append("")
    
    # GUI gaps
    report.append("## GUI Coverage Gaps (< 50%)")
    report.append("")
    if gaps["gui_gaps"]:
        report.append("| File | Coverage | Missing Lines |")
        report.append("|------|----------|---------------|")
        for gap in sorted(gaps["gui_gaps"], key=lambda x: float(x["coverage"].rstrip('%'))):
            report.append(f"| {gap['file']} | {gap['coverage']} | {gap['missing_lines']} |")
        report.append("")
        report.append("**Recommendation**: Add GUI integration tests for workflows")
    else:
        report.append("✅ GUI coverage is adequate!")
    report.append("")
    
    # MCP gaps
    report.append("## MCP Coverage Gaps (< 40%)")
    report.append("")
    if gaps["mcp_gaps"]:
        report.append("| File | Coverage | Missing Lines |")
        report.append("|------|----------|---------------|")
        for gap in sorted(gaps["mcp_gaps"], key=lambda x: float(x["coverage"].rstrip('%'))):
            report.append(f"| {gap['file']} | {gap['coverage']} | {gap['missing_lines']} |")
        report.append("")
        report.append("**Recommendation**: MCP services need integration tests with mocked connections")
    else:
        report.append("✅ MCP coverage is adequate!")
    report.append("")
    
    # Core gaps
    report.append("## Core Coverage Gaps (< 60%)")
    report.append("")
    if gaps["core_gaps"]:
        report.append("| File | Coverage | Missing Lines |")
        report.append("|------|----------|---------------|")
        for gap in sorted(gaps["core_gaps"], key=lambda x: float(x["coverage"].rstrip('%'))):
            report.append(f"| {gap['file']} | {gap['coverage']} | {gap['missing_lines']} |")
        report.append("")
        report.append("**Recommendation**: Core logic is critical - aim for 80%+ coverage")
    else:
        report.append("✅ Core coverage is adequate!")
    report.append("")
    
    # Recommendations
    report.append("## Testing Recommendations")
    report.append("")
    report.append("### Priority 1: Critical Paths")
    report.append("- [ ] Document save/load operations")
    report.append("- [ ] Git commit workflow")
    report.append("- [ ] Project creation and loading")
    report.append("- [ ] Template rendering")
    report.append("")
    report.append("### Priority 2: Integration Tests")
    report.append("- [ ] End-to-end document editing workflow")
    report.append("- [ ] Multi-document navigation")
    report.append("- [ ] Git branch switching with unsaved changes")
    report.append("- [ ] MCP query execution and results display")
    report.append("- [ ] Search and replace across files")
    report.append("")
    report.append("### Priority 3: Edge Cases")
    report.append("- [ ] Large file handling (>5MB)")
    report.append("- [ ] Crash recovery scenarios")
    report.append("- [ ] Concurrent file modifications")
    report.append("- [ ] Invalid template structures")
    report.append("- [ ] Network failures during git operations")
    report.append("")
    report.append("### Priority 4: GUI Coverage")
    report.append("- [ ] All button click handlers")
    report.append("- [ ] Keyboard shortcuts")
    report.append("- [ ] Context menu actions")
    report.append("- [ ] Drag and drop operations")
    report.append("- [ ] Window resize behavior")
    report.append("")
    
    return "\\n".join(report)

if __name__ == "__main__":
    print("Running coverage analysis...")
    stdout, code = run_coverage()
    print(stdout)
    
    print("\\nAnalyzing coverage gaps...")
    gaps = analyze_coverage()
    
    report = generate_report(gaps)
    
    # Write report
    report_path = Path("COVERAGE_GAPS.md")
    report_path.write_text(report)
    
    print(f"\\nReport generated: {report_path}")
    print("\\nSummary:")
    print(f"  Total Coverage: {gaps['summary']['coverage']}")
    print(f"  Critical Gaps: {len(gaps['critical_gaps'])} files")
    print(f"  GUI Gaps: {len(gaps['gui_gaps'])} files")
    print(f"  MCP Gaps: {len(gaps['mcp_gaps'])} files")
    print(f"  Core Gaps: {len(gaps['core_gaps'])} files")
