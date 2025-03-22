// content-scrapers.js
// Contains scrapers for different content sources

// Helper function to ensure URL is absolute
function makeAbsoluteUrl(url, baseUrl) {
  if (!url) return '';
  if (url.startsWith('http')) return url;
  if (url.startsWith('/')) {
    return baseUrl + url;
  }
  return baseUrl + '/' + url;
}

// Simple HTML parser function
function parseHTML(html, selector) {
  // Create a temporary container to extract elements
  const container = document.createElement('div');
  container.innerHTML = html;
  return container.querySelectorAll(selector);
}

// Anthropic Blog Scraper
async function scrapeAnthropicBlog() {
  const url = 'https://www.anthropic.com/blog';
  
  try {
    // For Service Worker environment, we'll need to use fetch and then extract content
    const response = await fetch(url, {
      mode: 'cors',
      credentials: 'omit'
    });
    const html = await response.text();
    
    // Create a placeholder for blog posts
    const articles = [];
    
    // Extract data using regular expressions
    const blogPostRegex = /<article[^>]*>([\s\S]*?)<\/article>/gi;
    const titleRegex = /<h2[^>]*>(.*?)<\/h2>/i;
    const linkRegex = /<a\s+(?:[^>]*?\s+)?href="([^"]*)"[^>]*>/i;
    const dateRegex = /<time[^>]*>(.*?)<\/time>/i;
    const summaryRegex = /<p[^>]*>(.*?)<\/p>/i;
    
    let match;
    while ((match = blogPostRegex.exec(html)) !== null) {
      const postHtml = match[0];
      
      // Extract title
      const titleMatch = titleRegex.exec(postHtml);
      if (!titleMatch) continue;
      const title = titleMatch[1].replace(/<[^>]+>/g, '').trim();
      
      // Extract link
      const linkMatch = linkRegex.exec(postHtml);
      if (!linkMatch) continue;
      const link = makeAbsoluteUrl(linkMatch[1], 'https://www.anthropic.com');
      
      // Extract date
      const dateMatch = dateRegex.exec(postHtml);
      const date = dateMatch ? new Date(dateMatch[1].trim()).toISOString() : new Date().toISOString();
      
      // Extract summary
      const summaryMatch = summaryRegex.exec(postHtml);
      const summary = summaryMatch ? summaryMatch[1].replace(/<[^>]+>/g, '').trim() : '';
      
      articles.push({
        title,
        url: link,
        date,
        summary,
        source: 'Anthropic'
      });
    }
    
    return articles;
  } catch (error) {
    console.error('Error scraping Anthropic blog:', error);
    return [];
  }
}

// OpenAI Blog Scraper
async function scrapeOpenAIBlog() {
  const url = 'https://openai.com/blog';
  
  try {
    const response = await fetch(url, {
      mode: 'cors',
      credentials: 'omit'
    });
    const html = await response.text();
    
    const articles = [];
    
    // Extract data using regular expressions
    const blogPostRegex = /<article[^>]*>([\s\S]*?)<\/article>/gi;
    const titleRegex = /<h2[^>]*>(.*?)<\/h2>/i;
    const linkRegex = /<a\s+(?:[^>]*?\s+)?href="([^"]*)"[^>]*>/i;
    const dateRegex = /<time[^>]*>(.*?)<\/time>/i;
    const summaryRegex = /<p[^>]*>(.*?)<\/p>/i;
    
    let match;
    while ((match = blogPostRegex.exec(html)) !== null) {
      const postHtml = match[0];
      
      // Extract title
      const titleMatch = titleRegex.exec(postHtml);
      if (!titleMatch) continue;
      const title = titleMatch[1].replace(/<[^>]+>/g, '').trim();
      
      // Extract link
      const linkMatch = linkRegex.exec(postHtml);
      if (!linkMatch) continue;
      const link = makeAbsoluteUrl(linkMatch[1], 'https://openai.com');
      
      // Extract date
      const dateMatch = dateRegex.exec(postHtml);
      const date = dateMatch ? new Date(dateMatch[1].trim()).toISOString() : new Date().toISOString();
      
      // Extract summary
      const summaryMatch = summaryRegex.exec(postHtml);
      const summary = summaryMatch ? summaryMatch[1].replace(/<[^>]+>/g, '').trim() : '';
      
      articles.push({
        title,
        url: link,
        date,
        summary,
        source: 'OpenAI'
      });
    }
    
    return articles;
  } catch (error) {
    console.error('Error scraping OpenAI blog:', error);
    return [];
  }
}

// DeepMind Blog Scraper
async function scrapeDeepMindBlog() {
  const url = 'https://www.deepmind.google/blog/';
  
  try {
    // For DeepMind, which has CORS issues, we'll just return a sample article
    // In a production environment, you'd need a proxy server to fetch this content
    
    return [{
      title: "Latest advances in AI research from DeepMind",
      url: "https://www.deepmind.google/blog/",
      date: new Date().toISOString(),
      summary: "Visit the DeepMind blog for the latest research and advancements in artificial intelligence.",
      source: "Google DeepMind"
    }];
    
  } catch (error) {
    console.error('Error scraping DeepMind blog:', error);
    return [];
  }
}

// Hugging Face Blog Scraper
async function scrapeHuggingFaceBlog() {
  const url = 'https://huggingface.co/blog';
  
  try {
    const response = await fetch(url, {
      mode: 'cors',
      credentials: 'omit'
    });
    const html = await response.text();
    
    const articles = [];
    
    // Extract data using regular expressions
    const blogPostRegex = /<article[^>]*>([\s\S]*?)<\/article>/gi;
    const titleRegex = /<h2[^>]*>(.*?)<\/h2>/i;
    const linkRegex = /<a\s+(?:[^>]*?\s+)?href="([^"]*)"[^>]*>/i;
    const dateRegex = /<time[^>]*>(.*?)<\/time>/i;
    const summaryRegex = /<p[^>]*>(.*?)<\/p>/i;
    
    let match;
    while ((match = blogPostRegex.exec(html)) !== null) {
      const postHtml = match[0];
      
      // Extract title
      const titleMatch = titleRegex.exec(postHtml);
      if (!titleMatch) continue;
      const title = titleMatch[1].replace(/<[^>]+>/g, '').trim();
      
      // Extract link
      const linkMatch = linkRegex.exec(postHtml);
      if (!linkMatch) continue;
      const link = makeAbsoluteUrl(linkMatch[1], 'https://huggingface.co');
      
      // Extract date
      const dateMatch = dateRegex.exec(postHtml);
      const date = dateMatch ? new Date(dateMatch[1].trim()).toISOString() : new Date().toISOString();
      
      // Extract summary
      const summaryMatch = summaryRegex.exec(postHtml);
      const summary = summaryMatch ? summaryMatch[1].replace(/<[^>]+>/g, '').trim() : '';
      
      articles.push({
        title,
        url: link,
        date,
        summary,
        source: 'Hugging Face'
      });
    }
    
    return articles;
  } catch (error) {
    console.error('Error scraping Hugging Face blog:', error);
    return [];
  }
}

// ArXiv GenAI Papers Scraper
async function scrapeArxivPapers() {
  // For ArXiv, we'll just return sample papers for simplicity
  // In a real implementation, you would need to parse the RSS feed instead
  
  return [
    {
      title: "Generative AI: Recent Advances and New Frontiers",
      url: "https://arxiv.org/abs/example1",
      date: new Date().toISOString(),
      summary: "This paper explores recent advances in generative AI and discusses potential future directions.",
      source: "ArXiv (GenAI)"
    },
    {
      title: "Large Language Models: Capabilities, Limitations, and Social Impact",
      url: "https://arxiv.org/abs/example2",
      date: new Date().toISOString(),
      summary: "A comprehensive analysis of large language models, their capabilities, and societal implications.",
      source: "ArXiv (GenAI)"
    },
    {
      title: "Multimodal Learning with Text and Images",
      url: "https://arxiv.org/abs/example3",
      date: new Date().toISOString(),
      summary: "This research presents new approaches for multimodal learning combining text and image understanding.",
      source: "ArXiv (GenAI)"
    }
  ];
}

// New Sources Scrapers

// Google AI Scraper
async function scrapeGoogleAIBlog() {
  try {
    // For initial testing, you can return a sample entry
    return [{
      title: "Latest Google AI Research",
      url: "https://ai.google/",
      date: new Date().toISOString(),
      summary: "Visit the Google AI blog for the latest research in artificial intelligence and machine learning.",
      source: "Google AI"
    }];
  } catch (error) {
    console.error('Error scraping Google AI blog:', error);
    return [];
  }
}

// Meta AI Scraper
async function scrapeMetaAIBlog() {
  try {
    return [{
      title: "Latest developments from Meta AI",
      url: "https://ai.meta.com/blog/",
      date: new Date().toISOString(),
      summary: "Check Meta AI for the latest research and developments in artificial intelligence.",
      source: "Meta AI"
    }];
  } catch (error) {
    console.error('Error scraping Meta AI blog:', error);
    return [];
  }
}

// Stability AI Scraper
async function scrapeStabilityAIBlog() {
  try {
    return [{
      title: "Stability AI Updates",
      url: "https://stability.ai/blog",
      date: new Date().toISOString(),
      summary: "Latest updates from Stability AI on generative models and text-to-image technologies.",
      source: "Stability AI"
    }];
  } catch (error) {
    console.error('Error scraping Stability AI blog:', error);
    return [];
  }
}

// Cohere Blog Scraper
async function scrapeCohereBlog() {
  try {
    return [{
      title: "Latest from Cohere",
      url: "https://txt.cohere.com/",
      date: new Date().toISOString(),
      summary: "Read about the latest developments in LLMs and AI applications from Cohere.",
      source: "Cohere"
    }];
  } catch (error) {
    console.error('Error scraping Cohere blog:', error);
    return [];
  }
}

// NVIDIA AI Blog Scraper
async function scrapeNvidiaAIBlog() {
  try {
    return [{
      title: "NVIDIA AI Research Updates",
      url: "https://blogs.nvidia.com/blog/category/deep-learning/",
      date: new Date().toISOString(),
      summary: "The latest from NVIDIA on deep learning, AI hardware, and research developments.",
      source: "NVIDIA AI"
    }];
  } catch (error) {
    console.error('Error scraping NVIDIA AI blog:', error);
    return [];
  }
}

// Midjourney Changelog Scraper
async function scrapeMidjourneyChangelog() {
  try {
    return [{
      title: "Midjourney Updates and Changes",
      url: "https://docs.midjourney.com/changelog",
      date: new Date().toISOString(),
      summary: "Latest updates to the Midjourney image generation model and platform.",
      source: "Midjourney"
    }];
  } catch (error) {
    console.error('Error scraping Midjourney changelog:', error);
    return [];
  }
}

// Microsoft Research AI Blog Scraper
async function scrapeMicrosoftResearchBlog() {
  try {
    return [{
      title: "Microsoft Research AI Updates",
      url: "https://www.microsoft.com/en-us/research/blog/category/artificial-intelligence/",
      date: new Date().toISOString(),
      summary: "Latest research from Microsoft on artificial intelligence, machine learning, and computer vision.",
      source: "Microsoft Research"
    }];
  } catch (error) {
    console.error('Error scraping Microsoft Research blog:', error);
    return [];
  }
}

// IBM Research AI Blog Scraper
async function scrapeIBMResearchBlog() {
  try {
    return [{
      title: "IBM Research AI Updates",
      url: "https://research.ibm.com/blog/ai",
      date: new Date().toISOString(),
      summary: "Latest AI research and developments from IBM Research labs across the world.",
      source: "IBM Research"
    }];
  } catch (error) {
    console.error('Error scraping IBM Research blog:', error);
    return [];
  }
}

// Distill.pub Scraper
async function scrapeDistillPub() {
  try {
    return [{
      title: "Latest from Distill.pub",
      url: "https://distill.pub/",
      date: new Date().toISOString(),
      summary: "Interactive, visual explanations of machine learning concepts from Distill.pub.",
      source: "Distill.pub"
    }];
  } catch (error) {
    console.error('Error scraping Distill.pub:', error);
    return [];
  }
}

// AI Alignment Forum Scraper
async function scrapeAIAlignmentForum() {
  try {
    return [{
      title: "AI Alignment Discussions",
      url: "https://www.alignmentforum.org/",
      date: new Date().toISOString(),
      summary: "Latest discussions on AI alignment, safety, and the future of artificial intelligence.",
      source: "AI Alignment Forum"
    }];
  } catch (error) {
    console.error('Error scraping AI Alignment Forum:', error);
    return [];
  }
}

// LessWrong AI Scraper
async function scrapeLessWrongAI() {
  try {
    return [{
      title: "AI Discussions on LessWrong",
      url: "https://www.lesswrong.com/topics/artificial-intelligence",
      date: new Date().toISOString(),
      summary: "Latest discussions about artificial intelligence, AI safety, and alignment from LessWrong.",
      source: "LessWrong (AI)"
    }];
  } catch (error) {
    console.error('Error scraping LessWrong AI:', error);
    return [];
  }
}

// Weights & Biases Blog Scraper
async function scrapeWeightsBiasesBlog() {
  try {
    return [{
      title: "Weights & Biases AI Updates",
      url: "https://wandb.ai/fully-connected",
      date: new Date().toISOString(),
      summary: "Latest articles on machine learning, MLOps, and AI research from Weights & Biases.",
      source: "Weights & Biases"
    }];
  } catch (error) {
    console.error('Error scraping Weights & Biases blog:', error);
    return [];
  }
}

// Replicate Blog Scraper
async function scrapeReplicateBlog() {
  try {
    return [{
      title: "Replicate Updates",
      url: "https://replicate.com/blog",
      date: new Date().toISOString(),
      summary: "Latest updates from Replicate on machine learning models and infrastructure.",
      source: "Replicate"
    }];
  } catch (error) {
    console.error('Error scraping Replicate blog:', error);
    return [];
  }
}

// MIT AI News Scraper
async function scrapeMITAINews() {
  try {
    return [{
      title: "AI Research News from MIT",
      url: "https://news.mit.edu/topic/artificial-intelligence2",
      date: new Date().toISOString(),
      summary: "Latest news and research on artificial intelligence from MIT.",
      source: "MIT AI News"
    }];
  } catch (error) {
    console.error('Error scraping MIT AI News:', error);
    return [];
  }
}

// VentureBeat AI Scraper
async function scrapeVentureBeatAI() {
  try {
    return [{
      title: "AI Business and Tech News",
      url: "https://venturebeat.com/category/ai/",
      date: new Date().toISOString(),
      summary: "Latest news on AI business, startups, and technology trends from VentureBeat.",
      source: "VentureBeat AI"
    }];
  } catch (error) {
    console.error('Error scraping VentureBeat AI:', error);
    return [];
  }
}

// TechCrunch AI Scraper
async function scrapeTechCrunchAI() {
  try {
    return [{
      title: "TechCrunch AI News",
      url: "https://techcrunch.com/category/artificial-intelligence/",
      date: new Date().toISOString(),
      summary: "Latest news on AI startups, funding, and technology developments from TechCrunch.",
      source: "TechCrunch AI"
    }];
  } catch (error) {
    console.error('Error scraping TechCrunch AI:', error);
    return [];
  }
}

// Import AI Newsletter Scraper
async function scrapeImportAINewsletter() {
  try {
    return [{
      title: "Import AI Newsletter",
      url: "https://jack-clark.net/",
      date: new Date().toISOString(),
      summary: "Jack Clark's Import AI newsletter covering the latest developments and trends in AI research and policy.",
      source: "Import AI Newsletter"
    }];
  } catch (error) {
    console.error('Error scraping Import AI Newsletter:', error);
    return [];
  }
}

// The Decoder Scraper
async function scrapeTheDecoder() {
  try {
    return [{
      title: "The Decoder AI News",
      url: "https://the-decoder.com/",
      date: new Date().toISOString(),
      summary: "Latest news and analysis on AI research, products, and industry developments from The Decoder.",
      source: "The Decoder"
    }];
  } catch (error) {
    console.error('Error scraping The Decoder:', error);
    return [];
  }
}

// Main function to scrape a specific source
async function scrapeSource(source) {
  switch(source.name) {
    case 'Anthropic':
      return scrapeAnthropicBlog();
    case 'OpenAI':
      return scrapeOpenAIBlog();
    case 'Google DeepMind':
      return scrapeDeepMindBlog();
    case 'Hugging Face':
      return scrapeHuggingFaceBlog();
    case 'ArXiv (GenAI)':
      return scrapeArxivPapers();
    case 'ArXiv (LLMs)':
    case 'ArXiv (Multimodal)':
      return scrapeArxivPapers(); // Reusing the same scraper for all ArXiv categories for now
    case 'Google AI':
      return scrapeGoogleAIBlog();
    case 'Meta AI':
      return scrapeMetaAIBlog();
    case 'Stability AI':
      return scrapeStabilityAIBlog();
    case 'Cohere':
      return scrapeCohereBlog();
    case 'NVIDIA AI':
      return scrapeNvidiaAIBlog();
    case 'Midjourney':
      return scrapeMidjourneyChangelog();
    case 'Microsoft Research':
      return scrapeMicrosoftResearchBlog();
    case 'IBM Research':
      return scrapeIBMResearchBlog();
    case 'Distill.pub':
      return scrapeDistillPub();
    case 'AI Alignment Forum':
      return scrapeAIAlignmentForum();
    case 'LessWrong (AI)':
      return scrapeLessWrongAI();
    case 'Weights & Biases':
      return scrapeWeightsBiasesBlog();
    case 'Replicate':
      return scrapeReplicateBlog();
    case 'MIT AI News':
      return scrapeMITAINews();
    case 'VentureBeat AI':
      return scrapeVentureBeatAI();
    case 'TechCrunch AI':
      return scrapeTechCrunchAI();
    case 'Import AI Newsletter':
      return scrapeImportAINewsletter();
    case 'The Decoder':
      return scrapeTheDecoder();
    default:
      console.warn(`No scraper implemented for source: ${source.name}`);
      return [];
  }
}

// Make functions globally available
self.makeAbsoluteUrl = makeAbsoluteUrl;
self.scrapeAnthropicBlog = scrapeAnthropicBlog;
self.scrapeOpenAIBlog = scrapeOpenAIBlog;
self.scrapeDeepMindBlog = scrapeDeepMindBlog;
self.scrapeHuggingFaceBlog = scrapeHuggingFaceBlog;
self.scrapeArxivPapers = scrapeArxivPapers;
self.scrapeGoogleAIBlog = scrapeGoogleAIBlog;
self.scrapeMetaAIBlog = scrapeMetaAIBlog;
self.scrapeStabilityAIBlog = scrapeStabilityAIBlog;
self.scrapeCohereBlog = scrapeCohereBlog;
self.scrapeNvidiaAIBlog = scrapeNvidiaAIBlog;
self.scrapeMidjourneyChangelog = scrapeMidjourneyChangelog;
self.scrapeMicrosoftResearchBlog = scrapeMicrosoftResearchBlog;
self.scrapeIBMResearchBlog = scrapeIBMResearchBlog;
self.scrapeDistillPub = scrapeDistillPub;
self.scrapeAIAlignmentForum = scrapeAIAlignmentForum;
self.scrapeLessWrongAI = scrapeLessWrongAI;
self.scrapeWeightsBiasesBlog = scrapeWeightsBiasesBlog;
self.scrapeReplicateBlog = scrapeReplicateBlog;
self.scrapeMITAINews = scrapeMITAINews;
self.scrapeVentureBeatAI = scrapeVentureBeatAI;
self.scrapeTechCrunchAI = scrapeTechCrunchAI;
self.scrapeImportAINewsletter = scrapeImportAINewsletter;
self.scrapeTheDecoder = scrapeTheDecoder;
self.scrapeSource = scrapeSource;