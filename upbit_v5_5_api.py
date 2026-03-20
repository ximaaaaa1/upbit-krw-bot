#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V5.5 API - Daily Volume Analysis (JSON output)
Анализирует дневные объемы и выдает JSON для веб-сайта
"""
import requests
import json
import sys
import io
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

headers = {"Accept": "application/json"}
MAX_WORKERS = 20

def get_daily_volumes(ticker):
    """Получить объём за вчера и сегодня (дневные свечи)"""
    try:
        url = f"https://api.upbit.com/v1/candles/days?market={ticker}&count=2"
        r = requests.get(url, headers=headers, timeout=3.0)
        
        if r.status_code != 200:
            return None
        
        candles = r.json()
        if not candles or len(candles) < 2:
            return None
        
        # candles[0] = сегодня, candles[1] = вчера
        today = candles[0]
        yesterday = candles[1]
        
        today_vol = float(today.get("candle_acc_trade_volume", 0))
        yesterday_vol = float(yesterday.get("candle_acc_trade_volume", 0))
        today_price = float(today.get("trade_price", 0))
        
        if yesterday_vol <= 0 or today_vol <= 0:
            return None
        
        volume_ratio = today_vol / yesterday_vol
        growth_pct = (volume_ratio - 1) * 100
        
        return {
            "today_volume": today_vol,
            "yesterday_volume": yesterday_vol,
            "volume_ratio": volume_ratio,
            "growth_pct": growth_pct,
            "price": today_price
        }
    except Exception as e:
        return None

def analyze_ticker(ticker):
    """Анализ пары"""
    try:
        coin = ticker.split("-")[1]
        data = get_daily_volumes(ticker)
        
        if not data:
            return None
        
        return {
            "coin": coin,
            "ticker": ticker,
            "price": int(data["price"]),
            "today_volume": int(data["today_volume"]),
            "yesterday_volume": int(data["yesterday_volume"]),
            "volume_ratio": round(data["volume_ratio"], 2),
            "growth_pct": round(data["growth_pct"], 1)
        }
    except:
        return None

def get_krw_markets():
    """Получить все KRW пары"""
    try:
        url = "https://api.upbit.com/v1/market/all"
        r = requests.get(url, headers=headers, timeout=5)
        
        if r.status_code != 200:
            return []
        
        markets = r.json()
        krw_markets = [m['market'] for m in markets if m['market'].startswith('KRW-')]
        return krw_markets
    except:
        return []

def main():
    print("[*] V5.5 API - Daily Volume Analysis", file=sys.stderr)
    
    # Получить все KRW пары
    markets = get_krw_markets()
    print(f"[+] Found {len(markets)} KRW markets", file=sys.stderr)
    
    if not markets:
        print(json.dumps({"success": False, "error": "No markets found", "results": []}))
        return
    
    results = []
    
    # Анализируем параллельно
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(analyze_ticker, ticker): ticker for ticker in markets}
        completed = 0
        
        for future in as_completed(futures):
            completed += 1
            if completed % 50 == 0:
                print(f"[*] Analyzed {completed}/{len(markets)}...", file=sys.stderr)
            
            result = future.result()
            if result:
                results.append(result)
    
    # Фильтруем - только токены где волюм выросли (ratio > 1.0)
    growth_only = [r for r in results if r["volume_ratio"] > 1.0]
    
    # Сортируем по vol_ratio (от большего к меньшему)
    growth_only.sort(key=lambda x: x["volume_ratio"], reverse=True)
    
    # TOP-30 с ростом волюма
    top_results = growth_only[:30]
    
    print(f"[+] Found {len(top_results)} anomalies", file=sys.stderr)
    
    # Выводим JSON
    output = {
        "success": True,
        "timestamp": None,
        "signals_count": len(top_results),
        "results": top_results
    }
    
    print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
