#!/usr/bin/env python3
import re
import sys
from pathlib import Path

CARD_PATTERN = re.compile(r"\[(?:0\..N|1\..N|0\..1|1\..1|0\..N|N|1|0\.\.N)\]|")
ENTITY_DECL = re.compile(r"^entity\s+([A-Za-z_][A-Za-z0-9_]*)")
WEAK_ENTITY_DECL = re.compile(r"^weak entity\s+([A-Za-z_][A-Za-z0-9_]*)")
REL_DECL = re.compile(r"^relationship\s+([A-Za-z_][A-Za-z0-9_]*)")
NOTATION_DECL = re.compile(r"^notation\s*=\s*([A-Za-z_]+)")

def check_file(path: Path):
    text = path.read_text(encoding='utf-8')
    lines = text.splitlines()
    issues = []

    # Check header
    if not lines or not lines[0].strip().startswith('erdiagram'):
        issues.append('Missing or malformed header: file should start with "erdiagram ModelName"')

    # Check notation
    if not any(line.strip().startswith('notation=') for line in lines[:10]):
        issues.append('Missing notation declaration (e.g. notation=crowsfoot) in the first 10 lines')

    # Braces balancing
    open_braces = 0
    for i, line in enumerate(lines, start=1):
        open_braces += line.count('{')
        open_braces -= line.count('}')
        if open_braces < 0:
            issues.append(f'Unmatched closing brace on line {i}')
            open_braces = 0
    if open_braces != 0:
        issues.append('Mismatched braces: some blocks are not closed')

    # Simple entity/relationship name checks
    for i, line in enumerate(lines, start=1):
        s = line.strip()
        if s.startswith('entity ') or s.startswith('weak entity '):
            m = ENTITY_DECL.match(s) or WEAK_ENTITY_DECL.match(s)
            if not m:
                issues.append(f'Invalid entity declaration on line {i}: "{s}"')
        if s.startswith('relationship '):
            m = REL_DECL.match(s)
            if not m:
                issues.append(f'Invalid relationship declaration on line {i}: "{s}"')

    # Check relationship arrow and cardinality patterns
    rel_block = False
    for i, line in enumerate(lines, start=1):
        if line.strip().startswith('relationship '):
            rel_block = True
        if rel_block:
            if '->' in line:
                # quick cardinality check: presence of [ and ] near entity names
                tokens = line.split('->')
                for t in tokens:
                    if '[' in t and ']' in t:
                        # crude check for valid cardinality patterns
                        if not re.search(r"\[(?:0\..N|1\..N|0\..1|1\..1|N|1)\]", t):
                            # allow role syntax like [1 | "role"]
                            if '|' in t and re.search(r"\[(?:0\..N|1\..N|0\..1|1\..1|N|1)\s*\|", t):
                                pass
                            else:
                                issues.append(f'Unrecognized cardinality on line {i}: "{line.strip()}"')
            if line.strip().endswith('}'):
                rel_block = False

    # Check for quoted identifiers (not allowed)
    for i, line in enumerate(lines, start=1):
        if '"' in line:
            issues.append(f'Quoted identifiers or roles found on line {i}: bigER prefers unquoted names; using quotes may cause parser errors')

    return issues

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: biger_validator.py <path_to_erd_file>')
        sys.exit(2)
    p = Path(sys.argv[1])
    if not p.exists():
        print(f'File not found: {p}')
        sys.exit(2)
    issues = check_file(p)
    if not issues:
        print('PASS: No obvious syntax problems found by the lightweight validator.')
        sys.exit(0)
    else:
        print('Found issues:')
        for it in issues:
            print('- ' + it)
        sys.exit(1)
