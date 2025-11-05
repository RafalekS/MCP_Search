# Critical Parsing Fixes Needed

## Issues Identified

### 1. claudemcp.com - Extracting navigation instead of search results
- **Problem**: When search returns "No servers found", parser extracts all navigation links
- **Fix Needed**: Detect empty results, don't extract navigation menu items
- **Current**: Gets "Servers", "SEO MCP", "Figma Context MCP" etc
- **Expected**: Return 0 results when search finds nothing

### 2. dxt.services - Extracting category links
- **Problem**: Extracting "Latest", "Official", "Featured", "View all" navigation
- **Expected**: 13 actual search results from website
- **Fix Needed**: Better selector filtering, exclude navigation elements

### 3. dxt.so/dxts - Wrong search parameter
- **Problem**: Config uses `?q=n8n` but site expects `?query=n8n`
- **Current**: Only 3 results
- **Expected**: 60 results from website
- **Fix Needed**: Update search endpoint parameter

## Sources to Remove (Broken/Paid)
- aiagentstore.ai (now paid/useless)
- prompthero.com (now paid/useless)

## Parser Improvements Needed

### Generic Parser (_parse_generic_results)
1. Add "no results" detection
2. Expand navigation filter list
3. Check if links are actual content vs UI elements

### Site-Specific Parsers
1. Add claudemcp.com specific parser
2. Add dxt.services specific parser
3. Fix dxt.so parser

## New Sources to Research & Add (5 per category)

### MCP Servers
- Research GitHub trending MCP repos
- Check MCP documentation for official lists
- Find community-curated collections

### DXT Tools
- Desktop extension marketplaces
- Developer tool directories
- Extension registries

### AI Agents
- AI tool directories
- Agent marketplaces
- Platform-specific stores

### Commands
- Command repositories
- Tool collections
- Community resources

## Source Management UI Needed
- Add/Remove sources
- Edit source configurations
- Test source connectivity
- Enable/Disable sources
