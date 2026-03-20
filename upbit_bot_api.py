#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Upbit KRW Bot API - Returns JSON results for web UI
Adapted from upbit_mega_fast.py
"""

import requests
import json
import math
from concurrent.futures import ThreadPoolExecutor, as_completed

UPBIT_API = "https://api.upbit.com/v1"
headers = {"Accept": "application/json"}

def analyze(ticker):
    """V5.3 LOGIC: Analyze and score token"""
    try:
        coin = ticker.split("-")[1]
        
        url = f"{UPBIT_API}/candles/minutes/1?market={ticker}&count=1440"
        r = requests.get(url, headers=headers, timeout=3.0)
        
        if r.status_code != 200:
            return None
        
        candles = r.json()
        if not candles or len(candles) < 100:
            return None
        
        volumes = [float(c.get("candle_acc_trade_volume", 0)) for c in candles]
        prices = [float(c.get("trade_price", 0)) for c in candles]
        
        if min(volumes) <= 0 or min(prices) <= 0:
            return None
        
        # Split data in half
        mid = len(volumes) // 2
        past_vol = volumes[mid:]
        recent_vol = volumes[:mid]
        
        past_avg = sum(past_vol) / len(past_vol)
        recent_avg = sum(recent_vol) / len(recent_vol)
        
        vol_ratio = recent_avg / past_avg if past_avg > 0 else 0
        
        price_change = ((prices[0] - prices[-1]) / prices[-1] * 100) if prices[-1] > 0 else 0
        
        # DEAD status
        is_past_dead = past_avg < 500000
        is_recent_active = recent_avg > past_avg * 1.3
        
        status = "💀→💥" if (is_past_dead and is_recent_active) else "⚡" if vol_ratio > 2.0 else "—"
        
        # Score calculation
        dead_spike_bonus = 500 if (is_past_dead and is_recent_active) else 0
        score = (vol_ratio * 100) + dead_spike_bonus
        
        # Trigger
        is_anomaly = (is_past_dead and is_recent_active) or score > 15
        
        if not is_anomaly:
            return None
        
        return {
            'coin': coin,
            'ticker': ticker,
            'vol_ratio': round(vol_ratio, 2),
            'price_change': round(price_change, 2),
            'status': status,
            'score': round(score, 1),
            'is_detected': status == "💀→💥"
        }
    except:
        pass
    
    return None

def get_all_markets():
    """Get all KRW pairs from Upbit"""
    try:
        r = requests.get(f"{UPBIT_API}/market/all?is_details=false", headers=headers, timeout=5)
        markets = r.json()
        krw_pairs = [m['market'] for m in markets if m['market'].startswith('KRW-')]
        return krw_pairs[:170]
    except:
        return []

def scan_all():
    """Scan all tokens and return results"""
    markets = get_all_markets()
    if not markets:
        return []
    
    results = []
    with ThreadPoolExecutor(max_workers=25) as executor:
        futures = {executor.submit(analyze, ticker): ticker for ticker in markets}
        
        for future in as_completed(futures):
            result = future.result()
            if result:
                results.append(result)
    
    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)
    
    return results[:50]  # Top 50

def main():
    """Main entry point"""
    results = scan_all()
    
    output = {
        'success': len(results) > 0,
        'signals_count': len(results),
        'results': results,
        'timestamp': __import__('datetime').datetime.now().isoformat()
    }
    
    # Print JSON
    print(json.dumps(output, ensure_ascii=False))
    return output

if __name__ == "__main__":
    main()
