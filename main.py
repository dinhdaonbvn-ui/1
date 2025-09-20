from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os, time, threading
import ccxt, asyncio
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Futures Signal App - Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory history store (for demo; production: use Postgres)
HISTORY = []

# Strategy params via env
SYMBOL = os.getenv("SYMBOL", "SOL/USDT")
TIMEFRAME = os.getenv("TIMEFRAME", "1h")
FAST_EMA = int(os.getenv("FAST_EMA", "9"))
SLOW_EMA = int(os.getenv("SLOW_EMA", "21"))

# Exchange init (public data)
EXCHANGE_ID = os.getenv("EXCHANGE", "binance")
def create_exchange():
    exchange_class = getattr(ccxt, EXCHANGE_ID)
    kwargs = {}
    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")
    if api_key and api_secret:
        kwargs['apiKey'] = api_key
        kwargs['secret'] = api_secret
    ex = exchange_class(kwargs)
    # for some exchanges, set options for futures symbols; keep default
    return ex

exchange = create_exchange()

def fetch_price(symbol):
    try:
        # Try fetch ticker (works without API keys)
        t = exchange.fetch_ticker(symbol)
        return float(t['last'])
    except Exception as e:
        raise RuntimeError(f"Failed fetch price: {e}")

# Simple EMA calc on small window using prices from exchange (not full OHLCV history for simplicity)
def simple_ema(prices, span):
    if not prices:
        return None
    k = 2 / (span + 1)
    ema = prices[0]
    for p in prices[1:]:
        ema = p * k + ema * (1 - k)
    return ema

class SignalResponse(BaseModel):
    signal: str
    price: float

@app.get("/api/signal", response_model=SignalResponse)
async def get_signal():
    try:
        price = fetch_price(SYMBOL)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    # For a lightweight approach, fetch recent closes via fetch_ohlcv if available
    try:
        ohlcv = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=max(FAST_EMA, SLOW_EMA)+5)
        closes = [c[4] for c in ohlcv]
    except Exception:
        # fallback: use repeated last price
        closes = [price] * (max(FAST_EMA, SLOW_EMA) + 5)
    fast = simple_ema(closes[-FAST_EMA:], FAST_EMA)
    slow = simple_ema(closes[-SLOW_EMA:], SLOW_EMA)
    signal = "HOLD"
    if fast and slow:
        if fast > slow:
            signal = "LONG"
        elif fast < slow:
            signal = "SHORT"
    rec = {"time": int(time.time()), "symbol": SYMBOL, "price": price, "signal": signal, "fast": fast, "slow": slow}
    HISTORY.insert(0, rec)
    if len(HISTORY) > 500:
        HISTORY.pop()
    return JSONResponse(content={"signal": signal, "price": price})

class DCARequest(BaseModel):
    side: str
    base_price: float = None
    steps: int = 5
    spacing_pct: float = 2.0
    base_usd: float = 5.0

@app.post("/api/dca")
async def dca(req: DCARequest):
    try:
        if req.base_price is None:
            base = fetch_price(SYMBOL)
        else:
            base = req.base_price
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    levels = []
    for i in range(req.steps):
        if req.side.upper() == "LONG":
            price = base * (1 - req.spacing_pct/100 * (i+1))
        else:
            price = base * (1 + req.spacing_pct/100 * (i+1))
        levels.append({"step": i+1, "price": round(price, 8), "usd": req.base_usd})
    return {"base": base, "side": req.side.upper(), "levels": levels}

@app.get("/api/history")
async def history(limit: int = 50):
    return {"history": HISTORY[:limit]}

# Health
@app.get("/")
async def root():
    return {"ok": True, "service": "futures-signal-backend"}
