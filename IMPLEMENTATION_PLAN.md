# Implementation Plan: Volatility-Adjusted Trend Break Detection System

## Project Goals

### Phase 1: Core Algorithm Development (Current)

✅ Implement robust trend detection for highly volatile instruments (options/warrants)
✅ Detect significant trend breaks (>20-30%) while filtering noise (<20%)
✅ Generate actionable buy/sell recommendations with confidence scores
✅ Daily automated analysis with comprehensive logging

### Phase 2: MongoDB Integration (Future)

🔄 Fetch instrument list (WKNs) from MongoDB "Musterdepot" collection
🔄 Store analysis results and historical signals in MongoDB
🔄 Sync with real portfolio:

   - **BUY signals**: Only actionable if WKN not currently owned
   - **SELL signals**: Only actionable if WKN currently in portfolio

🔄 Track recommendation history and performance

### Phase 3: Cloud Deployment (Future)

🔄 Dockerize application for consistent deployment
🔄 Deploy to Azure Container Instances or Azure Container Apps
🔄 Schedule execution using Azure Functions or Logic Apps
🔄 Integrate with Azure Key Vault for secrets management
🔄 Enable email notifications via Azure Communication Services

### Phase 4: Production Features (Future)

🔄 Email reporting (activated after algorithm validation)
🔄 Performance tracking and backtesting
🔄 Web dashboard for viewing signals
🔄 SMS alerts for critical signals
🔄 Risk management and position sizing

---

## Technical Architecture

### Current State (Development)

```text
Local Machine
├── Python Application (uv)
│   ├── Data: API calls to securities provider
│   └── Storage: Local file system (logs, charts)
├── Execution: Manual or Windows Task Scheduler
└── Output: Console + Local files
```

### Target State (Production)

```text
Azure Cloud
├── Docker Container
│   ├── Python Application
│   └── Automated scheduling
├── Azure MongoDB (CosmosDB)
│   ├── musterdepot_collection (WKNs to analyze)
│   ├── portfolio_collection (owned positions)
│   └── signals_collection (historical recommendations)
├── Azure Key Vault (API keys, SMTP credentials)
└── Azure Communication Services (Email alerts)
```

---

## Phase 1 Implementation Steps (Current Focus)

### ✅ **Step 1: Create Trend Detection Configuration** (COMPLETED)

**File:** `app/trend_config.py` (created 2026-02-10)

**Status:** ✅ Complete - Configuration created with optimized parameters for hourly/daily timeframes

**Bug Fixes:**

- Fixed lookback_window: 20 → 240 hours (to capture full 14-day history)
- Fixed thresholds: 0.20 → 20.0 (percentage values, not decimals)

**Content:**

```python
"""Configuration for trend detection algorithms."""

# Hourly candle configuration (14 days ≈ 336 periods)
HOURLY_CONFIG = {
    # Supertrend parameters
    'supertrend_atr_period': 7,      # Fast reaction for volatile instruments
    'supertrend_multiplier': 3.5,    # Wider bands to reduce false signals
    
    # ADX trend strength
    'adx_period': 10,                # Shorter for hourly data
    'atr_period': 14,                # Standard ATR period
    
    # Drawdown/Rally detection
    'lookback_window': 20,           # Periods to find recent high/low (~2.5 days)
    
    # Signal thresholds
    'min_threshold': 0.20,           # 20% - significant move
    'severe_threshold': 0.30,        # 30% - critical move
    'min_adx_strength': 25,          # Minimum ADX for "strong trend"
    
    # Optional confirmation
    'use_ema_confirmation': True,
    'ema_fast_period': 8,            # ~1 trading day
    'ema_slow_period': 21,           # ~2.5 trading days
    
    # Volatility adjustment
    'use_dynamic_thresholds': True,
    'volatility_quantile': 0.75,    # 75th percentile
}

# Daily candle configuration (1 month ≈ 22 periods)
DAILY_CONFIG = {
    'supertrend_atr_period': 10,
    'supertrend_multiplier': 3.0,
    'adx_period': 14,
    'atr_period': 14,
    'lookback_window': 10,           # ~2 weeks
    'min_threshold': 0.20,
    'severe_threshold': 0.30,
    'min_adx_strength': 25,
    'use_ema_confirmation': True,
    'ema_fast_period': 5,
    'ema_slow_period': 13,
    'use_dynamic_thresholds': True,
    'volatility_quantile': 0.75,
}

def get_config(timeframe: str = 'hourly') -> dict:
    """Get configuration for specified timeframe."""
    configs = {
        'hourly': HOURLY_CONFIG,
        'hour': HOURLY_CONFIG,
        'daily': DAILY_CONFIG,
        'day': DAILY_CONFIG,
    }
    return configs.get(timeframe.lower(), HOURLY_CONFIG)
```

---

### **Step 2: Implement Core Trend Detection**

**File:** `app/analysis.py` (add new function)

**Function:** `detect_trend_break(df: pd.DataFrame, config: dict, timeframe: str) -> dict`

**Algorithm:**

1. Extract OHLC data as numpy arrays
2. Calculate Supertrend (use existing `supertrend()` from `app/indicators.py`)
3. Calculate ADX and directional indicators (ta-lib)
4. Calculate ATR and normalize to percentage
5. Calculate drawdowns and rallies from recent highs/lows
6. Apply dynamic volatility thresholds if enabled
7. Generate signal based on combined conditions
8. Determine confidence level

**Signal Logic:**

**STRONG_SELL:**

- Drawdown > 30% OR
- (Drawdown > 20% AND ADX > 40 AND all bearish indicators aligned)

**SELL:**

- Drawdown > 20% AND
- Supertrend = -1 (downtrend) AND
- ADX > 25 (strong trend) AND
- MinusDI > PlusDI (bearish momentum)

**BUY:**

- Rally > 20% from recent low AND
- Supertrend = +1 (uptrend) AND
- ADX > 25 AND
- PlusDI > MinusDI (bullish momentum)

**HOLD:**

- None of above conditions met

**Return structure:**

```python
{
    'action': 'SELL' | 'STRONG_SELL' | 'BUY' | 'HOLD',
    'reason': 'Detailed explanation',
    'confidence': 'HIGH' | 'MEDIUM' | 'LOW',
    'metrics': {
        'supertrend_direction': 1 | -1,
        'adx': float,
        'plus_di': float,
        'minus_di': float,
        'drawdown_pct': float,
        'rally_pct': float,
        'atr_pct': float,
        'current_price': float,
        # ... more metrics
    },
    'timestamp': pd.Timestamp
}
```

---

### ✅ **Step 3: Integrate into Main Loop** (COMPLETED)

**File:** `app/main.py` (modified 2026-02-10)

**Status:** ✅ Complete - Trend detection integrated, debug output added

**Bug Fixes:**
- Fixed Windows console encoding (UTF-8 for emoji support)
- Fixed dictionary key access (action/metrics structure)
- Added debug output showing data range validation

**Changes:**

1. Import new functions
2. After parabola analysis, call `detect_trend_break()`
3. Add trend signal to results list
4. Update console output with signal info

**Modified results structure:**

```python
results.append({
    "WKN": wkn,
    "Name": name,
    "Current Price": f"{current_price:.2f} €",
    "Parabola": recommendation,           # Existing
    "Trend Signal": trend_signal['action'], # New
    "Confidence": trend_signal['confidence'],
    "Reason": trend_signal['reason'],
    "ADX": f"{trend_signal['metrics']['adx']:.1f}",
    "Drawdown %": f"{trend_signal['metrics']['drawdown_pct']:.1f}%",
})
```

---

### **Step 4: Enhanced Email Reporting**

**File:** `app/main.py` (email section)

**Changes:**

1. Filter results by signal type
2. Sort by priority (STRONG_SELL > SELL > BUY, then by confidence)
3. Create separate HTML sections for sells vs buys
4. Apply CSS styling based on signal severity

**Email structure:**

```text
Subject: 📊 Portfolio Analysis: X SELL, Y BUY signals

Summary Box:
- 🔴 X positions to SELL
- 🟢 Y positions to BUY
- ⚪ Z positions to HOLD

[SELL Signals Table] - red/orange highlighting
[BUY Signals Table] - green highlighting
[Complete Portfolio Table] - all positions
```

---

### **Step 5: Logging & Debugging**

**File:** `app/main.py` (setup section)

**Add:**

- Create `logs/` directory
- Configure logging to file + console
- Log key events: start, each security, signals, errors, completion
- Log filename: `logs/analysis_YYYYMMDD_HHMMSS.log`

---

### **Step 6: Optimize Supertrend Parameters**

**File:** `app/indicators.py` (modify existing)

**Change:** Make `supertrend()` function parameters configurable

- Current: hardcoded `atr_period=10`, `multiplier=3.0`
- New: accept parameters from config

---

### **Step 7: Directory Structure**

**Create:**

```text
logs/                   # Analysis logs
charts/                 # Candlestick charts
reports/                # Daily HTML reports
```

**Update:** `.gitignore` to exclude these directories

---

### **Step 8: Testing & Validation**

**Create:** `tests/test_trend_detection.py`

**Test cases:**

- Strong downtrend (30% drop) → STRONG_SELL
- Moderate downtrend (25% drop) → SELL
- Normal fluctuation (10% move) → HOLD
- Strong uptrend (25% rally) → BUY
- Volatility adjustment working correctly

**Validation with real data:**

- Test HT8UZB (known crash 31.01.2026) → should detect SELL
- Test stable ETF → should show mostly HOLD

---

## Phase 2 Implementation (MongoDB Integration)

### **Step 9: MongoDB Schema Design**

**Database:** `portfolio_analyzer`

**Collections:**

```javascript
// musterdepot_collection
{
  _id: ObjectId,
  name: "MegatrendFolger",
  wkns: ["HT8UZB", "JU5YHH", ...],
  active: true,
  created_at: ISODate,
  updated_at: ISODate
}

// portfolio_collection (real holdings)
{
  _id: ObjectId,
  wkn: "HT8UZB",
  name: "HSBC Alphabet Call",
  quantity: 100,
  avg_buy_price: 3.50,
  current_value: 280.00,
  last_updated: ISODate,
  active: true
}

// signals_collection (recommendation history)
{
  _id: ObjectId,
  wkn: "HT8UZB",
  signal: "STRONG_SELL",
  confidence: "HIGH",
  reason: "Drawdown >30%...",
  metrics: {...},
  price_at_signal: 2.80,
  timestamp: ISODate,
  actioned: false,
  action_date: null
}
```

---

### **Step 10: MongoDB Integration Module**

**File:** `app/db.py` (new file)

**Functions:**

```python
# Connection
async def get_db_connection() -> AsyncIOMotorClient

# Musterdepot operations
async def fetch_wkns_from_musterdepot(depot_name: str) -> list[str]

# Portfolio operations
async def get_current_holdings() -> list[dict]
async def is_wkn_in_portfolio(wkn: str) -> bool

# Signal operations
async def save_signal(signal: dict) -> str
async def get_signal_history(wkn: str, days: int = 30) -> list[dict]

# Smart recommendations
async def filter_actionable_signals(signals: list[dict]) -> dict:
    """
    Returns:
    {
        'actionable_sells': [...],  # WKNs we own that should be sold
        'actionable_buys': [...],   # WKNs we don't own that should be bought
        'ignored': [...]            # Signals we can't act on
    }
    """
```

---

### **Step 11: Smart Signal Filtering**

**File:** `app/main.py` (modify)

**Logic:**

```python
# After generating all signals
portfolio_holdings = await get_current_holdings()
owned_wkns = {h['wkn'] for h in portfolio_holdings}

# Filter signals
actionable_sells = [
    sig for sig in all_signals 
    if sig['action'] in ['SELL', 'STRONG_SELL'] 
    and sig['wkn'] in owned_wkns
]

actionable_buys = [
    sig for sig in all_signals
    if sig['action'] == 'BUY'
    and sig['wkn'] not in owned_wkns
]

# Email only includes actionable signals
```

---

### **Step 12: MongoDB Configuration**

**File:** `app/settings.py` (add MongoDB settings)

**Add to .env:**

```text
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=portfolio_analyzer
```

**Dependencies:** Add to `pyproject.toml`:

```toml
dependencies = [
    # ... existing ...
    "motor>=3.3.0",  # Async MongoDB driver
]
```

---

## Phase 3 Implementation (Docker & Azure)

### **Step 13: Dockerization**

**File:** `Dockerfile` (new)

```dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install system dependencies for ta-lib
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install TA-Lib C library
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib/ && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    cd .. && rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# Copy project files
COPY pyproject.toml uv.lock ./
COPY app/ ./app/

# Install Python dependencies
RUN pip install uv
RUN uv pip install --system -r pyproject.toml

# Run application
CMD ["python", "-m", "app.main"]
```

**File:** `docker-compose.yml` (for local testing)

```yaml
version: '3.8'
services:
  analyzer:
    build: .
    environment:
      - MONGODB_URI=mongodb://mongo:27017
      - SMTP_HOST=${SMTP_HOST}
      - SMTP_USER=${SMTP_USER}
      - SMTP_PASSWORD=${SMTP_PASSWORD}
    depends_on:
      - mongo
    volumes:
      - ./logs:/app/logs
      - ./charts:/app/charts
  
  mongo:
    image: mongo:7
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db

volumes:
  mongodb_data:
```

---

### **Step 14: Azure Deployment**

**Resources needed:**

1. **Azure Container Registry** - store Docker images
2. **Azure Container Instances** or **Container Apps** - run containers
3. **Azure Cosmos DB** (MongoDB API) - managed MongoDB
4. **Azure Key Vault** - store secrets
5. **Azure Logic Apps** or **Azure Functions** - scheduling

**File:** `azure-deploy.sh` (deployment script)

```bash
#!/bin/bash
# Build and push Docker image
docker build -t portfolio-analyzer .
docker tag portfolio-analyzer acr.azurecr.io/portfolio-analyzer:latest
docker push acr.azurecr.io/portfolio-analyzer:latest

# Deploy to Azure Container Instances
az container create \
  --resource-group portfolio-rg \
  --name portfolio-analyzer \
  --image acr.azurecr.io/portfolio-analyzer:latest \
  --environment-variables \
    MONGODB_URI=@Microsoft.KeyVault(...) \
  --restart-policy Never
```

**Scheduling:** Azure Logic App triggers container daily at 7:00 AM

---

### **Step 15: Azure Configuration**

**File:** `app/settings.py` (extend)

**Add Azure-specific settings:**

```python
# Azure Key Vault
azure_key_vault_url: Optional[str] = None

# Azure Cosmos DB (MongoDB API)
mongodb_uri: str = Field(default="mongodb://localhost:27017")
mongodb_database: str = "portfolio_analyzer"

# Azure Communication Services (Email)
azure_email_connection_string: Optional[str] = None
```

---

## Phase 4 Implementation (Production Features)

### **Step 16: Email Activation**

**When:** After 2 weeks of successful paper trading validation

**File:** `app/main.py` (uncomment email send)

**Feature flags:** Add to config:

```python
ENABLE_EMAIL = os.getenv('ENABLE_EMAIL', 'false').lower() == 'true'
ENABLE_SMS = os.getenv('ENABLE_SMS', 'false').lower() == 'true'
```

---

### **Step 17: Performance Tracking**

**File:** `app/performance.py` (new)

**Features:**

- Track recommendation accuracy
- Calculate Sharpe ratio of signals
- Compare vs buy-and-hold
- Generate monthly performance report

---

### **Step 18: Web Dashboard**

**Framework:** FastAPI or Streamlit

**Features:**

- View current signals
- Historical performance
- Portfolio composition
- Interactive charts

---

## Development Workflow

### Current Development (Local)

```bash
# Setup
cd portfolio-trend-analyzer
uv sync

# Run analysis
uv run python -m app.main

# Run tests
pytest tests/ -v

# Check code
ruff check app/
```

### With MongoDB (Local)

```bash
# Start MongoDB
docker-compose up -d mongo

# Run with MongoDB
MONGODB_URI=mongodb://localhost:27017 uv run python -m app.main
```

### With Docker (Local)

```bash
# Build and run
docker-compose up --build

# View logs
docker-compose logs -f analyzer
```

### Production (Azure)

```bash
# Deploy
./azure-deploy.sh

# Check logs
az container logs --resource-group portfolio-rg --name portfolio-analyzer

# Monitor
az monitor metrics list ...
```

---

## Success Criteria

### Phase 1 (Algorithm Development) ✅

- [ ] Detects >20% drawdowns reliably
- [ ] <10% false positive rate  
- [ ] >80% true positive rate
- [ ] Analysis completes in <5 minutes
- [ ] Clean logs, no errors
- [ ] High confidence signals are accurate

### Phase 2 (MongoDB Integration)

- [ ] Successfully reads WKNs from MongoDB
- [ ] Correctly identifies owned vs not-owned positions
- [ ] Saves signal history for tracking
- [ ] Smart filtering works (only actionable recommendations)

### Phase 3 (Azure Deployment)

- [ ] Docker container builds successfully
- [ ] Runs reliably on Azure
- [ ] Scheduled execution works daily
- [ ] Secrets managed via Key Vault
- [ ] Zero downtime over 1 month

### Phase 4 (Production)

- [ ] Email delivery >99% reliable
- [ ] Positive ROI vs manual trading
- [ ] User satisfaction with recommendations
- [ ] Performance metrics tracked accurately

---

## Risk Management

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| False signals | High | Multi-indicator confirmation, paper trade first |
| API failures | Medium | Retry logic, fallback data sources |
| MongoDB connection loss | Medium | Local cache, graceful degradation |
| Azure costs | Low | Container only runs for short periods |
| Email not delivered | Medium | Backup: save report to file, SMS alerts |
| Docker build failures | Low | CI/CD pipeline with tests |

---

## Timeline

### Week 1-2: Phase 1 (Current Sprint)

- ✅ Step 1-2: Core algorithm (Day 1-2)
- ✅ Step 3-4: Integration & email (Day 3-4)
- ✅ Step 5-7: Logging, optimization, structure (Day 5)
- ✅ Step 8: Testing & validation (Week 2)

### Week 3-4: Phase 2 (MongoDB)

- Step 9-10: MongoDB schema & integration
- Step 11-12: Smart filtering & configuration
- Testing with real portfolio data

### Month 2: Phase 3 (Docker & Azure)

- Step 13: Dockerization & local testing
- Step 14-15: Azure deployment & configuration
- Production monitoring setup

### Month 3+: Phase 4 (Production Features)

- Email activation (after validation)
- Performance tracking
- Web dashboard
- Continuous optimization

---

## Next Actions

**Immediate (This Session):**

1. ✅ Create this plan document
2. ▶️ Implement Step 1: `app/trend_config.py`
3. ▶️ Implement Step 2: `detect_trend_break()` in `app/analysis.py`
4. ▶️ Quick test with HT8UZB data

**Today:**

- Complete Steps 3-4 (integration & email)
- Step 8: Test with test_depot
- Verify signal quality

**This Week:**

- Steps 5-7: Polish & optimize
- Extended testing & parameter tuning
- Documentation of findings

**Ready to start coding?** ✅
