const express = require('express');
const { execSync, spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 5000;

// CORS middleware
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE');
  res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  if (req.method === 'OPTIONS') {
    return res.sendStatus(200);
  }
  next();
});

app.use(express.json());
app.use(express.static(__dirname));

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Run bot
app.post('/api/run-bot', (req, res) => {
  const { bot_type } = req.body;
  
  console.log(`[API] Starting bot: ${bot_type}`);
  
  try {
    const pythonPath = 'python3' || 'python';
    const scriptPath = path.join(__dirname, 'upbit_mega_fast.py');
    
    // Execute with timeout
    let result = '';
    try {
      result = execSync(`${pythonPath} "${scriptPath}"`, {
        timeout: 300000, // 5 minutes
        encoding: 'utf-8',
        stdio: ['pipe', 'pipe', 'pipe'],
        cwd: path.join(__dirname, '..')
      });
    } catch (e) {
      // execSync throws on non-zero exit
      result = e.stdout || '';
      console.error('[API] Script error output:', e.stderr || '');
    }
    
    // Parse results from output
    let botResults = [];
    try {
      // Look for "=== RESULTS ===" section
      const lines = result.split('\n');
      const resultLines = [];
      let inResults = false;
      
      for (const line of lines) {
        if (line.includes('== RESULTS ==') || line.includes('== TOP')) {
          inResults = true;
          continue;
        }
        if (inResults && line.trim().startsWith('1.')) {
          // Parse table rows like: "1. USDT-ALT | Vol: 30.99x..."
          const match = line.match(/\d+\.\s+([A-Z0-9]+)[^|]*\|\s*Vol:\s*([\d.]+)x[^|]*\|\s*([^|]+)\|\s*Price:\s*([^\n]+)/);
          if (match) {
            botResults.push({
              coin: match[1],
              vol_ratio: parseFloat(match[2]),
              status: match[3].trim(),
              price_change: match[4].trim()
            });
          }
        }
      }
      
      // If no table found, try to count anomalies from output
      const anomalyMatch = result.match(/Found (\d+) anomalies/i);
      const signalCount = anomalyMatch ? parseInt(anomalyMatch[1]) : botResults.length;
      
      console.log(`[API] Bot completed. Found ${signalCount} signals`);
      
      res.json({
        success: true,
        signals_count: signalCount,
        results: botResults.slice(0, 30),
        timestamp: new Date().toISOString(),
        message: 'Bot executed successfully'
      });
      
    } catch (parseErr) {
      console.error('[API] Parse error:', parseErr.message);
      res.json({
        success: true,
        signals_count: 0,
        results: [],
        timestamp: new Date().toISOString(),
        message: 'Bot completed but failed to parse results',
        raw_output: result.substring(0, 500)
      });
    }
    
  } catch (error) {
    console.error('[API] Bot error:', error.message);
    
    res.json({
      success: false,
      error: error.message || 'Bot execution failed',
      signals_count: 0,
      results: []
    });
  }
});

// Serve index.html for any other routes
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, () => {
  console.log(`🚀 UPBIT KRW Bot Control Panel running on http://localhost:${PORT}`);
  console.log(`📡 API endpoint: POST /api/run-bot`);
});
