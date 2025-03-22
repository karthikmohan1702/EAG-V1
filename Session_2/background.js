// background.js
// Background script for GenAI Beacon - handles content fetching and processing

// Force reset of sources for existing installations
setTimeout(() => {
  chrome.storage.local.get(['sources'], (data) => {
    console.log('Current sources in storage:', data.sources ? Object.keys(data.sources) : 'none');
    chrome.storage.local.set({ sources: SOURCES, version: '1.0.1' }, () => {
      console.log('SOURCES HAVE BEEN FORCE RESET');
    });
  });
}, 1000);

// Import required scripts using importScripts
importScripts('content-scrapers.js', 'gemini-api.js');

// Define current version - update this when you want to force a sources update
const CURRENT_VERSION = '1.0.1';

// Source definitions
const SOURCES = {
  RESEARCH_LABS: {
    anthropic: {
      name: "Anthropic",
      url: "https://www.anthropic.com/blog",
      type: "blog",
      enabled: true
    },
    openai: {
      name: "OpenAI",
      url: "https://openai.com/blog",
      type: "blog",
      enabled: true
    },
    deepmind: {
      name: "Google DeepMind",
      url: "https://www.deepmind.google/blog/",
      type: "blog",
      enabled: true
    },
    google_ai: {
      name: "Google AI",
      url: "https://ai.google/",
      type: "blog",
      enabled: true
    },
    meta_ai: {
      name: "Meta AI",
      url: "https://ai.meta.com/blog/",
      type: "blog",
      enabled: true
    },
    stability_ai: {
      name: "Stability AI",
      url: "https://stability.ai/blog",
      type: "blog",
      enabled: true
    },
    cohere: {
      name: "Cohere",
      url: "https://txt.cohere.com/",
      type: "blog",
      enabled: false
    },
    nvidia_ai: {
      name: "NVIDIA AI",
      url: "https://blogs.nvidia.com/blog/category/deep-learning/",
      type: "blog",
      enabled: false
    },
    midjourney: {
      name: "Midjourney",
      url: "https://docs.midjourney.com/changelog",
      type: "blog",
      enabled: false
    },
    microsoft_research: {
      name: "Microsoft Research",
      url: "https://www.microsoft.com/en-us/research/blog/category/artificial-intelligence/",
      type: "blog",
      enabled: false
    },
    ibm_research: {
      name: "IBM Research",
      url: "https://research.ibm.com/blog/ai",
      type: "blog",
      enabled: false
    }
  },
  ACADEMIC: {
    arxiv_genai: {
      name: "ArXiv (GenAI)",
      url: "https://arxiv.org/search/?query=generative+AI&searchtype=all",
      type: "academic",
      enabled: true
    },
    arxiv_llm: {
      name: "ArXiv (LLMs)",
      url: "https://arxiv.org/search/?query=large+language+model&searchtype=all",
      type: "academic",
      enabled: false
    },
    arxiv_multimodal: {
      name: "ArXiv (Multimodal)",
      url: "https://arxiv.org/search/?query=multimodal+AI&searchtype=all",
      type: "academic",
      enabled: false
    },
    distill: {
      name: "Distill.pub",
      url: "https://distill.pub/",
      type: "academic",
      enabled: false
    }
  },
  COMMUNITY: {
    huggingface: {
      name: "Hugging Face",
      url: "https://huggingface.co/blog",
      type: "blog",
      enabled: true
    },
    ai_alignment_forum: {
      name: "AI Alignment Forum",
      url: "https://www.alignmentforum.org/",
      type: "forum",
      enabled: false
    },
    lesswrong: {
      name: "LessWrong (AI)",
      url: "https://www.lesswrong.com/topics/artificial-intelligence",
      type: "forum",
      enabled: false
    },
    weights_and_biases: {
      name: "Weights & Biases",
      url: "https://wandb.ai/fully-connected",
      type: "blog",
      enabled: false
    },
    replicate: {
      name: "Replicate",
      url: "https://replicate.com/blog",
      type: "blog",
      enabled: false
    }
  },
  INDUSTRY_NEWS: {
    ai_news_mit: {
      name: "MIT AI News",
      url: "https://news.mit.edu/topic/artificial-intelligence2",
      type: "news",
      enabled: false
    },
    venturebeat_ai: {
      name: "VentureBeat AI",
      url: "https://venturebeat.com/category/ai/",
      type: "news",
      enabled: false
    },
    techcrunch_ai: {
      name: "TechCrunch AI",
      url: "https://techcrunch.com/category/artificial-intelligence/",
      type: "news",
      enabled: false
    },
    ai_alignment_newsletter: {
      name: "Import AI Newsletter",
      url: "https://jack-clark.net/",
      type: "newsletter",
      enabled: false
    },
    the_decoder: {
      name: "The Decoder",
      url: "https://the-decoder.com/",
      type: "news",
      enabled: false
    }
  }
};

// Function to update sources for existing users
async function updateSources() {
  try {
    // Get existing settings
    const data = await new Promise(resolve => {
      chrome.storage.local.get(['sources', 'apiKey', 'refreshInterval'], resolve);
    });
    
    // Update sources while preserving user preferences
    const updatedSources = {};
    
    // For each category in the new SOURCES
    for (const category in SOURCES) {
      updatedSources[category] = {};
      
      // For each source in the category
      for (const sourceKey in SOURCES[category]) {
        // Get the new source definition
        const newSource = SOURCES[category][sourceKey];
        
        // Check if user had this source or category before
        let enabled = newSource.enabled; // Default to new source setting
        
        // If old sources exist and have this category and source, preserve the enabled state
        if (data.sources && data.sources[category] && data.sources[category][sourceKey]) {
          enabled = data.sources[category][sourceKey].enabled;
        }
        
        // Add to updated sources
        updatedSources[category][sourceKey] = {
          ...newSource,
          enabled
        };
      }
    }
    
    // Save updated sources back to storage
    await new Promise(resolve => {
      chrome.storage.local.set({ sources: updatedSources }, resolve);
    });
    
    console.log('Sources updated for existing user');
  } catch (error) {
    console.error('Error updating sources:', error);
  }
}

// Initialize extension
chrome.runtime.onInstalled.addListener(({ reason }) => {
  if (reason === 'install') {
    // Set default preferences with your API key
    chrome.storage.local.set({
      sources: SOURCES,
      refreshInterval: 60, // minutes
      apiKey: 'AIzaSyB3a1xt3WmtNzS98IOKGvTkPgp9ERO4yYo',
      lastFetch: null,
      articles: [],
      version: CURRENT_VERSION
    }, () => {
      // Fetch content immediately after installation
      fetchAllContent();
    });
  } else {
    // Check if we need to update sources based on version
    chrome.storage.local.get(['version'], (data) => {
      if (!data.version || data.version !== CURRENT_VERSION) {
        console.log(`Updating from ${data.version || 'unknown'} to ${CURRENT_VERSION}`);
        updateSources();
        chrome.storage.local.set({ version: CURRENT_VERSION });
      }
    });
  }
  
  // Set up alarms for content fetching
  setupAlarms();
});

// Initialize alarms for periodic content fetching
function setupAlarms() {
  chrome.storage.local.get(['refreshInterval'], (data) => {
    const interval = data.refreshInterval || 60;
    
    // Clear any existing alarms
    chrome.alarms.clear('fetchContent');
    
    // Create new alarm
    chrome.alarms.create('fetchContent', {
      periodInMinutes: interval
    });
    
    console.log(`Alarm set to fetch content every ${interval} minutes`);
  });
}

// Listen for alarm triggering
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'fetchContent') {
    fetchAllContent();
  }
});

// Listen for manual refresh requests
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'refreshContent') {
    fetchAllContent().then(() => {
      sendResponse({ success: true });
    }).catch(error => {
      sendResponse({ success: false, error: error.message });
    });
    return true; // Indicates async response
  }
  
  if (message.action === 'updateSettings') {
    setupAlarms();
    sendResponse({ success: true });
  }
  
  // Add handler for manual source reset
  if (message.action === 'resetSources') {
    chrome.storage.local.set({ sources: SOURCES }, () => {
      sendResponse({ success: true });
    });
    return true; // Indicates async response
  }
});

// Main function to fetch content from all enabled sources
async function fetchAllContent() {
  try {
    console.log('Starting content fetch...');
    
    // Get current settings and API key
    const { sources, apiKey } = await new Promise(resolve => {
      chrome.storage.local.get(['sources', 'apiKey'], resolve);
    });
    
    if (!apiKey) {
      console.warn('No API key configured. Aborting content fetch.');
      return;
    }
    
    // Collect all enabled sources
    const enabledSources = [];
    for (const category in sources) {
      for (const sourceKey in sources[category]) {
        const source = sources[category][sourceKey];
        if (source.enabled) {
          enabledSources.push(source);
        }
      }
    }
    
    console.log(`Fetching content from ${enabledSources.length} sources`);
    console.log('Enabled sources:', enabledSources.map(s => s.name)); // Debug enabled sources
    
    // Fetch content from each source
    const allArticles = [];
    for (const source of enabledSources) {
      try {
        const articles = await fetchSourceContent(source);
        if (articles && articles.length > 0) {
          allArticles.push(...articles);
        }
      } catch (error) {
        console.error(`Error fetching from ${source.name}:`, error);
      }
    }
    
    // Process articles with Gemini
    if (allArticles.length > 0) {
      const processedArticles = await processWithGemini(allArticles, apiKey);
      
      // Store the processed articles
      await storeArticles(processedArticles);
      
      // Notify popup if it's open
      chrome.runtime.sendMessage({
        action: 'contentUpdated',
        count: processedArticles.length
      }).catch(() => {
        // Popup might not be open, ignore errors
      });
      
      console.log(`Processed ${processedArticles.length} articles`);
    } else {
      console.log('No new articles found');
    }
    
    // Update last fetch time
    chrome.storage.local.set({ lastFetch: new Date().toISOString() });
    
  } catch (error) {
    console.error('Error in fetchAllContent:', error);
    throw error;
  }
}

// Fetch content from a specific source
async function fetchSourceContent(source) {
  console.log(`Fetching from ${source.name}`);
  
  try {
    // Use the globally available scrapeSource function
    const articles = await scrapeSource(source);
    
    console.log(`Fetched ${articles.length} articles from ${source.name}`);
    return articles;
  } catch (error) {
    console.error(`Error fetching from ${source.name}:`, error);
    return [];
  }
}

// Process articles with Gemini API
async function processWithGemini(articles, apiKey) {
  console.log(`Processing ${articles.length} articles with Gemini`);
  
  // Use the globally available function
  const processedArticles = [];
  
  for (const article of articles) {
    try {
      // Call the Gemini API to analyze the article
      const geminiAnalysis = await processArticleWithGemini(apiKey, article);
      
      processedArticles.push({
        ...article,
        analysis: geminiAnalysis
      });
      
      // Add a small delay between API calls to avoid rate limiting
      await new Promise(resolve => setTimeout(resolve, 500));
      
    } catch (error) {
      console.error(`Error processing article with Gemini:`, error);
      // Still include the article, just without analysis
      processedArticles.push(article);
    }
  }
  
  return processedArticles;
}

// Store processed articles
async function storeArticles(articles) {
  // Get existing articles
  const { articles: existingArticles = [] } = await new Promise(resolve => {
    chrome.storage.local.get(['articles'], resolve);
  });
  
  // Merge new and existing articles, avoiding duplicates
  const allArticles = [...existingArticles];
  
  for (const newArticle of articles) {
    // Check if article already exists (by URL)
    const exists = allArticles.some(article => article.url === newArticle.url);
    if (!exists) {
      allArticles.push(newArticle);
    }
  }
  
  // Sort by date, newest first
  allArticles.sort((a, b) => new Date(b.date) - new Date(a.date));
  
  // Limit to the most recent 100 articles
  const limitedArticles = allArticles.slice(0, 100);
  
  // Store in local storage
  await new Promise(resolve => {
    chrome.storage.local.set({ articles: limitedArticles }, resolve);
  });
  
  return limitedArticles;
}

// Make SOURCES available globally
self.SOURCES = SOURCES;