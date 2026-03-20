import requests
import sys
import io
import concurrent.futures
import json
import csv
import os
import math
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

os.makedirs("upbit_scans", exist_ok=True)

BOT_TOKEN = "8522893493:AAG9L-mPLcNYgA8kyid5hNBAjC3tlK4PYi0"
GROUP_ID_1 = "-1003432880225"
TOPIC_ID_1 = 1390
GROUP_ID_2 = "@upbit_v5_3"
TOPIC_ID_2 = None
GROUP_ID_3 = "@rogdao"
TOPIC_ID_3 = 5971

headers = {"Accept": "application/json"}

def analyze(ticker):
    """V5.3 LOGIC: Compare past volume vs recent volume (adaptive to available data)"""
    try:
        coin = ticker.split("-")[1]
        
        # Get 1440 minutes = 24 hours of 1-min candles
        url = f"https://api.upbit.com/v1/candles/minutes/1?market={ticker}&count=1440"
        r = requests.get(url, headers=headers, timeout=3.0)
        
        if r.status_code != 200:
            return None
        
        candles = r.json()
        if not candles or len(candles) < 100:  # At least 100 candles
            return None
        
        # Extract volumes and prices (candles[0] = newest)
        volumes = [float(c.get("candle_acc_trade_volume", 0)) for c in candles]
        prices = [float(c.get("trade_price", 0)) for c in candles]
        
        if min(volumes) <= 0 or min(prices) <= 0:
            return None
        
        # === V5.3: SPLIT DATA IN HALF (Past vs Recent) ===
        # Works with any amount of data - from 100 to 1440 candles
        
        data_len = len(candles)
        mid = data_len // 2
        
        # RECENT: newer half (0-mid)
        recent = volumes[:mid]
        recent_prices = prices[:mid]
        
        # PAST: older half (mid-end)
        past = volumes[mid:]
        past_prices = prices[mid:]
        
        # Average volumes
        avg_recent = sum(recent) / len(recent) if recent else 0
        avg_past = sum(past) / len(past) if past else 0
        avg_all = sum(volumes) / len(volumes) if volumes else 0
        
        # Current volume (newest candle)
        current_vol = volumes[0]
        
        # === PATTERN DETECTION ===
        
        # Was past DEAD? (low volume in past half)
        dead_threshold = avg_all * 0.5
        was_past_dead = avg_past < dead_threshold
        
        # Is recent ACTIVE? (volume increased significantly)
        is_recent_active = (avg_recent > avg_past * 1.5) or (current_vol > avg_past * 2.5)
        
        # Current spike vs recent average?
        vol_ratio = (current_vol / avg_recent) if avg_recent > 0 else 0
        vol_ratio_vs_past = (current_vol / avg_past) if avg_past > 0 else 0
        
        # === RECENT TREND (last 12 candles) ===
        recent_12 = volumes[:12]
        recent_prices_12 = prices[:12]
        
        acceleration = 1.0
        if len(recent_12) >= 3 and recent_12[0] > recent_12[1] > recent_12[2]:
            acceleration = 2.0
        elif len(recent_12) >= 3 and recent_12[0] > recent_12[1]:
            acceleration = 1.5
        
        # === PRICE CHANGE (1 min) ===
        price_change = ((recent_prices_12[0] - recent_prices_12[1]) / recent_prices_12[1]) * 100 if len(recent_prices_12) > 1 and recent_prices_12[1] > 0 else 0
        
        # === V5.3: BONUSES (Past dead -> Recent spike) ===
        dead_spike_bonus = 0.0
        log_vol = math.log(vol_ratio + 1) if vol_ratio > 0 else 0
        log_vol_past = math.log(vol_ratio_vs_past + 1) if vol_ratio_vs_past > 0 else 0
        
        # KEY PATTERN: Past was DEAD + Recent is ACTIVE = WHALES WAKING UP COIN!
        if was_past_dead and is_recent_active:
            # This is the F-USDT pattern!
            dead_spike_bonus = 500.0 + (log_vol_past * 150) + (vol_ratio_vs_past * 30)
        
        # PATTERN 2: High current spike
        if vol_ratio > 2.0:
            dead_spike_bonus += 200.0 + (log_vol * 80)
        
        # PATTERN 3: Price stable with HIGH volume = accumulation
        if vol_ratio > 2.0 and abs(price_change) < 1.0:
            dead_spike_bonus += 100.0
        
        # PATTERN 4: Extreme volume (>5x)
        if vol_ratio > 5.0:
            dead_spike_bonus += 100.0
        
        # PATTERN 5: Price recovery with volume
        if vol_ratio > 2.0 and price_change >= 0:
            dead_spike_bonus += 50.0
        
        # ===== PATTERN 6: WHALE ACCUMULATION (ADDED 06.03) =====
        # Whales accumulate quietly: DEAD coin + ACTIVE recent + stable price + moderate vol
        if was_past_dead and is_recent_active and 0.3 < vol_ratio < 2.0 and abs(price_change) < 1.0:
            whale_bonus = 400.0 + (vol_ratio_vs_past * 50)
            dead_spike_bonus += whale_bonus
        
        # ===== PATTERN 7: STRONG HISTORICAL SPIKE (ADDED 06.03) =====
        # Even if current volume dropped, vol_ratio_vs_past > 20x = whale activity
        if was_past_dead and vol_ratio_vs_past > 20.0:
            historical_spike_bonus = (vol_ratio_vs_past * 80)
            dead_spike_bonus += historical_spike_bonus
        
        # ===== PATTERN 8: EXTREME HISTORICAL SPIKE (ADDED 06.03) =====
        # vol_ratio_vs_past > 50x = definitely whales (like ANKR 75x)
        if vol_ratio_vs_past > 50.0:
            extreme_whale_bonus = 500.0 + (vol_ratio_vs_past * 100)
            dead_spike_bonus += extreme_whale_bonus
        
        # ===== PATTERN 9: DEAD COIN ACTIVATION (ADDED 06.03) =====
        # Any activation of dead coin deserves bonus
        if was_past_dead and avg_recent > avg_past * 1.2:
            activation_bonus = 200.0
            dead_spike_bonus += activation_bonus
        
        # 4. FINAL SCORE (V5.3 Enhanced)
        base_score = vol_ratio * 100
        score = (base_score * acceleration) + dead_spike_bonus
        
        # 5. TRIGGER: Ultra sensitive (lowered threshold for more signals)
        trigger = (was_past_dead and is_recent_active) or dead_spike_bonus > 15 or vol_ratio > 1.3
        
        # Determine dead status
        dead_status = ""
        if was_past_dead and is_recent_active:
            dead_status = "DEAD->ACTIVE"
        elif was_past_dead:
            dead_status = "DEAD"
        else:
            dead_status = "ACTIVE"
        
        return {
            "coin": coin,
            "pair": ticker,
            "vol_ratio": vol_ratio,
            "price_change": price_change,
            "acceleration": acceleration,
            "dead_spike_bonus": dead_spike_bonus,
            "dead_status": dead_status,
            "score": score,
            "is_anomaly": trigger
        }
    except:
        pass
    
    return None

print("=== UPBIT PUMP PREDICTOR V5.3 (PAST->RECENT: DEAD -> SPIKE) ===\n")

try:
    print("1. Getting all markets...")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    r = requests.get("https://api.upbit.com/v1/market/all", headers=headers, timeout=10)
    markets = r.json()
    
    usdt_tickers = [m["market"] for m in markets if m["market"].startswith("USDT-")]
    krw_tickers = [m["market"] for m in markets if m["market"].startswith("KRW-")]
    
    # *** ТОЛЬКО KRW пары! ***
    all_tickers = krw_tickers
    
    print(f"   USDT pairs: {len(usdt_tickers)} (SKIPPED)")
    print(f"   KRW pairs: {len(krw_tickers)}")
    print(f"   TOTAL: {len(all_tickers)} (KRW only)\n")
    
    print("2. Analyzing (parallel, 600-min data split in half)...")
    all_results = []
    candidates = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
        results = executor.map(analyze, all_tickers)
        for r in results:
            if r:
                all_results.append(r)
                if r["is_anomaly"]:
                    candidates.append(r)
    
    print(f"   Analyzed: {len(all_results)}/338 tokens")
    print(f"   Found {len(candidates)} anomalies\n")
    
    # Sort by score
    all_results.sort(key=lambda x: x["score"], reverse=True)
    candidates.sort(key=lambda x: x["score"], reverse=True)
    
    # Save ALL tokens to CSV
    csv_filename = f"upbit_scans/upbit_all_tokens_{timestamp}.csv"
    with open(csv_filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["pair", "coin", "vol_ratio", "price_change", "acceleration", "dead_spike_bonus", "dead_status", "score", "is_anomaly", "timestamp"])
        writer.writeheader()
        for r in all_results:
            r["timestamp"] = timestamp
            writer.writerow(r)
    print(f"3. Saved all {len(all_results)} tokens to: {csv_filename}")
    
    # Save TOP-50 separately for tracking
    top50_filename = f"upbit_scans/upbit_top50_{timestamp}.csv"
    with open(top50_filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["rank", "pair", "coin", "vol_ratio", "price_change", "acceleration", "dead_spike_bonus", "dead_status", "score", "timestamp"])
        writer.writeheader()
        for idx, r in enumerate(candidates[:50], 1):
            row = {
                "rank": idx,
                "pair": r["pair"],
                "coin": r["coin"],
                "vol_ratio": r["vol_ratio"],
                "price_change": r["price_change"],
                "acceleration": r["acceleration"],
                "dead_spike_bonus": r["dead_spike_bonus"],
                "dead_status": r["dead_status"],
                "score": r["score"],
                "timestamp": timestamp
            }
            writer.writerow(row)
    print(f"   Saved TOP-50 to: {top50_filename}\n")
    
    # Filter: ONLY KRW pairs + blacklist
    blacklist = {"JTO", "HYPER", "SOMI", "TRUMP", "PEPE", "ZRO", "ALT", "SOL", "BLAST", "XRP", "PUMP", "USDE", "RAY", "POL", "MNT", "USDC"}
    candidates_filtered = [c for c in candidates if c["coin"] not in blacklist and c["pair"].startswith("KRW-")]
    print(f"   After blacklist + KRW filter: {len(candidates_filtered)} anomalies\n")
    candidates = candidates_filtered
    
    # Print TOP-50
    print("📊 TOP-50 ANOMALIES (V5.3: PAST DEAD -> RECENT SPIKE):")
    print("-" * 180)
    print(f"{'#':<3} {'Coin':<10} {'Pair':<15} {'Vol':<10} {'Dead':<12} {'Spike':<12} {'Score':<12}")
    print("-" * 180)
    
    for i, c in enumerate(candidates[:50], 1):
        print(f"{i:<3} {c['coin']:<10} {c['pair']:<15} {c['vol_ratio']:>8.2f}x {c['dead_status']:<12} {c['dead_spike_bonus']:>11.1f} {c['score']:>11.1f}")
    
    # Check specific coins (also check all_results if not in filtered candidates)
    print(f"\n🔍 KEY TOKENS:")
    for check_coin in ["F", "DEEP", "CYBER"]:
        found = [c for c in candidates if c["coin"] == check_coin]
        if found:
            idx = candidates.index(found[0]) + 1
            f = found[0]
            print(f"   ✓ {check_coin:<10} #{idx:3d}/{len(candidates)} | {f['pair']:<12} | Vol: {f['vol_ratio']:.2f}x | Dead: {f['dead_status']:<12} | Score: {f['score']:.1f}")
        else:
            # Check in all_results (might be below threshold or blacklisted)
            found_all = [c for c in all_results if c["coin"] == check_coin]
            if found_all:
                f = found_all[0]
                idx = all_results.index(f) + 1
                print(f"   ~ {check_coin:<10} #{idx:3d}/{len(all_results)} (filtered out) | {f['pair']:<12} | Vol: {f['vol_ratio']:.2f}x | Dead: {f['dead_status']:<12} | Score: {f['score']:.1f}")
            else:
                print(f"   ✗ {check_coin:<10} - NOT FOUND IN UPBIT KRW")
    
    if candidates:
        # TOP-30 (сокращён для Telegram - длина сообщения)
        top_50 = candidates[:50]
        best = candidates[0]
        
        msg = "🚀 V5.3 PUMP SIGNALS (KRW ONLY!) - TOP-50:\n"
        for i, c in enumerate(top_50, 1):
            dead_marker = {
                "DEAD->ACTIVE": "💀→💥",
                "DEAD": "💀",
                "ACTIVE": ""
            }[c['dead_status']]
            
            accel_str = "⚡" if c['acceleration'] > 1.5 else ""
            msg += f"{i:3d}. {c['pair']:<12} | Vol: {c['vol_ratio']:>7.1f}x {dead_marker}{accel_str} | Price: {c['price_change']:+6.2f}%\n"
        
        msg += f"\n🎯 ЛУЧШИЙ: {best['pair']}\n"
        msg += f"Vol: {best['vol_ratio']:.2f}x | Dead: {best['dead_status']} | Spike: {best['dead_spike_bonus']:.1f} | Price: {best['price_change']:.2f}%"
        
        print(f"\nMESSAGE:\n{msg}\n")
        
        print("4. Sending to Telegram...")
        
        # Send to GROUP_ID_1
        print("   Sending to GROUP_1 (-1003432880225)...")
        payload1 = {
            "chat_id": GROUP_ID_1,
            "text": msg
        }
        if TOPIC_ID_1:
            payload1["message_thread_id"] = TOPIC_ID_1
        
        r1 = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                         json=payload1, timeout=10)
        
        if r1.json().get("ok"):
            print("✅ SENT to GROUP_1!")
        else:
            print(f"❌ ERROR GROUP_1: {r1.json()}")
        
        # Send to GROUP_ID_2
        print("   Sending to GROUP_2 (@upbit_v5_3)...")
        payload2 = {
            "chat_id": GROUP_ID_2,
            "text": msg
        }
        if TOPIC_ID_2:
            payload2["message_thread_id"] = TOPIC_ID_2
        
        r2 = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                         json=payload2, timeout=10)
        
        if r2.json().get("ok"):
            print("✅ SENT to GROUP_2!")
        else:
            print(f"❌ ERROR GROUP_2: {r2.json()}")
        
        # Send to GROUP_ID_3
        print("   Sending to GROUP_3 (@rogdao/5971)...")
        payload3 = {
            "chat_id": GROUP_ID_3,
            "text": msg
        }
        if TOPIC_ID_3:
            payload3["message_thread_id"] = TOPIC_ID_3
        
        r3 = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                         json=payload3, timeout=10)
        
        if r3.json().get("ok"):
            print("✅ SENT to GROUP_3!")
        else:
            print(f"❌ ERROR GROUP_3: {r3.json()}")
    else:
        print("❌ NO ANOMALIES FOUND")

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
