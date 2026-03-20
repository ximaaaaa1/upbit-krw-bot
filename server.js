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

// V5.5 Daily Volume Analysis
app.post('/api/analyze', (req, res) => {
  // Set longer timeout for this endpoint
  req.socket.setTimeout(300000);  // 5 minutes
  
  console.log(`[API] V5.5 Daily Volume Analysis started at ${new Date().toISOString()}`);
  
  try {
    const pythonPath = 'python3' || 'python';
    const scriptPath = path.join(__dirname, 'upbit_v5_5_api.py');
    
    // Check if script exists
    if (!fs.existsSync(scriptPath)) {
      return res.status(500).json({
        success: false,
        error: 'V5.5 script not found',
        results: []
      });
    }
    
    let result = '';
    try {
      result = execSync(`${pythonPath} "${scriptPath}"`, {
        timeout: 240000, // 4 minutes max
        encoding: 'utf-8',
        stdio: ['pipe', 'pipe', 'pipe'],
        maxBuffer: 10 * 1024 * 1024  // 10MB buffer for large outputs
      });
    } catch (e) {
      result = e.stdout || '';
      console.error('[API] V5.5 error:', e.stderr || e.message);
    }
    
    let v55Data = { success: false, signals_count: 0, results: [] };
    try {
      const jsonMatch = result.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        v55Data = JSON.parse(jsonMatch[0]);
      }
    } catch (parseErr) {
      console.error('[API] V5.5 parse error:', parseErr.message);
    }
    
    console.log(`[API] V5.5 completed. Found ${v55Data.signals_count} anomalies`);
    
    res.json({
      success: v55Data.success && v55Data.signals_count > 0,
      signals_count: v55Data.signals_count || 0,
      results: (v55Data.results || []).slice(0, 30),  // Top 30
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('[API] V5.5 error:', error.message);
    
    res.json({
      success: false,
      error: error.message || 'V5.5 analysis failed',
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
