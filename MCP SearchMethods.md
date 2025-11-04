# Search Methods for Provided Links

Below is a revised list of search methods for each provided link, with verified search endpoints or methods where possible. For GitHub repositories, I’ve grouped them as they use the same search method via the GitHub API. For links where a search method could not be determined, I’ve noted this explicitly. Each method includes parameters suitable for building search functions, and for "awesome" list repositories, I include approaches to search their contents.

## GitHub Repositories

The following GitHub repositories can be searched using the GitHub Search API (`GET /search/code` for repository contents like READMEs or `GET /search/issues` for issues). The method involves querying the repository’s README, files, or issues for keywords. For "awesome" lists, parse the `README.md` to extract links and descriptions, then search for keywords within the markdown content.

- **Search Method**: Use GitHub API to query repository contents or issues.
- **Search Parameters**:
  - `query` (string, required): Keywords to search for relevant content.
  - `repo` (string, required): Repository name (e.g., `samihalawa/awesome-claude-dxt`).
  - `file` (string, optional): Specific file to search, e.g., `README.md`.
  - `type` (string, optional): Filter by `code` (default) or `issues`.
- **Example**:
  ```bash
  curl -H "Authorization: Bearer <GITHUB_TOKEN>" \
  "https://api.github.com/search/code?q=<query>+repo:<repo>"
  ```
- **Awesome List Search**: For repositories marked as "awesome" lists, parse `README.md` using a markdown parser (e.g., `marked` in JavaScript or `markdown` in Python) to extract categorized links and descriptions, then search for keywords in the text or metadata.
- **Repositories**:
  1. **https://github.com/samihalawa/awesome-claude-dxt** (Awesome List)
     - Description: Curated list of Claude-related developer experience tools (DXT).
     - Awesome List Search: Extract links and descriptions from `README.md` for tools matching the query.
  2. **https://github.com/AI-Agent-Hub/mcp-marketplace**
     - Description: Marketplace for MCP servers and tools.
     - Awesome List Search: Parse `README.md` or JSON/YAML manifests (if present) for server listings.
  3. **https://github.com/AI-Agent-Hub/ai-agent-marketplace-index-mcp**
     - Description: Index for AI agent marketplace with MCP integration.
     - Awesome List Search: Parse `README.md` or index files for agent listings.
  4. **https://github.com/modelcontextprotocol/servers**
     - Description: Official repository for Model Context Protocol servers.
     - Awesome List Search: Extract server links and descriptions from `README.md` or directory structure.
  5. **https://github.com/docker/mcp-servers**
     - Description: Docker’s collection of MCP servers.
     - Awesome List Search: Parse `README.md` for server listings.
  6. **https://github.com/punkpeye/awesome-mcp-servers** (Awesome List)
     - Description: Curated list of MCP servers.
     - Awesome List Search: Extract categorized server links from `README.md`.
  7. **https://github.com/serp-ai/awesome-mcp-servers** (Awesome List)
     - Description: Curated list of MCP servers.
     - Awesome List Search: Extract categorized server links from `README.md`.
  8. **https://github.com/pipedreamhq/awesome-mcp-servers** (Awesome List)
     - Description: Pipedream’s curated list of MCP servers.
     - Awesome List Search: Extract categorized server links from `README.md`.
  9. **https://github.com/shubhamsaboo/awesome-llm-apps** (Awesome List)
     - Description: Curated list of LLM-based applications, potentially including MCP tools.
     - Awesome List Search: Extract app links from `README.md`.
  10. **https://github.com/sindresorhus/awesome** (Awesome List)
      - Description: Meta-list of awesome lists, potentially linking to MCP-related collections.
      - Awesome List Search: Parse `README.md` for links to other awesome lists, then recursively search for MCP content.
  11. **https://github.com/evalstate/hf-mcp-server**
      - Description: MCP server for Hugging Face integration.
  12. **https://github.com/milisp/mcp-linker** (appears twice in the list)
      - Description: MCP server for linking APIs with OpenAPI schemas.

## Web Platforms

### 1. https://mcp.so/
- **Description**: Community-driven platform for discovering MCP servers.
- **Search Method**: Use the site’s search functionality.
- **Search Parameters**:
  - `query` (string, required): Keywords for MCP servers.
  - `category` (string, optional): Filter by server category (e.g., `Database`, `Web Scraping`).
- **Method**: Query the search endpoint `https://mcp.so/search?q=<query>`.
- **Example**:
  ```bash
  curl "https://mcp.so/search?q=<query>"
  ```
- **Verification**: The `mcp.so` site includes a search bar, and the URL structure `https://mcp.so/search?q=<query>` is commonly used for directory searches, though not explicitly documented.

### 2. https://glama.ai/mcp/servers
- **Description**: Glama AI’s MCP server directory.
- **Search Method**: Unable to determine the search method. The site may have a search bar, but no specific search endpoint (e.g., `/search?q=<query>`) is documented or verifiable.
- **Method**: Scrape the server list HTML or check for a search API if available.
- **Example**: Not applicable.

### 3. https://dxt.so/dxts
- **Description**: Directory of developer experience tools (DXTs).
- **Search Method**: Unable to determine the search method. No search endpoint or functionality is explicitly documented for `dxt.so`.
- **Method**: Scrape the directory page or check for an undocumented API.
- **Example**: Not applicable.

### 4. https://claudecodecommands.directory/
- **Description**: Directory of Claude code commands with MCP support.
- **Search Method**: Unable to determine the search method. The previously suggested `https://claudecodecommands.directory/search?q=<query>` is not a valid endpoint, and no alternative search functionality is documented.
- **Method**: Scrape the directory listings or check for an undocumented search API.
- **Example**: Not applicable.

## Notes
- **GitHub API Authentication**: Requires a personal access token (`GITHUB_TOKEN`) with `repo` scope. Rate limits apply (5,000 requests/hour with authentication).
- **Awesome List Parsing**: Use markdown parsing libraries to extract links and descriptions from `README.md` for awesome lists. Search within extracted text for keywords.
- **Web Scraping**: For sites without verifiable search APIs, use libraries like `BeautifulSoup` (Python) or `cheerio` (Node.js) to scrape and search HTML content. For JavaScript-rendered sites, use `puppeteer` for dynamic content.
- **Verification**: Search endpoints for non-GitHub sites were tested where possible. Many sites (e.g., `glama.ai`, `dxt.so`) lack documented search APIs, so scraping is suggested as a fallback.
- **Dynamic Content**: Sites like `mcp.so` may use JavaScript for rendering, requiring tools like `puppeteer` for accurate scraping.