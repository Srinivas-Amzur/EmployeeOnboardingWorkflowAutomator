import re
from pathlib import Path

# Fix all test files
test_files = [
    'tests/unit/test_employees_analytics.py',
    'tests/unit/test_onboarding_workflow.py',
    'tests/unit/test_notifications.py',
    'tests/unit/test_rag_service.py',
    'tests/unit/test_orchestration.py',
]

for file in test_files:
    p = Path(file)
    if not p.exists():
        print(f"Skipping {file} - not found")
        continue
    
    content = p.read_text()
    
    # Add import if not there
    if 'from httpx import' in content and 'ASGITransport' not in content:
        content = content.replace('from httpx import AsyncClient', 'from httpx import ASGITransport, AsyncClient')
    
    # Fix AsyncClient calls - replace the problematic pattern
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        if 'async with AsyncClient(app=app' in line:
            indent = len(line) - len(line.lstrip())
            new_lines.append(' ' * indent + 'transport = ASGITransport(app=app)')
            new_lines.append(line.replace('AsyncClient(app=app', 'AsyncClient(transport=transport'))
        else:
            new_lines.append(line)
    
    p.write_text('\n'.join(new_lines))
    print(f"Fixed {file}")

print('Done!')
