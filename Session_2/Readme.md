# GenAI Beacon

GenAI Beacon is a Chrome extension that helps you stay informed about the latest developments in Generative AI by aggregating content from top research labs, academic publications, community resources, and industry news sources.

## Features

- **Content Aggregation**: Automatically fetches articles from 25+ leading GenAI sources
- **AI-Powered Analysis**: Uses Google's Gemini API to analyze and categorize articles
- **Customizable Sources**: Configure which sources to monitor through an easy-to-use settings page
- **Content Filtering**: Filter articles by category or source
- **Bookmarking**: Save interesting articles for later reference
- **Automatic Updates**: Regularly checks for new content in the background

## Installation

### From Chrome Web Store (Coming Soon)
1. Visit the Chrome Web Store (link to be added)
2. Click "Add to Chrome"
3. Follow the installation prompts

### Manual Installation
1. Download the latest release from this repository
2. Unzip the file to a location on your computer
3. In Chrome, go to `chrome://extensions/`
4. Enable "Developer mode" (toggle in the top-right corner)
5. Click "Load unpacked" and select the unzipped folder
6. The extension icon should appear in your Chrome toolbar

## Configuration

### API Key Setup
1. Click the extension icon to open the popup
2. Click on the settings icon (gear) or right-click the extension icon and select "Options"
3. In the API Configuration section, enter your Gemini API key
   - To get a Gemini API key, visit [Google AI Studio](https://ai.google.dev/)
   - Sign in with your Google account
   - Go to API keys in your account settings
   - Create a new API key

### Content Sources
The extension monitors content from the following categories:

**Research Labs**
- Anthropic
- OpenAI
- Google DeepMind
- Google AI
- Meta AI
- Stability AI
- Cohere
- NVIDIA AI
- Midjourney
- Microsoft Research
- IBM Research

**Academic Publications**
- ArXiv (GenAI)
- ArXiv (LLMs)
- ArXiv (Multimodal)
- Distill.pub

**Community Content**
- Hugging Face
- AI Alignment Forum
- LessWrong (AI)
- Weights & Biases
- Replicate

**Industry News**
- MIT AI News
- VentureBeat AI
- TechCrunch AI
- Import AI Newsletter
- The Decoder

### Customizing Sources
1. In the extension settings, navigate to the "Content Sources" section
2. Toggle entire categories on/off using the category switches
3. Toggle individual sources on/off using the checkboxes
4. Changes are saved automatically

## Usage

### Viewing Content
1. Click the extension icon to open the popup
2. Browse the latest articles from your enabled sources
3. Use the Category and Source dropdowns to filter content
4. Click "Read Original" to open the full article in a new tab
5. Click "Bookmark" to save an article for later reference

### Refreshing Content
- Content refreshes automatically according to your refresh interval settings
- Click the refresh button in the popup to manually refresh content
- You can adjust the refresh interval in the settings page

## File Structure

```
genai-beacon/
├── manifest.json        # Extension manifest
├── background.js        # Background service worker
├── content-scrapers.js  # Content scraping functions
├── gemini-api.js        # Gemini API integration
├── popup.html           # Main popup UI
├── popup.js             # Popup functionality
├── options.html         # Settings page UI
├── options.js           # Settings functionality
├── styles.css           # Styles for popup and options
└── icons/               # Extension icons
```

## Development

### Prerequisites
- Chrome browser
- Text editor
- Basic knowledge of HTML, CSS, and JavaScript
- Google Gemini API key

### Local Development
1. Clone this repository
2. Make changes to the code
3. Load the extension in Chrome using the "Load unpacked" method
4. Test your changes

### Adding New Sources
To add a new content source:

1. Add the source to the appropriate category in the `SOURCES` object in `background.js`
2. Create a scraper function for the source in `content-scrapers.js`
3. Add the source to the `scrapeSource` function in `content-scrapers.js`
4. Add the domain to `host_permissions` in `manifest.json`

### Building From Source
1. Ensure all files are updated and saved
2. Zip the entire directory (excluding any development files)
3. The resulting ZIP file can be distributed or uploaded to the Chrome Web Store

## Troubleshooting

### Common Issues

**Content Not Updating**
- Check your API key is correctly set
- Ensure you have at least one source enabled
- Try manually refreshing content
- Check the browser console for any errors

**Extension Not Loading**
- Make sure all required files are present
- Verify the manifest.json is correctly formatted
- Check for JavaScript errors in the browser console

**CORS Issues With Sources**
- Some sources may have CORS restrictions that prevent direct scraping
- Consider implementing proxy solutions for these sources

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Google Gemini API for AI-powered content analysis
- All the amazing GenAI blogs and publications that make this extension possible
- The Chrome extension community for excellent documentation and examples
