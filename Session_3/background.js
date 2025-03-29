// Configuration
const TELEGRAM_BOT_TOKEN = "7551031759:AAFRBljn3nvmxcCIB6_7EdWQ8WJMewn5z7E";
const TELEGRAM_CHAT_ID = "1011367949";
const GEMINI_API_KEY = "AIzaSyAizctfr0NvoU0ZE-DgQWr6ndBau1OCz7g";

// Store conversation history
let conversationHistory = [];

// Handle messages from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  switch (message.action) {
    case 'analyze':
      handleAnalysis(message.query, sendResponse);
      return true; // Required for async response
    case 'sendToTelegram':
      handleSendToTelegram(message.message, sendResponse);
      return true; // Required for async response
    case 'getCurrentPrice':
      getBitcoinPrice()
        .then(price => sendResponse({ price }))
        .catch(error => sendResponse({ error: error.message }));
      return true; // Required for async response
  }
});

// Helper function for logging
function logStep(stepName, details = "") {
  const separator = "=".repeat(30);
  console.log(`\n${separator}\nSTEP: ${stepName}\n${separator}`);
  if (details) console.log(details);
}

function logAgent(agentName, action, data = "") {
  const separator = "-".repeat(30);
  console.log(`\n${separator}\nAGENT: ${agentName}\n${separator}`);
  console.log(`Action: ${action}`);
  if (data) console.log("Data:", data);
}

function logAPI(apiName, endpoint, params = "") {
  const separator = "*".repeat(30);
  console.log(`\n${separator}\nAPI CALL: ${apiName}\n${separator}`);
  console.log(`Endpoint: ${endpoint}`);
  if (params) console.log("Parameters:", params);
}

// Helper function to call Gemini API with retry logic
async function callGemini(prompt, retries = 3) {
  for (let attempt = 0; attempt < retries; attempt++) {
    try {
      console.log(`Calling Gemini API (attempt ${attempt + 1}/${retries})...`);
      
      const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${GEMINI_API_KEY}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          contents: [{
            parts: [{
              text: prompt
            }]
          }],
          generationConfig: {
            temperature: 0.3,
            topK: 20,
            topP: 0.8,
            maxOutputTokens: 2048
          },
          safetySettings: [
            {
              category: "HARM_CATEGORY_HARASSMENT",
              threshold: "BLOCK_NONE"
            },
            {
              category: "HARM_CATEGORY_HATE_SPEECH",
              threshold: "BLOCK_NONE"
            },
            {
              category: "HARM_CATEGORY_SEXUALLY_EXPLICIT",
              threshold: "BLOCK_NONE"
            },
            {
              category: "HARM_CATEGORY_DANGEROUS_CONTENT",
              threshold: "BLOCK_NONE"
            }
          ]
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error('Gemini API Error Response:', errorData);
        throw new Error(`Gemini API error: ${response.status} - ${errorData.error?.message || 'Unknown error'}`);
      }

      const data = await response.json();
      console.log('Gemini API Response:', data);

      if (!data.candidates?.[0]?.content?.parts?.[0]?.text) {
        console.error('Invalid Gemini Response Format:', data);
        throw new Error('Invalid response format from Gemini API');
      }

      console.log('Successfully received Gemini API response');
      return data.candidates[0].content.parts[0].text;
      
    } catch (error) {
      console.error(`Error calling Gemini API (attempt ${attempt + 1}):`, error);
      
      if (attempt === retries - 1) {
        throw new Error(`Failed to get response from Gemini API after ${retries} attempts: ${error.toString()}`);
      }
      
      // Wait before retrying with exponential backoff
      const waitTime = Math.pow(2, attempt) * 1000;
      console.log(`Waiting ${waitTime}ms before retry...`);
      await sleep(waitTime);
    }
  }
  throw new Error('Failed to get response from Gemini API after all retries');
}

// Helper function to format news data
function formatNewsData(news) {
  if (!news || news.length === 0) {
    return "No recent trending data available.";
  }
  
  return news.map(item => 
    `Title: ${item.title}\nSource: ${item.source}\nURL: ${item.url}`
  ).join('\n\n');
}

// Step 1: Market Data Analysis Agent
async function getMarketAnalysis(query, marketData) {
  const prompt = `
You are Agent 1 - The Market Analysis Agent.
Analyze the user's query type and market data to provide appropriate analysis.

Market Data:
${marketData}

User Query: ${query}

Previous Context:
${conversationHistory.map(item => `${item.role}: ${item.content}`).join('\n')}

IMPORTANT: First, identify if this is a Yes/No question or an open-ended analysis question.
If it's a Yes/No question, focus on factors that directly influence the answer.
If it's an open-ended question, provide comprehensive analysis.

For Yes/No questions, format as:
QUESTION TYPE: Yes/No
DIRECT FACTORS:
- [Factor 1]: [Direct impact on Yes/No decision]
- [Factor 2]: [Direct impact on Yes/No decision]

For open-ended questions, format as:
QUESTION TYPE: Open Analysis
MARKET ASSESSMENT:
[Your detailed market assessment]

In both cases, also provide:
REQUESTED INDICATORS:
- [Indicator 1]: [Why we need this]
- [Indicator 2]: [Why we need this]

NEWS FOCUS AREAS:
- [Category 1]: [Why this matters]
- [Category 2]: [Why this matters]`;

  const response = await callGemini(prompt);
  conversationHistory.push({ 
    role: "market_agent", 
    content: response,
    timestamp: new Date().toISOString(),
    data_analyzed: marketData
  });
  return response;
}

// Step 2: Technical Analysis Agent
async function getTechnicalAnalysis(marketAnalysis, technicalData) {
  const prompt = `
You are Agent 2 - The Technical Analysis Agent.
Review the previous agent's analysis and new technical data.

Previous Market Analysis:
${marketAnalysis}

Technical Data:
${technicalData}

Full Conversation History:
${conversationHistory.map(item => `[${item.role} at ${item.timestamp}]: ${item.content}`).join('\n')}

Your tasks:
1. Validate or challenge Market Agent's observations
2. Analyze technical indicators
3. Specify what news events would be most relevant

Format your response as:
TECHNICAL ASSESSMENT:
[Your detailed technical analysis]

MARKET ANALYSIS VALIDATION:
[Agree/disagree with specific points from Market Agent]

NEWS REQUIREMENTS:
[Specific news types that could confirm/reject this analysis]`;

  const response = await callGemini(prompt);
  conversationHistory.push({ 
    role: "technical_agent", 
    content: response,
    timestamp: new Date().toISOString(),
    data_analyzed: technicalData
  });
  return response;
}

// Step 3: News Analysis Agent
async function getNewsAnalysis(technicalAnalysis, news) {
  const prompt = `
You are Agent 3 - The News Analysis Agent.
Analyze news impact based on previous agents' findings.

Previous Technical Analysis:
${technicalAnalysis}

News Data:
${formatNewsData(news)}

Full Conversation History:
${conversationHistory.map(item => `[${item.role} at ${item.timestamp}]: ${item.content}`).join('\n')}

Your tasks:
1. Find correlations between news and technical patterns
2. Validate or challenge previous agents' conclusions
3. Identify potential market catalysts

Format your response as:
NEWS IMPACT ANALYSIS:
[Your detailed news analysis]

CORRELATION WITH TECHNICAL ANALYSIS:
[How news confirms/contradicts technical patterns]

POTENTIAL CATALYSTS:
[Specific events that could trigger price movements]`;

  const response = await callGemini(prompt);
  conversationHistory.push({ 
    role: "news_agent", 
    content: response,
    timestamp: new Date().toISOString(),
    data_analyzed: JSON.stringify(news)
  });
  return response;
}

// Step 4: Final Synthesis Agent
async function getFinalSynthesis(marketAnalysis, technicalAnalysis, newsAnalysis) {
  const prompt = `
You are Agent 4 - The Synthesis Agent.
Your task is to synthesize all analyses into a clear, question-appropriate response.

Full Analysis History:
${conversationHistory.map(item => `[${item.role} at ${item.timestamp}]:\n${item.content}\nData Analyzed: ${item.data_analyzed}\n---`).join('\n')}

Check the original question type from Market Agent's analysis.
For Yes/No questions:
1. Start with a clear YES or NO answer
2. Follow with brief, focused justification
3. List key factors that led to this decision

For open-ended questions:
1. Synthesize all agents' findings
2. Identify conflicts in analyses
3. Provide comprehensive recommendation

Format for Yes/No questions:
ANSWER: [YES/NO]
KEY REASONS:
1. [Main reason]
2. [Secondary reason]
3. [Additional factor]

SUPPORTING EVIDENCE:
[Brief summary of technical and news factors]

Format for open-ended questions:
SYNTHESIS OF FINDINGS:
[Summary of key points]

CONFLICTS AND RESOLUTIONS:
[How you resolved conflicting viewpoints]

FINAL RECOMMENDATION:
[Clear, actionable recommendation]

MONITORING POINTS:
[Specific things to watch]`;

  const response = await callGemini(prompt);
  conversationHistory.push({ 
    role: "synthesis_agent", 
    content: response,
    timestamp: new Date().toISOString()
  });
  return response;
}

// Updated main analysis handler
async function handleAnalysis(query, sendResponse) {
  try {
    logStep("Analysis Started", `Query: ${query}`);
    
    // Reset conversation history for new analysis
    conversationHistory = [];
    conversationHistory.push({ 
      role: "user", 
      content: query,
      timestamp: new Date().toISOString()
    });
    
    // Step 1: Collect Market Data
    logStep("Market Data Collection");
    const currentPrice = await getBitcoinPrice();
    const historicalData = await getHistoricalData();
    const marketData = formatMarketData(currentPrice, historicalData);
    
    // Step 2: Market Analysis
    logAgent("Market Analysis Agent", "Initial Market Assessment");
    const marketAnalysis = await getMarketAnalysis(query, marketData);
    
    // Step 3: Technical Analysis
    logAgent("Technical Analysis Agent", "Technical Pattern Analysis");
    const technicalData = await getHistoricalData(); // Get fresh data
    const technicalAnalysis = await getTechnicalAnalysis(marketAnalysis, technicalData);
    
    // Step 4: News Analysis
    logAgent("News Analysis Agent", "News Impact Assessment");
    const news = await getRecentNews();
    const newsAnalysis = await getNewsAnalysis(technicalAnalysis, news);
    
    // Step 5: Final Synthesis
    logAgent("Synthesis Agent", "Final Recommendation");
    const finalSynthesis = await getFinalSynthesis(
      marketAnalysis,
      technicalAnalysis,
      newsAnalysis
    );
    
    // Format and send response
    logStep("Formatting Response");
    const formattedAnalysis = formatResponse(finalSynthesis);
    
    logStep("Analysis Complete", "All agents have completed their sequential analysis");
    sendResponse({ analysis: formattedAnalysis });
    
  } catch (error) {
    console.error('Error in analysis:', error);
    sendResponse({ 
      error: 'Failed to perform analysis',
      details: error.message
    });
  }
}

// Helper function to format market data
function formatMarketData(currentPrice, historicalData) {
  let priceChange = 'N/A';
  let marketCap = 'N/A';
  let volume = 'N/A';

  try {
    if (historicalData.prices.length >= 2) {
      const current = historicalData.prices[historicalData.prices.length - 1][1];
      const previous = historicalData.prices[historicalData.prices.length - 2][1];
      priceChange = ((current - previous) / previous * 100).toFixed(2);
    }

    if (historicalData.market_caps?.length > 0) {
      marketCap = historicalData.market_caps[historicalData.market_caps.length - 1][1];
    }
    
    if (historicalData.total_volumes?.length > 0) {
      volume = historicalData.total_volumes[historicalData.total_volumes.length - 1][1];
    }
  } catch (error) {
    console.error('Error formatting market data:', error);
  }

  return [
    'Current Market Data:',
    `• Price: $${currentPrice.toLocaleString()}`,
    `• 24h Change: ${priceChange}%`,
    `• Market Cap: ${marketCap !== 'N/A' ? `$${marketCap.toLocaleString()}` : 'N/A'}`,
    `• 24h Volume: ${volume !== 'N/A' ? `$${volume.toLocaleString()}` : 'N/A'}`
  ].join('\n');
}

// Helper function to format the final response
function formatResponse(analysis) {
  // Common formatting function for sections
  const formatSection = (text) => {
    const lines = text.split('\n');
    const formattedLines = [];
    let currentSection = null;
    let inList = false;
    
    for (const line of lines) {
      const trimmedLine = line.trim();
      
      // Check if this is a section header
      if (trimmedLine === trimmedLine.toUpperCase() && trimmedLine.endsWith(':')) {
        // Close previous list if exists
        if (inList) {
          formattedLines.push('</ul>');
          inList = false;
        }
        // Add new section header
        const headerText = trimmedLine.slice(0, -1); // Remove the colon
        formattedLines.push(`<div class="section-header">${headerText}</div>`);
      } else if (trimmedLine.startsWith('•') || trimmedLine.startsWith('-')) {
        // Start list if not already in one
        if (!inList) {
          formattedLines.push('<ul class="bullet-list">');
          inList = true;
        }
        // Add list item
        const itemText = trimmedLine.replace(/^[•-]\s*/, '').trim();
        formattedLines.push(`<li>${itemText}</li>`);
      } else if (trimmedLine) {
        // Close list if exists
        if (inList) {
          formattedLines.push('</ul>');
          inList = false;
        }
        // Regular content
        formattedLines.push(`<p class="content">${trimmedLine}</p>`);
      }
    }
    
    // Close any open list
    if (inList) {
      formattedLines.push('</ul>');
    }
    
    return formattedLines.join('\n');
  };

  // Add emojis to section headers
  const addEmojis = (text) => {
    const emojiMap = {
      'ANSWER': '▶️',
      'KEY REASONS': '📝',
      'SUPPORTING EVIDENCE': '📊',
      'MARKET ASSESSMENT': '📈',
      'TECHNICAL ANALYSIS': '📊',
      'NEWS IMPACT': '📰',
      'SYNTHESIS': '💡',
      'CONFLICTS AND RESOLUTIONS': '⚖️',
      'RECOMMENDATION': '✅',
      'MONITORING POINTS': '👀',
      'SUMMARY': '📋',
      'RISK FACTORS': '⚠️'
    };

    return text.replace(/<div class="section-header">([^<]+)<\/div>/g, (match, header) => {
      const emoji = emojiMap[header] || '';
      return `<div class="section-header">${emoji} ${header}</div>`;
    });
  };

  // Create the HTML structure
  const createHTML = (text, title) => {
    const styles = `
      <style>
        .analysis-container {
          font-family: Arial, sans-serif;
          max-width: 800px;
          margin: 0 auto;
          padding: 20px;
          background: #f8f9fa;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .title {
          text-align: center;
          font-size: 24px;
          font-weight: bold;
          color: #2c3e50;
          padding: 15px;
          margin-bottom: 20px;
          border-bottom: 2px solid #3498db;
        }
        .section-header {
          font-size: 18px;
          font-weight: bold;
          color: #2c3e50;
          margin: 20px 0 10px 0;
          padding: 8px;
          background: #e9ecef;
          border-radius: 4px;
        }
        .bullet-list {
          list-style-type: none;
          padding-left: 20px;
          margin: 10px 0;
        }
        .bullet-list li {
          position: relative;
          padding: 5px 0 5px 25px;
          line-height: 1.5;
        }
        .bullet-list li:before {
          content: "•";
          position: absolute;
          left: 0;
          color: #3498db;
          font-weight: bold;
        }
        .content {
          line-height: 1.6;
          color: #34495e;
          margin: 10px 0;
          padding: 0 10px;
        }
        .separator {
          border-top: 1px solid #dee2e6;
          margin: 20px 0;
        }
      </style>
    `;

    return `
      ${styles}
      <div class="analysis-container">
        <div class="title">${title}</div>
        ${text}
        <div class="separator"></div>
      </div>
    `;
  };

  // Format the analysis text
  let formattedText = formatSection(analysis);
  formattedText = addEmojis(formattedText);

  // Choose title based on content
  const title = analysis.includes('ANSWER:') ? 
    'Bitcoin Decision Helper' : 
    'Bitcoin Market Analysis';

  return createHTML(formattedText, title);
}

// Handle sending to Telegram
async function handleSendToTelegram(message, sendResponse) {
  try {
    await sendTelegramMessage(message);
    sendResponse({ success: true });
  } catch (error) {
    console.error('Error sending to Telegram:', error);
    sendResponse({ error: error.message });
  }
}

// Helper function for exponential backoff
async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Get current Bitcoin price with retry logic
async function getBitcoinPrice(retries = 3) {
  for (let attempt = 0; attempt < retries; attempt++) {
    try {
      console.log(`Attempting to fetch Bitcoin price (attempt ${attempt + 1}/${retries})...`);
      const response = await fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd');
      
      if (response.status === 429) {
        // Rate limit hit - wait with exponential backoff
        const waitTime = Math.pow(2, attempt) * 1000; // 1s, 2s, 4s
        console.log(`Rate limit hit, waiting ${waitTime}ms before retry...`);
        await sleep(waitTime);
        continue;
      }
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error(`CoinGecko API error (attempt ${attempt + 1}):`, {
          status: response.status,
          statusText: response.statusText,
          body: errorText
        });
        throw new Error(`CoinGecko API error: ${response.status} - ${response.statusText} - ${errorText}`);
      }
      
      const data = await response.json();
      if (!data.bitcoin?.usd) {
        throw new Error('Invalid response format from CoinGecko API');
      }
      
      console.log(`Successfully fetched Bitcoin price: $${data.bitcoin.usd}`);
      return data.bitcoin.usd;
    } catch (error) {
      console.error(`Error fetching Bitcoin price (attempt ${attempt + 1}):`, error.toString(), error);
      if (attempt === retries - 1) {
        throw new Error(`Failed to fetch Bitcoin price after ${retries} attempts: ${error.toString()}`);
      }
      // Wait before retrying with exponential backoff
      const waitTime = Math.pow(2, attempt) * 1000;
      console.log(`Waiting ${waitTime}ms before retry...`);
      await sleep(waitTime);
    }
  }
  throw new Error('Failed to fetch Bitcoin price after all retries');
}

// Get historical data with retry logic
async function getHistoricalData(retries = 3) {
  for (let attempt = 0; attempt < retries; attempt++) {
    try {
      console.log(`Attempting to fetch historical data (attempt ${attempt + 1}/${retries})...`);
      const response = await fetch('https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=1');
      
      if (response.status === 429) {
        // Rate limit hit - wait with exponential backoff
        const waitTime = Math.pow(2, attempt) * 1000; // 1s, 2s, 4s
        console.log(`Rate limit hit, waiting ${waitTime}ms before retry...`);
        await sleep(waitTime);
        continue;
      }
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error(`CoinGecko API error (attempt ${attempt + 1}):`, {
          status: response.status,
          statusText: response.statusText,
          body: errorText
        });
        throw new Error(`CoinGecko API error: ${response.status} - ${response.statusText} - ${errorText}`);
      }
      
      const data = await response.json();
      if (!data || !data.prices || !Array.isArray(data.prices)) {
        throw new Error('Invalid response format from CoinGecko API');
      }
      
      console.log('Successfully fetched historical data');
      return data;
    } catch (error) {
      console.error(`Error fetching historical data (attempt ${attempt + 1}):`, error.toString(), error);
      if (attempt === retries - 1) {
        throw new Error(`Failed to fetch historical data after ${retries} attempts: ${error.toString()}`);
      }
      // Wait before retrying with exponential backoff
      const waitTime = Math.pow(2, attempt) * 1000;
      console.log(`Waiting ${waitTime}ms before retry...`);
      await sleep(waitTime);
    }
  }
  throw new Error('Failed to fetch historical data after all retries');
}

// Get recent news with retry logic
async function getRecentNews(retries = 3) {
  for (let attempt = 0; attempt < retries; attempt++) {
    try {
      console.log(`Attempting to fetch news (attempt ${attempt + 1}/${retries})...`);
      // Using the trending coins endpoint as a fallback since status_updates is not available
      const response = await fetch('https://api.coingecko.com/api/v3/search/trending');
      
      if (response.status === 429) {
        // Rate limit hit - wait with exponential backoff
        const waitTime = Math.pow(2, attempt) * 1000; // 1s, 2s, 4s
        console.log(`Rate limit hit, waiting ${waitTime}ms before retry...`);
        await sleep(waitTime);
        continue;
      }
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error(`CoinGecko API error (attempt ${attempt + 1}):`, {
          status: response.status,
          statusText: response.statusText,
          body: errorText
        });
        throw new Error(`CoinGecko API error: ${response.status} - ${response.statusText} - ${errorText}`);
      }
      
      const data = await response.json();
      if (!data.coins || !Array.isArray(data.coins)) {
        throw new Error('Invalid response format from CoinGecko API');
      }
      
      // Format trending coins as news items
      const formattedNews = data.coins.slice(0, 3).map(item => ({
        title: `${item.item.name} (${item.item.symbol.toUpperCase()}) is trending with price_btc: ${item.item.price_btc}`,
        source: 'CoinGecko Trends',
        url: `https://www.coingecko.com/en/coins/${item.item.id}`
      }));
      
      console.log(`Successfully fetched ${formattedNews.length} trending items`);
      return formattedNews;
    } catch (error) {
      console.error(`Error fetching trending data (attempt ${attempt + 1}):`, error.toString(), error);
      if (attempt === retries - 1) {
        // Instead of throwing error, return empty array to allow analysis to continue
        console.warn('Failed to fetch trending data after all retries, continuing without news');
        return [];
      }
      // Wait before retrying with exponential backoff
      const waitTime = Math.pow(2, attempt) * 1000;
      console.log(`Waiting ${waitTime}ms before retry...`);
      await sleep(waitTime);
    }
  }
  return []; // Return empty array if all retries fail
}

// Send message to Telegram
async function sendTelegramMessage(message) {
  try {
    // Escape special characters for HTML
    const escapedMessage = message
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');

    const response = await fetch(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        chat_id: TELEGRAM_CHAT_ID,
        text: escapedMessage,
        parse_mode: 'HTML',
        disable_web_page_preview: true
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`Telegram API error: ${response.status} - ${errorData.description || 'Unknown error'}`);
    }
  } catch (error) {
    console.error('Error sending Telegram message:', error);
    throw error;
  }
} 