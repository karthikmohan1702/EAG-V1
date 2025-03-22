// gemini-api.js
// Handles the Gemini API integration for GenAI Beacon

// Main function to call Gemini API
async function callGeminiAPI(apiKey, prompt, options = {}) {
  // Updated Gemini API endpoint using gemini-2.0-flash instead of gemini-pro
  const apiUrl = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent';
  
  // Default options
  const defaultOptions = {
    temperature: 0.2,
    maxOutputTokens: 500,
    topK: 40,
    topP: 0.95
  };
  
  // Merge options
  const requestOptions = {
    ...defaultOptions,
    ...options
  };
  
  try {
    const response = await fetch(`${apiUrl}?key=${apiKey}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        contents: [
          {
            parts: [
              {
                text: prompt
              }
            ]
          }
        ],
        generationConfig: {
          temperature: requestOptions.temperature,
          maxOutputTokens: requestOptions.maxOutputTokens,
          topK: requestOptions.topK,
          topP: requestOptions.topP
        }
      })
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`Gemini API Error: ${errorData.error.message || 'Unknown error'}`);
    }
    
    const data = await response.json();
    
    // Extract the text from the response
    if (data.candidates && data.candidates.length > 0 && 
        data.candidates[0].content && data.candidates[0].content.parts) {
      return data.candidates[0].content.parts[0].text;
    } else {
      throw new Error('Unexpected Gemini API response format');
    }
  } catch (error) {
    console.error('Error calling Gemini API:', error);
    throw error;
  }
}

// Process article content with Gemini
async function processArticleWithGemini(apiKey, article) {
  // Create the prompt for Gemini
  const prompt = `
As an AI assistant specialized in analyzing Generative AI news, please analyze the following article about generative AI:

Title: ${article.title}
Source: ${article.source}
Summary: ${article.summary || 'Not provided'}
URL: ${article.url}

Please provide the following information in a structured format:

1. Enhanced Summary: Write a concise 2-3 sentence summary that captures the key innovations or developments described in this article.

2. Categorization: Categorize this content into ONE of these categories: LLMs, Multimodal, Research, Product, Ethics, Tools, Business, or Other.

3. Technical Significance: On a scale of 1-5 (where 5 is extremely significant), rate how technically significant this development is for AI practitioners and researchers.

4. Key Insights: List 2-3 bullet points highlighting the most important technical or practical insights from this article.

Your response should be structured in JSON format like this:
{
  "enhancedSummary": "...",
  "category": "...",
  "significance": X,
  "keyInsights": ["...", "...", "..."]
}
`;

  try {
    // Call Gemini API
    const response = await callGeminiAPI(apiKey, prompt);
    
    // Parse the JSON response
    try {
      // Extract JSON from the response (handling potential text before/after the JSON)
      const jsonMatch = response.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        return JSON.parse(jsonMatch[0]);
      } else {
        throw new Error('Could not extract JSON from Gemini response');
      }
    } catch (parseError) {
      console.error('Error parsing Gemini response as JSON:', parseError);
      
      // Fallback: Create a simple object with just the raw response
      return {
        enhancedSummary: response.substring(0, 200) + '...',
        category: 'Other',
        significance: 3,
        keyInsights: ['Could not extract structured insights from Gemini response']
      };
    }
  } catch (error) {
    console.error('Error processing article with Gemini:', error);
    
    // Return a basic analysis object on error
    return {
      enhancedSummary: article.summary || 'No summary available',
      category: 'Other',
      significance: 3,
      keyInsights: ['Failed to process with Gemini AI']
    };
  }
}

// Make functions globally available
self.callGeminiAPI = callGeminiAPI;
self.processArticleWithGemini = processArticleWithGemini;