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
    const scriptPath = path.join(__dirname, 'upbit_bot_api.py');
    
    // Execute with timeout
    let result = '';
    try {
      result = execSync(`${pythonPath} "${scriptPath}"`, {
        timeout: 300000, // 5 minutes
        encoding: 'utf-8',
        stdio: ['pipe', 'pipe', 'pipe']
      });
    } catch (e) {
      // execSync throws on non-zero exit
      result = e.stdout || '';
      console.error('[API] Script error:', e.stderr || e.message);
    }
    
    // Parse JSON output from Python script
    let botData = { success: false, signals_count: 0, results: [] };
    try {
      // Extract JSON from output
      const jsonMatch = result.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        botData = JSON.parse(jsonMatch[0]);
      }
    } catch (parseErr) {
      console.error('[API] JSON parse error:', parseErr.message);
      console.error('[API] Raw output:', result.substring(0, 500));
    }
    
    console.log(`[API] Bot completed. Found ${botData.signals_count} signals`);
    
    res.json({
      success: botData.success && botData.signals_count > 0,
      signals_count: botData.signals_count || 0,
      results: (botData.results || []).slice(0, 50),  // Top 50
      timestamp: botData.timestamp || new Date().toISOString(),
      message: botData.signals_count > 0 ? 'Bot executed successfully' : 'No anomalies detected'
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
