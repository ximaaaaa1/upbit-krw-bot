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
    """Анализ пары с фильтрами"""
    try:
        coin = ticker.split("-")[1]
        data = get_daily_volumes(ticker)
        
        if not data:
            return None
        
        price = data["price"]
        yesterday_vol = data["yesterday_volume"]
        today_vol = data["today_volume"]
        ratio = data["volume_ratio"]
        
        # ФИЛЬТРЫ для качественных сигналов:
        
        # 1. Исключить копейчные токены (< 1 KRW)
        if price < 1:
            return None
        
        # 2. Исключить микро-ликвидность (вчерашний vol < 100k)
        if yesterday_vol < 100000:
            return None
        
        # 3. Только токены с ростом волюма (ratio > 1.0)
        if ratio <= 1.0:
            return None
        
        # 4. Исключить экстремальные спайки (> 50x) - скорее всего делистинг/баг
        if ratio > 50:
            return None
        
        return {
            "coin": coin,
            "ticker": ticker,
            "price": int(price),
            "today_volume": int(today_vol),
            "yesterday_volume": int(yesterday_vol),
            "volume_ratio": round(ratio, 2),
            "growth_pct": round(data["growth_pct"], 1),
            "quality_score": round(ratio * (today_vol / yesterday_vol), 2)  # Итоговый скор
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
    
    # Результаты уже отфильтрованы в analyze_ticker()
    # Сортируем по quality_score (от большего к меньшему)
    results.sort(key=lambda x: x.get("quality_score", x["volume_ratio"]), reverse=True)
    
    # TOP-30
    top_results = results[:30]
    
    # Статистика
    total_analyzed = len(markets)
    total_growth = len(results)
    growth_pct = (total_growth / total_analyzed * 100) if total_analyzed > 0 else 0
    
    print(f"[+] Analyzed: {total_analyzed} | Growth: {total_growth} | Percentage: {growth_pct:.1f}%", file=sys.stderr)
    print(f"[+] TOP tokens (by ratio):", file=sys.stderr)
    for i, r in enumerate(top_results[:5], 1):
        print(f"  {i}. {r['coin']} {r['volume_ratio']:.2f}x (+{r['growth_pct']:.1f}%)", file=sys.stderr)
    
    # Выводим JSON с статистикой
    output = {
        "success": True,
        "timestamp": None,
        "signals_count": len(top_results),
        "stats": {
            "total_analyzed": total_analyzed,
            "tokens_with_growth": total_growth,
            "growth_percentage": round(growth_pct, 1),
            "avg_ratio": round(sum(r["volume_ratio"] for r in top_results) / len(top_results) if top_results else 0, 2),
            "best_token": f"{top_results[0]['coin']} ({top_results[0]['volume_ratio']:.2f}x)" if top_results else "N/A"
        },
        "results": top_results
    }
    
    print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
