#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Upbit KRW Bot API - Returns JSON results instead of sending to Telegram
"""

import requests
import json
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

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
        
        # Score
        dead_spike_bonus = 500 if (is_past_dead and is_recent_active) else 0
        divergence_bonus = abs(price_change) * 2 if price_change < 0 else 0
        score = (vol_ratio * 100) + dead_spike_bonus + divergence_bonus
        
        return {
            'coin': coin,
            'ticker': ticker,
            'vol_ratio': round(vol_ratio, 2),
            'vol_recent': f"${recent_avg:,.0f}",
            'vol_past': f"${past_avg:,.0f}",
            'price_change': f"{price_change:+.2f}%",
            'status': status,
            'score': round(score, 1)
        }
    except Exception as e:
        return None

def get_all_markets():
    """Get all KRW pairs from Upbit"""
    try:
        r = requests.get(f"{UPBIT_API}/market/all?is_details=false", headers=headers, timeout=5)
        markets = r.json()
        krw_pairs = [m['market'] for m in markets if m['market'].startswith('KRW-')]
        return krw_pairs[:170]  # Top 170
    except:
        return []

def scan_all():
    """Scan all tokens and return results"""
    print("[*] Starting scan...", flush=True)
    
    markets = get_all_markets()
    if not markets:
        print("[!] No markets found", flush=True)
        return []
    
    print(f"[*] Found {len(markets)} KRW pairs", flush=True)
    
    results = []
    with ThreadPoolExecutor(max_workers=25) as executor:
        futures = {executor.submit(analyze, ticker): ticker for ticker in markets}
        
        completed = 0
        for future in as_completed(futures):
            completed += 1
            result = future.result()
            if result:
                results.append(result)
            
            if completed % 20 == 0:
                print(f"[*] Scanned {completed}/{len(markets)}", flush=True)
    
    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"[+] Found {len(results)} anomalies", flush=True)
    
    return results[:30]  # Top 30

def main():
    """Main entry point"""
    results = scan_all()
    
    output = {
        'timestamp': datetime.now().isoformat(),
        'signals_count': len(results),
        'results': results
    }
    
    # Print JSON for API to parse
    print(json.dumps(output, ensure_ascii=False), flush=True)
    
    return output

if __name__ == "__main__":
    main()
