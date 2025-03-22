// popup.js
// Handles the popup UI functionality for GenAI Beacon

document.addEventListener('DOMContentLoaded', initializePopup);

// Main initialization function
async function initializePopup() {
  console.log('Initializing popup');
  
  // Hide the fetching message initially
  document.getElementById('fetchingMessage').classList.add('hidden');
  
  // Set up event listeners
  document.getElementById('refreshBtn').addEventListener('click', refreshContent);
  
  if (document.getElementById('refreshBtnEmpty')) {
    document.getElementById('refreshBtnEmpty').addEventListener('click', refreshContent);
  }
  
  document.getElementById('categoryFilter').addEventListener('change', filterArticles);
  document.getElementById('sourceFilter').addEventListener('change', filterArticles);
  
  // Add the Reset Sources button handler
  document.getElementById('resetSourcesBtn').addEventListener('click', function() {
    if (confirm('This will reset all sources to default settings. Continue?')) {
      chrome.runtime.sendMessage({ action: 'resetSources' }, function(response) {
        if (response && response.success) {
          alert('Sources have been reset. The popup will now refresh.');
          chrome.runtime.sendMessage({ action: 'refreshContent' }, function() {
            window.location.reload();
          });
        } else {
          alert('Failed to reset sources. Please try again.');
        }
      });
    }
  });
  
  // Load articles
  await loadArticles();
  
  // Load sources into filter dropdown
  await loadSourcesFilter();
  
  // Update last fetched time
  await updateLastFetchedTime();
  
  // If no articles, trigger initial content fetch
  const { articles = [] } = await getStorageData(['articles']);
  if (articles.length === 0) {
    refreshContent();
  }
  
  // Listen for background updates
  chrome.runtime.onMessage.addListener((message) => {
    if (message.action === 'contentUpdated') {
      loadArticles();
      updateLastFetchedTime();
    }
  });
}

// Helper to get data from storage
function getStorageData(keys) {
  return new Promise(resolve => {
    chrome.storage.local.get(keys, resolve);
  });
}

// Load saved articles
async function loadArticles() {
  try {
    const { articles = [] } = await getStorageData(['articles']);
    
    if (articles.length === 0) {
      document.getElementById('noArticles').classList.remove('hidden');
      document.getElementById('articlesContainer').classList.add('hidden');
      return;
    }
    
    // Hide "no articles" message, show articles container
    document.getElementById('noArticles').classList.add('hidden');
    document.getElementById('articlesContainer').classList.remove('hidden');
    
    // Clear existing articles
    const articlesContainer = document.getElementById('articlesContainer');
    articlesContainer.innerHTML = '';
    
    // Apply current filters
    const categoryFilter = document.getElementById('categoryFilter').value;
    const sourceFilter = document.getElementById('sourceFilter').value;
    
    // Filter articles
    let filteredArticles = articles;
    
    if (categoryFilter !== 'all') {
      filteredArticles = filteredArticles.filter(article => 
        article.analysis && article.analysis.category === categoryFilter
      );
    }
    
    if (sourceFilter !== 'all') {
      filteredArticles = filteredArticles.filter(article => 
        article.source === sourceFilter
      );
    }
    
    // Check if we have articles after filtering
    if (filteredArticles.length === 0) {
      document.getElementById('noArticles').classList.remove('hidden');
      document.getElementById('articlesContainer').classList.add('hidden');
      return;
    }
    
    // Render articles
    renderArticles(filteredArticles);
    
  } catch (error) {
    console.error('Error loading articles:', error);
  }
}

// Render articles to the UI
function renderArticles(articles) {
  const articlesContainer = document.getElementById('articlesContainer');
  const template = document.getElementById('articleTemplate');
  
  articlesContainer.innerHTML = ''; // Clear existing articles
  
  articles.forEach(article => {
    const clone = document.importNode(template.content, true);
    
    // Set basic article info
    clone.querySelector('.article-title').textContent = article.title;
    clone.querySelector('.article-summary').textContent = article.analysis ? 
      article.analysis.enhancedSummary : article.summary;
    
    // Create a nicely styled source badge
    const sourceElement = clone.querySelector('.article-source');
    sourceElement.textContent = article.source;
    sourceElement.classList.add('source-badge');
    
    // Add source-specific class for styling
    const sourceKey = getSourceClass(article.source);
    sourceElement.classList.add(sourceKey);
    
    // Format date
    const date = new Date(article.date);
    const formattedDate = date.toLocaleDateString(undefined, { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
    clone.querySelector('.article-date').textContent = formattedDate;
    
    // Set category if available
    if (article.analysis && article.analysis.category) {
      clone.querySelector('.article-category').textContent = article.analysis.category;
    } else {
      clone.querySelector('.article-category').remove();
    }
    
    // Set significance if available with better star display
    if (article.analysis && article.analysis.significance) {
      const stars = '★'.repeat(article.analysis.significance) + 
                   '☆'.repeat(5 - article.analysis.significance);
      clone.querySelector('.article-significance').textContent = stars;
      clone.querySelector('.article-significance').setAttribute('title', 
        `Significance: ${article.analysis.significance}/5`);
    } else {
      clone.querySelector('.article-significance').remove();
    }
    
    // Set key insights if available
    if (article.analysis && article.analysis.keyInsights && article.analysis.keyInsights.length > 0) {
      const insightsList = clone.querySelector('.insights-list');
      article.analysis.keyInsights.forEach(insight => {
        const li = document.createElement('li');
        li.textContent = insight;
        insightsList.appendChild(li);
      });
    } else {
      clone.querySelector('.article-insights').remove();
    }
    
    // Set up action buttons
    const readMoreBtn = clone.querySelector('.read-more-btn');
    readMoreBtn.addEventListener('click', () => {
      chrome.tabs.create({ url: article.url });
    });
    
    const saveBtn = clone.querySelector('.save-btn');
    saveBtn.addEventListener('click', () => {
      toggleBookmark(article);
      // Toggle button state
      saveBtn.classList.toggle('saved');
      saveBtn.textContent = saveBtn.classList.contains('saved') ? 'Bookmarked' : 'Bookmark';
    });
    
    // Add to container
    articlesContainer.appendChild(clone);
  });
}

// Helper function to get CSS class for source styling
function getSourceClass(sourceName) {
  const sourceMap = {
    'Anthropic': 'anthropic',
    'OpenAI': 'openai',
    'Google DeepMind': 'google-deepmind',
    'Google AI': 'google-ai',
    'Meta AI': 'meta-ai',
    'Stability AI': 'stability-ai',
    'Cohere': 'cohere',
    'NVIDIA AI': 'nvidia-ai',
    'Midjourney': 'midjourney',
    'Microsoft Research': 'microsoft-research',
    'IBM Research': 'ibm-research',
    'Hugging Face': 'huggingface',
    'ArXiv (GenAI)': 'arxiv',
    'ArXiv (LLMs)': 'arxiv',
    'ArXiv (Multimodal)': 'arxiv',
    'Distill.pub': 'distill',
    'AI Alignment Forum': 'ai-alignment-forum',
    'LessWrong (AI)': 'lesswrong',
    'Weights & Biases': 'weights-and-biases',
    'Replicate': 'replicate',
    'MIT AI News': 'mit-ai-news',
    'VentureBeat AI': 'venturebeat-ai',
    'TechCrunch AI': 'techcrunch-ai',
    'Import AI Newsletter': 'import-ai',
    'The Decoder': 'the-decoder'
  };
  
  return sourceMap[sourceName] || 'default-source';
}

// Filter articles based on selected filters
function filterArticles() {
  loadArticles(); // Reload with current filters
}

// Load sources into the source filter dropdown
async function loadSourcesFilter() {
  const { sources } = await getStorageData(['sources']);
  const sourceFilter = document.getElementById('sourceFilter');
  
  // Clear existing options except "All Sources"
  while (sourceFilter.options.length > 1) {
    sourceFilter.remove(1);
  }
  
  // Collect all source names
  const sourceNames = new Set();
  
  for (const category in sources) {
    for (const sourceKey in sources[category]) {
      const source = sources[category][sourceKey];
      if (source.enabled) {
        sourceNames.add(source.name);
      }
    }
  }
  
  // Add options to dropdown
  for (const sourceName of sourceNames) {
    const option = document.createElement('option');
    option.value = sourceName;
    option.textContent = sourceName;
    sourceFilter.appendChild(option);
  }
}

// Update last fetched time display
async function updateLastFetchedTime() {
  const { lastFetch } = await getStorageData(['lastFetch']);
  const lastUpdatedSpan = document.getElementById('lastUpdatedTime');
  
  if (lastFetch) {
    const date = new Date(lastFetch);
    const now = new Date();
    
    // Format based on how recent the update was
    if (isSameDay(date, now)) {
      // If today, show "Today at HH:MM"
      const timeString = date.toLocaleTimeString(undefined, {
        hour: '2-digit',
        minute: '2-digit'
      });
      lastUpdatedSpan.textContent = `Today at ${timeString}`;
    } else if (isYesterday(date, now)) {
      // If yesterday, show "Yesterday at HH:MM"
      const timeString = date.toLocaleTimeString(undefined, {
        hour: '2-digit',
        minute: '2-digit'
      });
      lastUpdatedSpan.textContent = `Yesterday at ${timeString}`;
    } else {
      // Otherwise, show full date format
      const formattedDate = date.toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
      lastUpdatedSpan.textContent = formattedDate;
    }
  } else {
    lastUpdatedSpan.textContent = 'Never';
  }
}

// Helper functions for date comparison
function isSameDay(date1, date2) {
  return date1.getDate() === date2.getDate() &&
         date1.getMonth() === date2.getMonth() &&
         date1.getFullYear() === date2.getFullYear();
}

function isYesterday(date1, date2) {
  const yesterday = new Date(date2);
  yesterday.setDate(yesterday.getDate() - 1);
  return date1.getDate() === yesterday.getDate() &&
         date1.getMonth() === yesterday.getMonth() &&
         date1.getFullYear() === yesterday.getFullYear();
}

// Refresh content
function refreshContent() {
  console.log('Refreshing content');
  
  // Show fetching message
  document.getElementById('fetchingMessage').classList.remove('hidden');
  
  // Request background script to refresh content
  chrome.runtime.sendMessage(
    { action: 'refreshContent' },
    (response) => {
      document.getElementById('fetchingMessage').classList.add('hidden');
      
      if (response && response.success) {
        loadArticles();
        updateLastFetchedTime();
      } else {
        // Handle error
        alert('Error refreshing content. Please try again later.');
      }
    }
  );
}

// Toggle bookmark for an article
async function toggleBookmark(article) {
  const { bookmarks = [] } = await getStorageData(['bookmarks']);
  
  // Check if already bookmarked (by URL)
  const bookmarkIndex = bookmarks.findIndex(bookmark => bookmark.url === article.url);
  
  if (bookmarkIndex === -1) {
    // Add to bookmarks
    bookmarks.push(article);
  } else {
    // Remove from bookmarks
    bookmarks.splice(bookmarkIndex, 1);
  }
  
  // Save updated bookmarks
  chrome.storage.local.set({ bookmarks });
}