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
    const pythonPath = 'python';
    const scriptPath = 'C:\\Users\\Administrator\\.openclaw\\workspace\\upbit_mega_fast.py';
    
    // Execute with timeout
    const result = execSync(`${pythonPath} "${scriptPath}"`, {
      timeout: 180000, // 3 minutes
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'pipe']
    });
    
    // Parse output for signal count
    const signalMatch = result.match(/Sent (\d+) clean reports/);
    const signalCount = signalMatch ? parseInt(signalMatch[1]) : 0;
    
    console.log(`[API] Bot completed. Found ${signalCount} signals`);
    
    res.json({
      success: true,
      signals_count: signalCount,
      message: 'Bot executed successfully'
    });
    
  } catch (error) {
    console.error('[API] Bot error:', error.message);
    
    res.json({
      success: false,
      error: error.message || 'Bot execution failed',
      signals_count: 0
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
