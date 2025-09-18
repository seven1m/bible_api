#!/usr/bin/env python3
"""Generate a human-readable Markdown test report from a JUnit XML file.

Usage:
  python tools/generate_test_report.py reports/junit.xml > reports/test-report.md

If no path supplied, defaults to reports/junit.xml.
"""
from __future__ import annotations
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timezone


def parse_junit(path: Path):
    tree = ET.parse(path)
    root = tree.getroot()
    # Support either <testsuite> root or <testsuites>
    suites = []
    if root.tag == 'testsuite':
        suites = [root]
    else:
        suites = list(root.findall('testsuite'))
    total_tests = 0
    total_failures = 0
    total_errors = 0
    total_skipped = 0
    cases = []
    for suite in suites:
        total_tests += int(suite.get('tests', 0))
        total_failures += int(suite.get('failures', 0))
        total_errors += int(suite.get('errors', 0))
        total_skipped += int(suite.get('skipped', 0))
        for case in suite.findall('testcase'):
            name = case.get('name')
            classname = case.get('classname')
            time = case.get('time')
            status = 'passed'
            failure_text = ''
            failure_elem = case.find('failure')
            error_elem = case.find('error')
            skipped_elem = case.find('skipped')
            if failure_elem is not None:
                status = 'failed'
                failure_text = (failure_elem.get('message') or '').strip()[:500]
            elif error_elem is not None:
                status = 'error'
                failure_text = (error_elem.get('message') or '').strip()[:500]
            elif skipped_elem is not None:
                status = 'skipped'
                failure_text = skipped_elem.get('message') or ''
            cases.append({
                'name': name,
                'classname': classname,
                'time': time,
                'status': status,
                'detail': failure_text
            })
    return {
        'total': total_tests,
        'failures': total_failures,
        'errors': total_errors,
        'skipped': total_skipped,
        'passed': total_tests - total_failures - total_errors - total_skipped,
        'cases': cases,
    }


def generate_markdown(summary: dict) -> str:
    lines = []
    lines.append(f"# Test Report ({datetime.now(timezone.utc).isoformat()})")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total: {summary['total']}")
    lines.append(f"- Passed: {summary['passed']}")
    lines.append(f"- Failed: {summary['failures']}")
    lines.append(f"- Errors: {summary['errors']}")
    lines.append(f"- Skipped: {summary['skipped']}")
    lines.append("")
    if summary['failures'] or summary['errors']:
        lines.append("## Failures / Errors")
        lines.append("")
        for c in summary['cases']:
            if c['status'] in ('failed', 'error'):
                lines.append(f"### {c['classname']}::{c['name']}")
                lines.append("")
                # Add fenced code block with failure detail (avoid triple backticks confusion)
                lines.append('```text')
                lines.append(c['detail'] or '(no message)')
                lines.append('```')
                lines.append("")
    lines.append("## All Tests")
    lines.append("")
    status_icon = {'passed': 'PASS', 'failed': 'FAIL', 'error': 'ERR', 'skipped': 'SKIP'}
    for c in summary['cases']:
        icon = status_icon.get(c['status'], c['status'].upper())
        lines.append(f"- [{icon}] {c['classname']}::{c['name']} ({c['time']}s)")
    return '\n'.join(lines)


def main():
    xml_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('reports/junit.xml')
    if not xml_path.exists():
        print(f"JUnit file not found: {xml_path}", file=sys.stderr)
        return 2
    summary = parse_junit(xml_path)
    md = generate_markdown(summary)
    print(md)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
