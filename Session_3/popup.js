document.addEventListener('DOMContentLoaded', function() {
  const currentPriceElement = document.getElementById('currentPrice');
  const queryInput = document.getElementById('query');
  const analyzeButton = document.getElementById('analyze');
  const analysisResult = document.getElementById('analysisResult');
  const telegramPrompt = document.getElementById('telegramPrompt');
  const sendToTelegramButton = document.getElementById('sendToTelegram');
  const statusElement = document.getElementById('status');

  let currentAnalysis = null;

  // Update current price
  function updateCurrentPrice() {
    fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd')
      .then(response => response.json())
      .then(data => {
        const price = data.bitcoin.usd;
        currentPriceElement.textContent = `$${price.toLocaleString()}`;
      })
      .catch(error => {
        currentPriceElement.textContent = 'Error loading price';
        showStatus('Error fetching price', 'error');
      });
  }

  // Show status message
  function showStatus(message, type) {
    statusElement.textContent = message;
    statusElement.className = `status ${type}`;
    statusElement.style.display = 'block';
    setTimeout(() => {
      statusElement.style.display = 'none';
    }, 5000);
  }

  function displayAnalysisResult(result) {
    analysisResult.innerHTML = '';
    const container = document.createElement('div');
    container.className = 'analysis-container';
    container.innerHTML = result;
    analysisResult.appendChild(container);
    analysisResult.style.display = 'block';
    telegramPrompt.style.display = 'block';
    currentAnalysis = result;
    showStatus('Analysis complete!', 'success');
  }

  // Handle analysis request
  analyzeButton.addEventListener('click', async function() {
    const query = queryInput.value.trim();
    
    if (!query) {
      showStatus('Please enter a question about Bitcoin', 'error');
      return;
    }

    showStatus('Analyzing...', 'success');
    analysisResult.style.display = 'none';
    telegramPrompt.style.display = 'none';

    try {
      const response = await chrome.runtime.sendMessage({
        action: 'analyze',
        query: query
      });

      if (!response) {
        showStatus('No response received from analysis', 'error');
        return;
      }

      if (response.error) {
        showStatus(response.error, 'error');
        return;
      }

      if (!response.analysis) {
        showStatus('Invalid analysis response received', 'error');
        return;
      }

      displayAnalysisResult(response.analysis);
    } catch (error) {
      console.error('Analysis error:', error);
      showStatus('Error during analysis: ' + (error.message || 'Unknown error'), 'error');
    }
  });

  // Handle sending to Telegram
  sendToTelegramButton.addEventListener('click', async function() {
    if (!currentAnalysis) {
      showStatus('No analysis available to send', 'error');
      return;
    }

    try {
      showStatus('Sending to Telegram...', 'success');
      
      const response = await chrome.runtime.sendMessage({
        action: 'sendToTelegram',
        message: currentAnalysis
      });

      if (response.error) {
        showStatus(response.error, 'error');
        return;
      }

      if (response.success) {
        showStatus('Analysis sent to Telegram!', 'success');
      } else {
        showStatus('Failed to send to Telegram', 'error');
      }
    } catch (error) {
      showStatus('Error sending to Telegram: ' + error.message, 'error');
    }
  });

  // Initial price update
  updateCurrentPrice();

  // Refresh price every 30 seconds
  const priceUpdateInterval = setInterval(updateCurrentPrice, 30000);

  // Clean up when popup closes
  window.addEventListener('unload', function() {
    clearInterval(priceUpdateInterval);
  });
}); 