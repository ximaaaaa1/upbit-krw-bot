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
    const scriptPath = path.join(__dirname, 'upbit_api.py');
    
    // Execute with timeout
    const result = execSync(`${pythonPath} "${scriptPath}"`, {
      timeout: 180000, // 3 minutes
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'pipe']
    });
    
    // Parse JSON output from Python script
    let botData = {};
    try {
      // Extract JSON from output (last line usually)
      const lines = result.split('\n').filter(l => l.trim());
      const jsonLine = lines[lines.length - 1];
      botData = JSON.parse(jsonLine);
    } catch (e) {
      console.error('[API] Failed to parse bot output:', e.message);
      botData = {
        signals_count: 0,
        results: [],
        error: 'Failed to parse results'
      };
    }
    
    console.log(`[API] Bot completed. Found ${botData.signals_count || 0} signals`);
    
    res.json({
      success: true,
      signals_count: botData.signals_count || 0,
      results: botData.results || [],
      timestamp: botData.timestamp || new Date().toISOString(),
      message: 'Bot executed successfully'
    });
    
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
