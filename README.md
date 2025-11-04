# MCP Search - Universal Search for AI Tools

A comprehensive desktop application for searching across multiple sources of AI-related tools, resources, and extensions.

## 🚀 Features

### Search Categories
- **MCP Servers** - Model Context Protocol servers from official and community sources
- **DXT Tools** - Desktop Extensions for Claude and other AI applications  
- **AI Agents** - AI agents from various marketplaces and directories
- **Commands** - Claude Code commands and developer tools
- **AI Tools** - General AI tools and applications
- **AI Prompts** - Prompt marketplaces and libraries

### Key Capabilities
- **Multi-Source Search** - Search across 50+ sources simultaneously
- **Categorized Results** - Results organized by category with separate tabs
- **Dynamic Theming** - Support for custom themes with easy switching
- **Intelligent Caching** - Results cached for faster subsequent searches
- **Search History** - Remember your last 10 searches
- **Direct Links** - Click to open GitHub repositories or websites
- **Source Validation** - Verify source connectivity and availability
- **Progress Tracking** - Real-time search progress with detailed status

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- Windows 10/11 (tested), macOS and Linux (should work)

### Quick Setup
1. Clone or download this repository
2. Navigate to the project directory
3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. Run the application:
```bash
python MCP_Search.pyw
```

## 🎯 Usage

### Basic Search
1. **Enter Search Term** - Type your search query in the text field
2. **Select Categories** - Choose which categories to search (all selected by default)
3. **Click Search** - Press the search button or hit Enter
4. **Browse Results** - Click through the category tabs to see results
5. **View Details** - Click any result to see details and open links

### Advanced Features

#### Theme Customization
- Use the theme dropdown in the header to change appearance
- Themes are loaded from the `themes/` directory
- Current theme is automatically saved and restored

#### Search History
- Your last 10 searches are automatically saved
- Use the "Recent Searches" dropdown to quickly repeat searches
- History persists between application sessions

#### Configuration
- All settings are stored in `config/conf.ini`
- Modify source URLs, API endpoints, and behavior
- Add API keys for enhanced functionality (GitHub, etc.)

## 🔧 Configuration

### API Keys
For enhanced functionality, add API keys in the Settings dialog or directly in `config/conf.ini`:

```ini
[API_KEYS]
github_api_key = your_github_token_here
tavily_api_key = your_tavily_key_here
brave_api_key = your_brave_key_here
```

### Adding New Sources
Edit `config/conf.ini` to add new sources:

```ini
[SOURCE_your_new_source]
name = Your Source Name
description = Description of your source
url = https://example.com
search_method = api
search_endpoint = https://api.example.com/search
search_params = q={query}
result_fields = name,description,url
```

Then add the source to a category:
```ini
[CATEGORIES]
your_category = existing_source1,existing_source2,your_new_source
```

## 🎨 Themes

Custom themes can be added to the `themes/` directory as JSON files. Example theme structure:

```json
{
  "CTkFrame": {
    "fg_color": ["#212121", "#2b2b2b"]
  },
  "CTkButton": {
    "fg_color": ["#3b8ed0", "#1f6aa5"],
    "hover_color": ["#36719f", "#144870"],
    "text_color": ["white", "white"]
  }
}
```

## 📂 Project Structure

```
mcp_search/
├── MCP_Search.pyw          # Main application file
├── theme_frame.py          # Theme management system
├── requirements.txt        # Python dependencies
├── config/
│   └── conf.ini           # Configuration file
├── themes/                # Theme JSON files
├── cache/                 # Cached search results
└── README.md             # This file
```

## 🔍 Supported Sources

### MCP Servers (13 sources)
- mcp.so - Community platform
- mcpservers.org - Official collection
- PulseMCP - Daily updated directory
- GitHub repositories (official and community)

### DXT Tools (6 sources)  
- desktopextensions.com - Official marketplace
- dxt.services - Services hub
- Community GitHub repositories

### AI Agents (9 sources)
- Microsoft Agent Store
- Google Cloud AI Agent Marketplace
- AWS AI Agent Marketplace (upcoming)
- Community marketplaces

### Commands (4 sources)
- claudecodecommands.directory
- GitHub awesome lists
- Community collections

### AI Tools (3 sources)
- AllThingsAI marketplace
- Awesome lists
- Community collections

### AI Prompts (7 sources)
- PromptBase - Premium marketplace
- PromptHero - Free prompts
- FlowGPT - ChatGPT focused
- Community marketplaces

## 🛠️ Development

### Architecture
- **ConfigManager** - Handles all configuration and settings
- **SearchManager** - Orchestrates searches across sources
- **BaseSearchClient** - Handles different search methods (API, GitHub, scraping)
- **CacheManager** - Manages result caching
- **DynamicThemeManager** - Handles theme loading and application

### Search Methods
1. **API** - Direct API calls with JSON responses
2. **GitHub API** - Search GitHub repositories and content
3. **Scrape** - Web scraping for sites without APIs

### Extending the Application
- Add new search methods in `BaseSearchClient`
- Create new result parsers for different data formats
- Add new UI components for specialized result types

## 🐛 Troubleshooting

### Common Issues

#### Application Won't Start
- Ensure Python 3.8+ is installed
- Install all requirements: `pip install -r requirements.txt`
- Check for error messages in the console

#### No Search Results
- Verify internet connection
- Check if sources are accessible
- Try different search terms
- Use the "Validate Sources" button

#### Slow Performance
- Clear cache using Settings > Clear Cache
- Disable unused categories
- Check network connectivity

#### Theme Issues
- Ensure theme files are valid JSON
- Place themes in the `themes/` directory
- Restart application after adding themes

## 📝 Changelog

### Version 1.0.0
- Initial release
- Multi-category search across 50+ sources
- Dynamic theming system
- Search history and caching
- Comprehensive configuration system

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Adding New Sources
1. Update `config/conf.ini` with source configuration
2. Test the new source
3. Update documentation
4. Submit pull request with details

## 📄 License

This project is provided as-is for educational and personal use.

## 🙋 Support

For questions or issues:
1. Check the troubleshooting section
2. Review the configuration file
3. Check application logs for error messages
4. Use the "Validate Sources" feature to test connectivity

## 🔮 Future Enhancements

- Export search results to various formats
- Advanced filtering and sorting options
- Bookmark favorite results
- Scheduled searches and notifications
- Plugin system for custom sources
- Enhanced scraping with BeautifulSoup
- Real-time source monitoring
- Integration with popular development tools

---

**Happy Searching!** 🚀
