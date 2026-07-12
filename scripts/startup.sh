#!/bin/bash
# Backend startup script

set -e

echo "=== 智媒圈 Backend Startup ==="

# Create data directories if not exist
python -c "
import os
dirs = ['rules','analytics','scheduled','agents','templates','ab_tests',
        'teams','videos','images','competitors','calibration','rewrites',
        'router_history','insights','workflows']
base = '/app/data'
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)
print('Data directories created:', len(dirs))
"

# Start uvicorn
echo "Starting FastAPI server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4