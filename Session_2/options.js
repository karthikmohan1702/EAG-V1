// options.js
// Handles the settings page functionality for GenAI Beacon

document.addEventListener('DOMContentLoaded', initializeOptionsPage);

// Source definitions (must match those in background.js)
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
      enabled: false
    },
    meta_ai: {
      name: "Meta AI",
      url: "https://ai.meta.com/blog/",
      type: "blog",
      enabled: false
    },
    stability_ai: {
      name: "Stability AI",
      url: "https://stability.ai/blog",
      type: "blog",
      enabled: false
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

// Main initialization function
async function initializeOptionsPage() {
  console.log('Initializing options page');
  
  // Load current settings
  await loadSettings();
  
  // Set up event listeners
  document.getElementById('toggleApiVisibility').addEventListener('click', toggleApiKeyVisibility);
  document.getElementById('apiKey').addEventListener('change', saveApiKey);
  
  // Category toggle event listeners
  if (document.getElementById('toggleResearchLabs')) {
    document.getElementById('toggleResearchLabs').addEventListener('change', (e) => {
      toggleCategory('RESEARCH_LABS', e.target.checked);
    });
  }
  
  if (document.getElementById('toggleAcademic')) {
    document.getElementById('toggleAcademic').addEventListener('change', (e) => {
      toggleCategory('ACADEMIC', e.target.checked);
    });
  }
  
  if (document.getElementById('toggleCommunity')) {
    document.getElementById('toggleCommunity').addEventListener('change', (e) => {
      toggleCategory('COMMUNITY', e.target.checked);
    });
  }
  
  if (document.getElementById('toggleIndustryNews')) {
    document.getElementById('toggleIndustryNews').addEventListener('change', (e) => {
      toggleCategory('INDUSTRY_NEWS', e.target.checked);
    });
  }
  
  // Save refresh interval if available
  if (document.getElementById('saveRefreshInterval')) {
    document.getElementById('saveRefreshInterval').addEventListener('click', saveRefreshInterval);
  }
}

// Helper to get data from storage
function getStorageData(keys) {
  return new Promise(resolve => {
    chrome.storage.local.get(keys, resolve);
  });
}

// Load current settings from storage
async function loadSettings() {
  try {
    const { 
      sources, 
      apiKey = '',
      refreshInterval = 60
    } = await getStorageData(['sources', 'apiKey', 'refreshInterval']);
    
    // Set API key
    document.getElementById('apiKey').value = apiKey;
    
    // Set refresh interval if field exists
    if (document.getElementById('refreshInterval')) {
      document.getElementById('refreshInterval').value = refreshInterval;
    }
    
    // Populate source lists
    if (sources) {
      populateSourceLists(sources);
    }
  } catch (error) {
    console.error('Error loading settings:', error);
  }
}

// Populate source lists with checkboxes
function populateSourceLists(sources) {
  try {
    // Research Labs (previously Research Blogs)
    const researchLabsList = document.getElementById('researchLabsList');
    if (researchLabsList && sources.RESEARCH_LABS) {
      populateSourceCategory(researchLabsList, sources.RESEARCH_LABS);
    }
    
    // Academic Publications
    const academicList = document.getElementById('academicList');
    if (academicList && sources.ACADEMIC) {
      populateSourceCategory(academicList, sources.ACADEMIC);
    }
    
    // Community Content
    const communityList = document.getElementById('communityList');
    if (communityList && sources.COMMUNITY) {
      populateSourceCategory(communityList, sources.COMMUNITY);
    }
    
    // Industry News (new category)
    const industryNewsList = document.getElementById('industryNewsList');
    if (industryNewsList && sources.INDUSTRY_NEWS) {
      populateSourceCategory(industryNewsList, sources.INDUSTRY_NEWS);
    }
    
    // Set category toggle states
    setToggleStates(sources);
  } catch (error) {
    console.error('Error populating source lists:', error);
  }
}

// Populate a single source category
function populateSourceCategory(container, categorySources) {
  container.innerHTML = '';
  
  for (const sourceKey in categorySources) {
    const source = categorySources[sourceKey];
    
    const sourceItem = document.createElement('div');
    sourceItem.className = 'source-item';
    
    const label = document.createElement('label');
    label.className = 'checkbox-label';
    
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.checked = source.enabled;
    checkbox.dataset.sourceKey = sourceKey;
    checkbox.dataset.category = getCategoryForSource(sourceKey);
    checkbox.addEventListener('change', () => {
      updateSourceState(checkbox.dataset.category, sourceKey, checkbox.checked);
    });
    
    const sourceTitle = document.createElement('span');
    sourceTitle.textContent = source.name;
    
    label.appendChild(checkbox);
    label.appendChild(sourceTitle);
    sourceItem.appendChild(label);
    container.appendChild(sourceItem);
  }
}

// Helper to get category name for a source
function getCategoryForSource(sourceKey) {
  for (const category in SOURCES) {
    if (sourceKey in SOURCES[category]) {
      return category;
    }
  }
  return '';
}

// Set toggle states based on source settings
function setToggleStates(sources) {
  try {
    // Research Labs
    if (document.getElementById('toggleResearchLabs') && sources.RESEARCH_LABS) {
      const allResearchEnabled = Object.values(sources.RESEARCH_LABS)
        .every(source => source.enabled);
      document.getElementById('toggleResearchLabs').checked = allResearchEnabled;
    }
    
    // Academic
    if (document.getElementById('toggleAcademic') && sources.ACADEMIC) {
      const allAcademicEnabled = Object.values(sources.ACADEMIC)
        .every(source => source.enabled);
      document.getElementById('toggleAcademic').checked = allAcademicEnabled;
    }
    
    // Community
    if (document.getElementById('toggleCommunity') && sources.COMMUNITY) {
      const allCommunityEnabled = Object.values(sources.COMMUNITY)
        .every(source => source.enabled);
      document.getElementById('toggleCommunity').checked = allCommunityEnabled;
    }
    
    // Industry News
    if (document.getElementById('toggleIndustryNews') && sources.INDUSTRY_NEWS) {
      const allIndustryNewsEnabled = Object.values(sources.INDUSTRY_NEWS)
        .every(source => source.enabled);
      document.getElementById('toggleIndustryNews').checked = allIndustryNewsEnabled;
    }
  } catch (error) {
    console.error('Error setting toggle states:', error);
  }
}

// Update individual source state
async function updateSourceState(category, sourceKey, enabled) {
  try {
    const { sources } = await getStorageData(['sources']);
    
    // Find and update the source
    if (sources[category] && sources[category][sourceKey]) {
      sources[category][sourceKey].enabled = enabled;
    }
    
    // Save changes automatically
    chrome.storage.local.set({ sources }, () => {
      showStatus('Settings saved');
      
      // Notify background script to update
      chrome.runtime.sendMessage({ action: 'updateSettings' });
    });
    
    // Update category toggle states
    setToggleStates(sources);
  } catch (error) {
    console.error('Error updating source state:', error);
  }
}

// Toggle an entire category
async function toggleCategory(category, enabled) {
  try {
    const { sources } = await getStorageData(['sources']);
    
    // Update all sources in the category
    for (const sourceKey in sources[category]) {
      sources[category][sourceKey].enabled = enabled;
    }
    
    // Save changes automatically
    chrome.storage.local.set({ sources }, () => {
      showStatus('Settings saved');
      
      // Notify background script to update
      chrome.runtime.sendMessage({ action: 'updateSettings' });
    });
    
    // Repopulate lists
    populateSourceLists(sources);
  } catch (error) {
    console.error('Error toggling category:', error);
  }
}

// Toggle API key visibility
function toggleApiKeyVisibility() {
  try {
    const apiKeyInput = document.getElementById('apiKey');
    const type = apiKeyInput.type === 'password' ? 'text' : 'password';
    apiKeyInput.type = type;
  } catch (error) {
    console.error('Error toggling API key visibility:', error);
  }
}

// Save API key
function saveApiKey() {
  try {
    const apiKey = document.getElementById('apiKey').value.trim();
    
    // Save to storage
    chrome.storage.local.set({ apiKey }, () => {
      showStatus('API key saved');
    });
  } catch (error) {
    console.error('Error saving API key:', error);
  }
}

// Save refresh interval
function saveRefreshInterval() {
  try {
    const refreshInterval = parseInt(document.getElementById('refreshInterval').value);
    
    if (isNaN(refreshInterval) || refreshInterval < 15) {
      showStatus('Please enter a valid interval (minimum 15 minutes)', true);
      return;
    }
    
    // Save to storage
    chrome.storage.local.set({ refreshInterval }, () => {
      showStatus('Refresh interval saved');
      
      // Notify background script to update alarms
      chrome.runtime.sendMessage({ action: 'updateSettings' });
    });
  } catch (error) {
    console.error('Error saving refresh interval:', error);
  }
}

// Show status message
function showStatus(message, isError = false) {
  try {
    const statusEl = document.getElementById('statusMessage');
    if (statusEl) {
      statusEl.textContent = message;
      statusEl.className = isError ? 
        'status-message error-message' : 
        'status-message success-message';
      
      // Clear after a delay
      setTimeout(() => {
        statusEl.textContent = '';
        statusEl.className = 'status-message';
      }, 3000);
    }
  } catch (error) {
    console.error('Error showing status message:', error);
  }
}