// Bot Control Panel Configuration

// Update this URL when deploying the backend
const API_BASE_URL = 'https://upbit-krw-bot.railway.app'; // Replace with your Railway/Heroku URL

// Or for local testing:
// const API_BASE_URL = 'http://localhost:5000';

window.CONFIG = {
  API_BASE_URL: API_BASE_URL,
  BOT_API: {
    run: `${API_BASE_URL}/api/run-bot`
  }
};

console.log('[CONFIG] API Base URL:', window.CONFIG.API_BASE_URL);
