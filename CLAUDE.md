# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NOA is a Django-based Korean tax and accounting management platform for DaesungTax (대승택스). The system provides comprehensive financial management, government tax filing (Hometax integration), real-time chat, and AI-powered accounting assistance.

**Core Stack:**
- Django 4.1.8 with ASGI/Daphne
- Microsoft SQL Server (MSSQL) - existing legacy database
- React 17.0.2 frontend
- Redis for WebSocket channels
- OpenAI GPT integration with LlamaIndex RAG

## Initial Setup

### Prerequisites

**Required Software:**
- Python 3.8+ (recommended: Python 3.10)
- Node.js 14+ and npm
- Redis Server (Windows: download from Redis releases or use WSL/Docker)
- Microsoft SQL Server access (remote server at 211.63.194.154)
- Git for version control

**Optional:**
- Visual Studio Code or PyCharm
- SQL Server Management Studio (SSMS) for database exploration

### First-Time Setup Steps

**1. Clone and Navigate:**
```bash
cd K:\noa-django\Noa
# Or your chosen directory
```

**2. Create Virtual Environment:**
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Unix/MacOS
python3 -m venv .venv
source .venv/bin/activate
```

**3. Install Python Dependencies:**
```bash
# Install all required packages
pip install -r requirements.txt

# If installation fails, install packages incrementally:
# Core Django packages first
pip install Django==4.1.8
pip install mssql-django==1.2
pip install channels==4.0.0 daphne==4.0.0
pip install django-redis==5.2.0 redis==4.5.4

# Then other dependencies from requirements.txt
```

**4. Install Frontend Dependencies:**
```bash
cd static
npm install
cd ..
```

**5. Configure Environment Variables:**

Create `.env` file in project root (if not exists):
```bash
# .env
SECRET_KEY=django-insecure-(5d_*k*!6*rk=g=+06jl+=u%d76p&2jps!!1zhf#lck(=lg*nx
DEBUG=True

# Database (MSSQL)
DB_NAME=simplebook
DB_USER=sa
DB_PASSWORD=your_password_here
DB_HOST=211.63.194.154
DB_PORT=1433

# Redis
REDIS_HOST=127.0.0.1
REDIS_PORT=6379

# OpenAI API
OPENAI_API_KEY=your_openai_key_here

# Email Configuration (optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
```

**Note:** The project currently has hardcoded credentials in `noa/settings.py`. For production, migrate these to environment variables using `django-environ`.

**6. Verify Database Connection:**
```bash
# Test database connectivity
python manage.py dbshell
# Should connect to MSSQL server
# Exit with: exit
```

**7. Run Migrations:**
```bash
# Note: Most models are managed=False (existing DB)
# This mainly sets up Django's auth tables if needed
python manage.py migrate
```

**8. Create Superuser (Optional):**
```bash
python manage.py createsuperuser
```

**9. Collect Static Files:**
```bash
python manage.py collectstatic --noinput
```

**10. Start Redis Server:**

**Windows (if installed natively):**
```bash
# Run redis-server.exe
redis-server
```

**Windows (using WSL):**
```bash
wsl
sudo service redis-server start
# Or: redis-server
```

**Windows (using Docker):**
```bash
docker run -d -p 6379:6379 redis:latest
```

**Verify Redis is running:**
```bash
redis-cli ping
# Should return: PONG
```

**11. Start Development Server:**
```bash
# Option 1: ASGI server with full WebSocket support (recommended)
daphne -b 0.0.0.0 -p 8000 noa.asgi:application

# Option 2: Django development server (limited WebSocket)
python manage.py runserver
```

**12. Access the Application:**
- Main app: http://localhost:8000
- Admin portal: http://localhost:8000/admin/

### Troubleshooting Setup Issues

**MSSQL Connection Fails:**
```bash
# Check pyodbc driver installation
pip install pyodbc

# On Windows, may need to install ODBC Driver for SQL Server
# Download from: https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
```

**Redis Connection Fails:**
```bash
# Check Redis is running
redis-cli ping

# If not running, start Redis server
redis-server

# Check port 6379 is not blocked
netstat -an | grep 6379  # Unix
netstat -an | findstr 6379  # Windows
```

**Static Files Not Loading:**
```bash
# Ensure static files are collected
python manage.py collectstatic --noinput

# Check STATIC_ROOT in settings.py
# Should be: noa/static/
```

**Import Errors:**
```bash
# Ensure virtual environment is activated
# Windows: .venv\Scripts\activate
# Unix: source .venv/bin/activate

# Reinstall problematic packages
pip install --upgrade <package-name>
```

**Korean Text Shows as Garbled:**
- Verify database collation is `Korean_Wansung_CI_AS`
- Check terminal encoding supports UTF-8
- In Windows terminal, set codepage: `chcp 65001`

**WebSocket Chat Not Working:**
1. Verify Redis is running: `redis-cli ping`
2. Check Daphne is used (not runserver): `daphne noa.asgi:application`
3. Check browser console for WebSocket connection errors
4. Verify ALLOWED_HOSTS includes your domain

**PDF/Image Processing Errors:**
```bash
# Install Pillow dependencies
pip install Pillow

# For pdf2image, install poppler:
# Windows: Download from https://github.com/oschwartz10612/poppler-windows/releases
# Add poppler/bin to PATH

# For opencv:
pip install opencv-python
```

### Development Workflow

**Daily Development:**
```bash
# 1. Activate virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Unix

# 2. Ensure Redis is running
redis-cli ping

# 3. Start development server
daphne -b 0.0.0.0 -p 8000 noa.asgi:application

# 4. In another terminal, watch for frontend changes (if using webpack)
cd static
npm run watch  # If configured
```

**Adding New Dependencies:**
```bash
# Install package
pip install package-name

# Update requirements.txt
pip freeze > requirements.txt
```

**Database Changes:**
```bash
# For NEW models (not legacy models):
python manage.py makemigrations app_name
python manage.py migrate

# For existing models (managed=False), manual SQL required
```

## Development Commands

### Server Management

**Run development server (ASGI):**
```bash
# Use Daphne for full WebSocket support
daphne -b 0.0.0.0 -p 8000 noa.asgi:application

# Or standard Django (limited WebSocket support)
python manage.py runserver
```

**Activate virtual environment:**
```bash
# Windows
.venv\Scripts\activate

# Unix/MacOS
source .venv/bin/activate
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Database migrations:**
```bash
# Note: Models are managed=False (existing legacy DB)
# Only create migrations for new models you add
python manage.py makemigrations
python manage.py migrate
```

### Redis (Required for WebSockets)

**Start Redis server:**
```bash
# Must be running on 127.0.0.1:6379 for chat functionality
redis-server
```

### Frontend Development

**Install Node.js dependencies:**
```bash
cd static
npm install
```

**Collect static files:**
```bash
python manage.py collectstatic --noinput
```

## Architecture Overview

### Django Apps Structure

**`app/` - Main Business Logic (20+ submodules)**
- `authentication/` - Custom user login/logout flows
- `dashboard/` - Financial dashboards and analytics
- `accountGpt/` - GPT-powered accounting Q&A
- `vatSingo/`, `payrollSingo/`, `corpSingo/` - Tax filing modules
- `statementBS/`, `statementIS/`, `statementMC/` - Financial statements (Balance Sheet, Income Statement, Cash Flow)
- `slipLedgr/`, `traderLedgr/` - Accounting ledgers
- `proofSheet/` - Receipt/proof management
- `bizMail/` - Business email management
- `kakao/` - Kakao messaging integration
- `Google/` - Google OAuth and API integration

**`chat/` - Real-time WebSocket Chat**
- AsyncWebsocketConsumer in `consumers.py`
- WebSocket routing: `ws/chat/<room_name>/`
- Group-based broadcasting via Redis channel layers

**`admins/` - Admin Portal (15+ submodules)**
- `dsboard/` - Admin dashboard
- `mnguser/`, `mngCorp/`, `mngPay/` - User/business/payment management
- `staffList/`, `staffInfo/` - Staff management
- `blog/` - Blog/content management
- `auto/` - Automation features

**`gpt_engine/` - AI/LLM Integration**
- OpenAI GPT-3.5-turbo integration
- RAG pattern with LlamaIndex
- Document embeddings (Ada-002 model)
- Vector database for semantic search

### Database Architecture

**Database:** MSSQL (`simplebook` DB at 211.63.194.154)

**Key Model Groups:**

1. **User Models** - `MemUser`, `MemAdmin`, `MemDeal`, `userProfile`
2. **Accounting** - `AcntItemcd` (chart of accounts), `ActSlipledgr` (journal entries), `ActGeralledgr` (general ledger)
3. **Assets** - `ActAsset`, `ActAssettrn` (fixed assets and transactions)
4. **Tax/Government** - `TblHometax*` tables (Hometax scraping/filing data)
5. **Communications** - `TblMail`, `TblOfstKakaoSms`, `TblSms`

**Important:** All models use `managed=False` - this is an existing legacy database. Django does not control schema migrations. Only create new models if adding new tables.

### Frontend Architecture

**React Integration:**
- React components in `static/` directory
- Advanced data grids: ag-grid-react, Syncfusion Spreadsheet
- PDF handling: react-pdf, @react-pdf/renderer
- Excel export: xlsx library
- Material-UI (MUI) v5.5.0 components
- Direct MSSQL client connection from Node.js

**Tab-based UI Pattern:**
- Dashboard uses tab-based navigation
- `render_tab_template()` utility function in views
- AJAX detection for partial vs full page renders

### WebSocket/Real-time Architecture

**Channel Layers Configuration:**
```python
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [("127.0.0.1", 6379)]},
        "OPTIONS": {"timeout": 300}  # 5 minutes
    }
}
```

**WebSocket URL Pattern:**
- `ws://domain/ws/chat/<room_name>/`
- Authenticated via `AuthMiddlewareStack`
- Group-based message broadcasting

### Authentication Patterns

**Multiple Auth Systems:**

1. **Django built-in** - Session-based (60000s timeout)
2. **Custom business auth** - `MemUser` model with `user_id` (max 12 chars), business registration number (`Biz_No`)
3. **OAuth2** - django-allauth for social login
4. **Multi-tenant** - django-hosts for subdomain routing (www, admin)

### AI/GPT Integration

**RAG Implementation (`gpt_engine/`):**

1. Document loading and chunking
2. OpenAI embeddings generation (Ada-002)
3. Vector storage in local vector DB
4. Query processing with LlamaIndex
5. Context-aware responses with GPT-3.5-turbo

**Usage pattern:**
```python
from gpt_engine.query_engine import process_query
result = process_query("사용자 질문")
```

## Important Patterns and Conventions

### Model Naming Conventions

- `MemUser`, `MemAdmin`, `MemDeal` - User/relationship tables
- `Acnt*` - Accounting/chart of accounts
- `Act*` - Activity/transaction tables (ledgers, assets)
- `Tbl*` - Reference/master data tables

### Account Code Ranges

Standard account code structure:
- **401-430**: Sales accounts
- **451-470**: Cost of Goods Sold (COGS)
- **501-599**: Operating expenses
- **601-699**: Non-operating income/expenses

### Database Field Patterns

Korean text fields use `Korean_Wansung_CI_AS` collation:
```python
db_column='Corp_Nm'  # Corporate name in Korean
```

All foreign keys map via `db_column` to existing MSSQL schema.

### Tab Template Rendering

Views should detect AJAX requests for tab loading:
```python
def render_tab_template(request, tab_template, context):
    if request.is_ajax():
        return render(request, tab_template, context)
    return render(request, 'dashboard.html', {'content': tab_template, **context})
```

### Financial Calculations

Use raw SQL for complex aggregations:
- Month-by-month sales analysis
- Multi-year comparisons
- Account hierarchy traversal
- Depreciation calculations

### External API Integrations

**Hometax (Government Tax System):**
- Selenium-based web scraping
- Automated form filling
- Data extraction from tax portal

**Kakao Messaging:**
- Business notification system
- SMS/LMS integration via `TblOfstKakaoSms`

**Google APIs:**
- OAuth authentication
- Cloud service integration

## Security Notes

**Current Settings (Development):**
- `DEBUG = True`
- `ALLOWED_HOSTS = ['*']`
- `CORS_ALLOW_ALL_ORIGINS = True`
- SECRET_KEY exposed in settings.py

**Before Production:**
- Set `DEBUG = False`
- Restrict `ALLOWED_HOSTS` to actual domains
- Configure CORS for specific origins only
- Move SECRET_KEY to environment variables
- Review iframe allow middleware
- Enable HTTPS/SSL
- Restrict database user permissions

## Middleware Stack Order

Critical middleware ordering (don't reorder):
1. django-hosts request (top)
2. CORS middleware (near top)
3. Common middleware
4. HTML minification
5. Security middleware
6. Sessions
7. CSRF
8. Authentication
9. Messages
10. XFrame options
11. Custom iframe allow middleware
12. django-hosts response (bottom)

## File Upload Handling

**Media configuration:**
```python
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
```

**Upload processing:**
- Pillow for image processing
- pdf2image for PDF handling
- opencv-python for advanced image operations

## Korean Localization

- Language code: `ko-kr`
- Timezone: `Asia/Seoul`
- Database collation: `Korean_Wansung_CI_AS`
- Humanize template tag for number formatting (천 단위 comma)

## Testing Considerations

This project does not have a formal test suite. When testing:

1. **Manual Testing Required:**
   - Test all WebSocket connections with Redis running
   - Verify MSSQL connectivity before running views
   - Check Hometax integration with valid credentials
   - Test file uploads to `media/` directory

2. **Critical Paths:**
   - User authentication flow (multiple auth backends)
   - Financial statement generation (complex SQL)
   - Real-time chat functionality (WebSocket + Redis)
   - PDF/Excel export functionality
   - Kakao message sending

3. **Database Testing:**
   - Use test database, not production MSSQL
   - Be aware models are `managed=False`
   - Raw SQL queries may break if schema changes

## Common Gotchas

1. **WebSocket connections fail** → Check Redis is running on 127.0.0.1:6379
2. **Database connection errors** → Verify MSSQL server accessibility (211.63.194.154)
3. **Static files not loading** → Run `python manage.py collectstatic`
4. **Korean text garbled** → Check database collation is `Korean_Wansung_CI_AS`
5. **Tab navigation broken** → Ensure AJAX detection in views
6. **GPT queries fail** → Verify OpenAI API key and vector DB initialization
7. **OAuth errors** → Check django-allauth configuration and redirect URIs
8. **PDF generation fails** → Install system dependencies (poppler for pdf2image)

## Deployment Notes

**Platform:** Windows Server + IIS

**ASGI Server:** Daphne (required for WebSocket support)

**Static Files:** Must be collected to `noa/static/` for IIS

**Web.config:** IIS FastCGI configuration present in root

**Environment Variables:** Store in `.env` file:
- Database credentials
- OpenAI API key
- Email SMTP credentials
- OAuth client secrets

**Redis:** Must be running as Windows service or Docker container

**Process Management:** Use Windows services or supervisor for Daphne process management
