FROM python:3.12-slim AS base
WORKDIR /app

FROM base AS deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS runner
COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin
COPY . .

# Create data directories
RUN python -c "import os; dirs = ['rules','analytics','scheduled','agents','templates','ab_tests','teams','videos','images','competitors','calibration','rewrites','router_history','insights','workflows']; base = '/app/data'; [os.makedirs(os.path.join(base, d), exist_ok=True) for d in dirs]; print('Created', len(dirs), 'directories')"

# Make startup.sh executable
RUN chmod +x /app/startup.sh

EXPOSE 8000

# Start server
CMD ["/bin/bash", "/app/startup.sh"]
