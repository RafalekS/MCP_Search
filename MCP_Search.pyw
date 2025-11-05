import customtkinter as ctk
from CTkListbox import CTkListbox
import requests
import threading
import webbrowser
import json
import csv
import configparser
import os
import sys
import time
from tkinter import filedialog, messagebox
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import re
from urllib.parse import quote, urljoin
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import hashlib
import pickle
from pathlib import Path
from bs4 import BeautifulSoup

# Import our theme manager
from theme_frame import DynamicThemeManager

# Import validation and export tools
from tools import SourceValidator, ExportManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
class Config:
    WINDOW_TITLE = "MCP Search - Find MCP Servers, DXT Tools, AI Agents & More"
    WINDOW_SIZE = "1400x900"
    CONFIG_FILE = "config/conf.ini"
    CACHE_DIR = "cache"
    MAX_SEARCH_LENGTH = 200
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 3

@dataclass
class SearchResult:
    """Data class for search result information"""
    name: str = ""
    description: str = ""
    url: str = ""
    github_url: str = ""
    category: str = ""
    source: str = ""
    last_updated: str = ""
    additional_info: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.additional_info is None:
            self.additional_info = {}
    
    @property
    def display_name(self) -> str:
        return self.name or "Unknown"
    
    @property
    def clickable_url(self) -> str:
        """Returns the best URL to open for this result"""
        return self.github_url or self.url or ""

class DebugManager:
    """Manages debugging and result analysis for search operations"""
    
    def __init__(self, debug_dir: str = "debug_results"):
        self.debug_dir = Path(debug_dir)
        self.debug_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for different types of debug data
        (self.debug_dir / "results").mkdir(exist_ok=True)
        (self.debug_dir / "html").mkdir(exist_ok=True)
        (self.debug_dir / "logs").mkdir(exist_ok=True)
        
        # Initialize debug log file
        self.debug_log_path = self.debug_dir / "logs" / f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        # Setup debug logger
        self.debug_logger = logging.getLogger('debug')
        self.debug_logger.setLevel(logging.DEBUG)
        
        # Create file handler for debug log
        handler = logging.FileHandler(self.debug_log_path)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.debug_logger.addHandler(handler)
    
    def save_search_results(self, source_name: str, query: str, results: List[SearchResult], 
                          raw_html: str = "", extraction_details: Dict = None):
        """Save detailed search results and extraction information to files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save results as JSON for analysis
        results_data = {
            "source": source_name,
            "query": query,
            "timestamp": timestamp,
            "result_count": len(results),
            "results": []
        }
        
        # Convert SearchResult objects to dictionaries
        for result in results:
            result_dict = {
                "name": result.name,
                "description": result.description,
                "url": result.url,
                "github_url": result.github_url,
                "category": result.category,
                "source": result.source,
                "last_updated": result.last_updated,
                "additional_info": result.additional_info
            }
            results_data["results"].append(result_dict)
        
        # Add extraction details if provided
        if extraction_details:
            results_data["extraction_details"] = extraction_details
        
        # Save results JSON
        results_file = self.debug_dir / "results" / f"{source_name}_{query}_{timestamp}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        # Save raw HTML if provided
        if raw_html:
            html_file = self.debug_dir / "html" / f"{source_name}_{query}_{timestamp}.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(raw_html)
        
        # Log debug information
        self.debug_logger.info(f"SEARCH: {source_name} | QUERY: {query} | RESULTS: {len(results)}")
        
        # Log individual results
        for i, result in enumerate(results):
            self.debug_logger.info(f"  RESULT {i+1}: {result.name[:50]}... | URL: {result.url}")
        
        if extraction_details:
            self.debug_logger.info(f"EXTRACTION DETAILS: {extraction_details}")
        
        print(f"Debug: Saved {len(results)} results from {source_name} to {results_file}")
    
    def save_extraction_debug(self, source_name: str, query: str, 
                            html_content: str, extraction_steps: List[Dict]):
        """Save detailed extraction debugging information"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        debug_data = {
            "source": source_name,
            "query": query,
            "timestamp": timestamp,
            "html_length": len(html_content),
            "extraction_steps": extraction_steps
        }
        
        # Save extraction debug data
        debug_file = self.debug_dir / "logs" / f"extraction_{source_name}_{query}_{timestamp}.json"
        with open(debug_file, 'w', encoding='utf-8') as f:
            json.dump(debug_data, f, indent=2, ensure_ascii=False)
        
        # Log extraction steps
        self.debug_logger.info(f"EXTRACTION DEBUG: {source_name} | QUERY: {query}")
        for step in extraction_steps:
            self.debug_logger.info(f"  STEP: {step}")
    
    def generate_summary_report(self, output_file: str = None):
        """Generate a summary report of all debug results"""
        if not output_file:
            output_file = self.debug_dir / f"summary_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        # Read all result files
        results_files = list((self.debug_dir / "results").glob("*.json"))
        
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>MCP Search Debug Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .source { border: 1px solid #ddd; margin: 10px 0; padding: 10px; }
                .result { margin: 5px 0; padding: 5px; background: #f9f9f9; }
                .error { color: red; }
                .success { color: green; }
                .warning { color: orange; }
            </style>
        </head>
        <body>
            <h1>MCP Search Debug Report</h1>
            <p>Generated: {timestamp}</p>
            <p>Total Sources Analyzed: {total_sources}</p>
        """.format(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            total_sources=len(results_files)
        )
        
        for results_file in results_files:
            try:
                with open(results_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                source_name = data.get('source', 'Unknown')
                query = data.get('query', 'Unknown')
                result_count = data.get('result_count', 0)
                
                html_content += f"""
                <div class="source">
                    <h2>{source_name}</h2>
                    <p><strong>Query:</strong> {query}</p>
                    <p><strong>Results Found:</strong> {result_count}</p>
                """
                
                if result_count > 0:
                    html_content += '<h3>Results:</h3>'
                    for result in data.get('results', []):
                        html_content += f"""
                        <div class="result">
                            <strong>{result.get('name', 'No name')}</strong><br>
                            <small>{result.get('description', 'No description')}</small><br>
                            <a href="{result.get('url', '#')}" target="_blank">{result.get('url', 'No URL')}</a>
                        </div>
                        """
                else:
                    html_content += '<p class="error">No results found</p>'
                
                html_content += '</div>'
                
            except Exception as e:
                html_content += f'<div class="source error">Error reading {results_file}: {e}</div>'
        
        html_content += """
        </body>
        </html>
        """
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Debug: Summary report generated at {output_file}")
        return output_file

class ConfigManager:
    """Manages application configuration from INI file"""
    
    def __init__(self, config_file: str = Config.CONFIG_FILE):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load_config()
    
    def load_config(self):
        """Load configuration from INI file"""
        try:
            if os.path.exists(self.config_file):
                self.config.read(self.config_file)
            else:
                logger.warning(f"Config file {self.config_file} not found, using defaults")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
    
    def save_config(self):
        """Save configuration to INI file"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                self.config.write(f)
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def get_categories(self) -> Dict[str, List[str]]:
        """Get all categories and their sources"""
        categories = {}
        if 'CATEGORIES' in self.config:
            for category, sources_str in self.config['CATEGORIES'].items():
                sources = [s.strip() for s in sources_str.split(',') if s.strip()]
                categories[category] = sources
        return categories
    
    def get_source_config(self, source_id: str) -> Dict[str, str]:
        """Get configuration for a specific source"""
        section_name = f"SOURCE_{source_id}"
        if section_name in self.config:
            return dict(self.config[section_name])
        return {}
    
    def get_api_key(self, key_name: str) -> str:
        """Get API key from configuration"""
        if 'API_KEYS' in self.config:
            return self.config['API_KEYS'].get(key_name, '')
        return ''
    
    def get_search_history(self) -> List[str]:
        """Get search history"""
        history = []
        if 'SEARCH_HISTORY' in self.config:
            for i in range(1, 11):  # search_1 to search_10
                search = self.config['SEARCH_HISTORY'].get(f'search_{i}', '')
                if search:
                    history.append(search)
        return history
    
    def add_to_search_history(self, search_term: str):
        """Add search term to history (keep last 10)"""
        if not search_term.strip():
            return
            
        history = self.get_search_history()
        
        # Remove if already exists
        if search_term in history:
            history.remove(search_term)
        
        # Add to beginning
        history.insert(0, search_term)
        
        # Keep only last 10
        history = history[:10]
        
        # Save back to config
        if 'SEARCH_HISTORY' not in self.config:
            self.config.add_section('SEARCH_HISTORY')
        
        # Clear existing entries
        for i in range(1, 11):
            self.config['SEARCH_HISTORY'][f'search_{i}'] = ''
        
        # Set new entries
        for i, search in enumerate(history, 1):
            self.config['SEARCH_HISTORY'][f'search_{i}'] = search
        
        self.save_config()
    
    def get_current_theme(self) -> str:
        """Get current theme"""
        if 'GENERAL' in self.config:
            return self.config['GENERAL'].get('current_theme', 'default')
        return 'default'
    
    def set_current_theme(self, theme_name: str):
        """Set current theme"""
        if 'GENERAL' not in self.config:
            self.config.add_section('GENERAL')
        self.config['GENERAL']['current_theme'] = theme_name
        self.save_config()

class CacheManager:
    """Manages caching of search results"""
    
    def __init__(self, cache_dir: str = Config.CACHE_DIR):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_cache_key(self, source: str, query: str) -> str:
        """Generate cache key for source and query"""
        combined = f"{source}_{query}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _get_cache_file(self, cache_key: str) -> str:
        """Get cache file path"""
        return os.path.join(self.cache_dir, f"{cache_key}.pkl")
    
    def get_cached_results(self, source: str, query: str, max_age_hours: int = 24) -> Optional[List[SearchResult]]:
        """Get cached results if they exist and are not expired"""
        cache_key = self._get_cache_key(source, query)
        cache_file = self._get_cache_file(cache_key)
        
        if not os.path.exists(cache_file):
            return None
        
        try:
            # Check file age
            file_age = time.time() - os.path.getmtime(cache_file)
            if file_age > max_age_hours * 3600:
                os.remove(cache_file)
                return None
            
            # Load cached results
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            try:
                os.remove(cache_file)
            except:
                pass
            return None
    
    def cache_results(self, source: str, query: str, results: List[SearchResult]):
        """Cache search results"""
        try:
            cache_key = self._get_cache_key(source, query)
            cache_file = self._get_cache_file(cache_key)
            
            with open(cache_file, 'wb') as f:
                pickle.dump(results, f)
        except Exception as e:
            logger.error(f"Error caching results: {e}")

class BaseSearchClient:
    """Base class for search clients"""

    def __init__(self, config_manager: ConfigManager, cache_manager: CacheManager):
        self.config_manager = config_manager
        self.cache_manager = cache_manager
        self.debug_manager = DebugManager()  # Initialize DebugManager
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MCP_Search/1.0 (Windows)'
        })
    
    def search(self, source_id: str, query: str, use_cache: bool = True) -> List[SearchResult]:
        """Search a specific source"""
        # Debug logging - track what's being searched
        logger.info(f"DEBUG: Starting search for '{query}' on source '{source_id}'")
        
        # Check cache first
        if use_cache:
            cached_results = self.cache_manager.get_cached_results(source_id, query)
            if cached_results is not None:
                logger.info(f"Returning cached results for {source_id}: {query}")
                return cached_results
        
        # Get source configuration
        source_config = self.config_manager.get_source_config(source_id)
        if not source_config:
            logger.error(f"No configuration found for source: {source_id}")
            return []
        
        try:
            # Perform search based on method
            search_method = source_config.get('search_method', 'scrape')
            
            if search_method == 'api':
                results = self._search_api(source_config, query)
            elif search_method == 'url_param':
                results = self._search_url_param(source_config, query)
            elif search_method == 'github_api':
                results = self._search_github_api(source_config, query)
            elif search_method == 'awesome_list':
                results = self._search_awesome_list(source_config, query)
            elif search_method == 'scrape':
                results = self._search_scrape(source_config, query)
            else:
                logger.warning(f"Unknown search method: {search_method}")
                return []
            
            # Cache results
            if use_cache and results:
                self.cache_manager.cache_results(source_id, query, results)
            
            logger.info(f"Found {len(results)} results from {source_id}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching {source_id}: {e}")
            return []
    
    def _search_api(self, source_config: Dict[str, str], query: str) -> List[SearchResult]:
        """Search using API endpoint"""
        endpoint = source_config.get('search_endpoint', '')
        if not endpoint:
            return []
        
        # Replace query parameter
        params_template = source_config.get('search_params', 'q={query}')
        
        try:
            # Build URL
            if '{query}' in endpoint:
                url = endpoint.format(query=quote(query))
                response = self.session.get(url, timeout=Config.REQUEST_TIMEOUT)
            else:
                # Parameters in query string
                params = {}
                for param_pair in params_template.split('&'):
                    if '=' in param_pair:
                        key, value = param_pair.split('=', 1)
                        if '{query}' in value:
                            value = value.format(query=quote(query))
                        params[key] = value
                
                response = self.session.get(endpoint, params=params, timeout=Config.REQUEST_TIMEOUT)
            
            response.raise_for_status()
            
            # Parse response
            try:
                data = response.json()
                results = self._parse_api_response(data, source_config)
            except json.JSONDecodeError:
                # Try to parse as text/html
                results = self._parse_text_response(response.text, source_config)
            
            return results
                
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            return []
    
    def _search_url_param(self, source_config: Dict[str, str], query: str) -> List[SearchResult]:
        """Search using URL with query parameter (like site.com/search?q=term)"""
        search_endpoint = source_config.get('search_endpoint', '')
        if not search_endpoint:
            return []
        
        try:
            # Build search URL by replacing {query} placeholder
            search_url = search_endpoint.format(query=quote(query))
            
            # Perform GET request to search URL
            response = self.session.get(search_url, timeout=Config.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            # Parse HTML response to extract individual search results
            return self._parse_search_results_html(response.text, source_config, search_url)
            
        except requests.RequestException as e:
            logger.error(f"URL param search failed for {search_url}: {e}")
            return []
    
    def _search_github_api(self, source_config: Dict[str, str], query: str) -> List[SearchResult]:
        """Search using GitHub API"""
        repo = source_config.get('search_repo', '')
        search_file = source_config.get('search_file', 'README.md')
        
        if not repo:
            return []
        
        try:
            # Get GitHub API key if available
            github_token = self.config_manager.get_api_key('github_api_key')
            headers = {}
            if github_token:
                headers['Authorization'] = f'token {github_token}'
            
            # Search in repository content
            search_url = f"https://api.github.com/search/code"
            params = {
                'q': f'{query} repo:{repo} filename:{search_file}',
                'sort': 'indexed',
                'order': 'desc'
            }
            
            response = self.session.get(search_url, params=params, headers=headers, timeout=Config.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            results = self._parse_github_response(data, source_config, repo)
            
            return results
            
        except requests.RequestException as e:
            logger.error(f"GitHub API request failed: {e}")
            return []
    
    def _search_awesome_list(self, source_config: Dict[str, str], query: str) -> List[SearchResult]:
        """Search using GitHub API to fetch and parse README.md awesome lists"""
        repo = source_config.get('search_repo', '')
        search_file = source_config.get('search_file', 'README.md')
        
        if not repo:
            return []
        
        try:
            # Get GitHub API key if available
            github_token = self.config_manager.get_api_key('github_api_key')
            headers = {}
            if github_token:
                headers['Authorization'] = f'token {github_token}'
            
            # Fetch the README.md content directly
            content_url = f"https://api.github.com/repos/{repo}/contents/{search_file}"
            
            response = self.session.get(content_url, headers=headers, timeout=Config.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            
            # Decode the base64 content
            import base64
            if 'content' in data:
                readme_content = base64.b64decode(data['content']).decode('utf-8')
                results = self._parse_awesome_list_content(readme_content, source_config, query)
                
                return results
            else:
                logger.warning(f"No content found in {repo}/{search_file}")
                return []
                
        except requests.RequestException as e:
            logger.error(f"Awesome list API request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing awesome list content: {e}")
            return []
    
    def _parse_awesome_list_content(self, content: str, source_config: Dict[str, str], query: str) -> List[SearchResult]:
        """Parse README.md content to extract individual tools/servers from awesome lists"""
        results = []
        source_name = source_config.get('name', 'GitHub')
        query_lower = query.lower()
        
        try:
            import re
            
            # Look for markdown list items with links and descriptions
            # Patterns to match:
            # - [Tool Name](url) - Description
            # * [Tool Name](url) - Description  
            # - [Tool Name](url): Description
            # - **[Tool Name](url)** - Description
            
            patterns = [
                r'^[\s]*[-\*]\s*\[([^\]]+)\]\(([^)]+)\)\s*[-:]?\s*(.*)$',  # Basic pattern
                r'^[\s]*[-\*]\s*\*\*\[([^\]]+)\]\(([^)]+)\)\*\*\s*[-:]?\s*(.*)$',  # Bold links
                r'^[\s]*[-\*]\s*\[([^\]]+)\]\(([^)]+)\)\s*\*\*([^*]+)\*\*.*$',  # Description in bold
                r'^[\s]*\d+\.\s*\[([^\]]+)\]\(([^)]+)\)\s*[-:]?\s*(.*)$',  # Numbered lists
            ]
            
            lines = content.split('\n')
            current_category = ""
            
            for line in lines:
                line = line.strip()
                
                # Track categories/sections (headings)
                if line.startswith('#'):
                    current_category = re.sub(r'^#+\s*', '', line).strip()
                    continue
                
                # Try each pattern to extract tool information
                for pattern in patterns:
                    match = re.match(pattern, line, re.MULTILINE)
                    if match:
                        name = match.group(1).strip()
                        url = match.group(2).strip()
                        description = match.group(3).strip() if len(match.groups()) >= 3 else ""
                        
                        # Clean up the description
                        description = re.sub(r'[*_`]', '', description)  # Remove markdown formatting
                        description = description.strip(' .-:')  # Remove trailing punctuation
                        
                        # Skip if no meaningful content
                        if not name or len(name) < 2:
                            continue
                            
                        # Skip navigation links and non-tool entries
                        skip_patterns = [
                            'table of contents', 'contributing', 'license', 'readme',
                            'back to top', 'go to', 'see also', 'more info',
                            'documentation', 'wiki', 'website', 'homepage'
                        ]
                        
                        if any(skip in name.lower() or skip in description.lower() for skip in skip_patterns):
                            continue
                        
                        # Filter by query - check if query matches name, description, or category
                        if query_lower in name.lower() or query_lower in description.lower() or query_lower in current_category.lower():
                            
                            # Enhance description with category if available
                            if current_category and current_category.lower() not in description.lower():
                                description = f"{description} (Category: {current_category})" if description else f"From {current_category} category"
                            
                            # Use description or create one from category
                            if not description and current_category:
                                description = f"Tool from {current_category} category"
                            elif not description:
                                description = "Tool from awesome list"
                            
                            results.append(SearchResult(
                                name=name,
                                description=description,
                                url=url,
                                github_url=url if 'github.com' in url else "",
                                source=source_name,
                                category=current_category
                            ))
                        
                        break  # Found a match, don't try other patterns for this line
            
            logger.info(f"Extracted {len(results)} tools from {source_name} awesome list matching '{query}'")
            
        except Exception as e:
            logger.error(f"Error parsing awesome list content: {e}")
        
        return results
    
    def _search_scrape(self, source_config: Dict[str, str], query: str) -> List[SearchResult]:
        """Search using web scraping"""
        base_url = source_config.get('url', '')
        if not base_url:
            return []
        
        try:
            # For now, just fetch the main page
            # In a full implementation, you'd need to handle search forms, pagination, etc.
            response = self.session.get(base_url, timeout=Config.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            return self._parse_scraped_content(response.text, source_config, query)
            
        except requests.RequestException as e:
            logger.error(f"Scraping request failed: {e}")
            return []
    
    def _parse_api_response(self, data: Dict, source_config: Dict[str, str]) -> List[SearchResult]:
        """Parse API response data"""
        results = []
        source_name = source_config.get('name', 'Unknown')
        
        # This is a simplified parser - each API would need custom parsing
        if isinstance(data, dict):
            if 'results' in data:
                items = data['results']
            elif 'data' in data:
                items = data['data']
            elif 'items' in data:
                items = data['items']
            else:
                items = [data]
        elif isinstance(data, list):
            items = data
        else:
            return results
        
        for item in items:
            if isinstance(item, dict):
                result = SearchResult(
                    name=item.get('name', item.get('title', '')),
                    description=item.get('description', item.get('desc', '')),
                    url=item.get('url', item.get('link', '')),
                    github_url=item.get('github_url', item.get('repository_url', '')),
                    source=source_name,
                    additional_info=item
                )
                results.append(result)
        
        return results
    
    def _parse_github_response(self, data: Dict, source_config: Dict[str, str], repo: str) -> List[SearchResult]:
        """Parse GitHub API response"""
        results = []
        source_name = source_config.get('name', 'Unknown')
        
        # Create a result for the repository itself
        result = SearchResult(
            name=repo.split('/')[-1],
            description=source_config.get('description', ''),
            url=f"https://github.com/{repo}",
            github_url=f"https://github.com/{repo}",
            source=source_name
        )
        results.append(result)
        
        return results
    
    def _parse_search_results_html(self, html: str, source_config: Dict[str, str], search_url: str) -> List[SearchResult]:
        """Parse HTML search results to extract individual items using BeautifulSoup with site-specific logic"""
        results = []
        source_name = source_config.get('name', 'Unknown')
        base_url = source_config.get('url', '')
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Site-specific extraction logic
            if 'pulsemcp.com' in search_url:
                results = self._parse_pulsemcp_results(soup, source_name, base_url)
            elif 'mcpservers.org' in search_url:
                results = self._parse_mcpservers_results(soup, source_name, base_url)
            elif 'mcpserverfinder.com' in search_url:
                results = self._parse_mcpserverfinder_results(soup, source_name, base_url)
            else:
                # Fall back to generic parsing for other sites
                results = self._parse_generic_results(soup, source_name, base_url, search_url)
            
            logger.info(f"Extracted {len(results)} results from {source_name}")
            
            # Save debug information
            extraction_details = {
                "method": "site_specific",
                "site": search_url,
                "results_extracted": len(results),
                "search_url": search_url,
                "base_url": base_url
            }
            
            # Save results and debug info
            self.debug_manager.save_search_results(
                source_name=source_name,
                query=search_url.split('q=')[-1].split('&')[0] if 'q=' in search_url else "unknown",
                results=results,
                raw_html=html,
                extraction_details=extraction_details
            )
            
        except Exception as e:
            logger.error(f"Error parsing search results HTML: {e}")
            # Fallback to basic parsing if BeautifulSoup fails
            return self._basic_fallback_parsing(html, source_config)
        
        return results
    
    def _parse_pulsemcp_results(self, soup, source_name: str, base_url: str) -> List[SearchResult]:
        """Parse PulseMCP specific results - extract actual server cards, not filter buttons"""
        results = []
        
        # Look for actual server cards with test IDs
        server_cards = soup.find_all('div', {'data-test-id': lambda x: x and 'mcp-server-grid-card' in x})
        
        for card in server_cards:
            try:
                # Extract server name from the card - multiple approaches
                name_elem = (card.find('h2') or 
                           card.find('h3') or 
                           card.find('h4') or
                           card.find(['span', 'div'], class_=lambda x: x and ('title' in x or 'name' in x)) or
                           card.find('strong'))
                name = name_elem.get_text(strip=True) if name_elem else "Unknown Server"
                
                # For PulseMCP, look for actual description content, not author names
                description = "No description available"
                
                # Look for description in specific areas of the card, avoiding author names
                desc_candidates = [
                    # Look for paragraph elements that contain substantial text
                    card.find('p', class_=lambda x: x and ('text-gray' in x or 'description' in x or 'summary' in x)),
                    # Look for divs with description-like content
                    card.find('div', class_=lambda x: x and ('description' in x or 'summary' in x or 'content' in x)),
                    # Look for any paragraph that's long enough to be a description
                    *[p for p in card.find_all('p') if p.get_text(strip=True) and len(p.get_text(strip=True)) > 30],
                    # Look for divs with substantial text content
                    *[div for div in card.find_all('div', class_=lambda x: x and 'text' in x if x else False) 
                      if div.get_text(strip=True) and len(div.get_text(strip=True)) > 30]
                ]
                
                for desc_elem in desc_candidates:
                    if desc_elem:
                        desc_text = desc_elem.get_text(strip=True)
                        # Filter out author names, short text, and common non-description content
                        if (desc_text and len(desc_text) > 30 and  # Must be substantial
                            desc_text != name and  # Not the same as name
                            not desc_text.lower() in ['view details', 'learn more', 'read more'] and
                            not desc_text.startswith('http') and
                            not desc_text.startswith('www.') and
                            # Avoid single words that are likely author names
                            len(desc_text.split()) > 3 and  # More than 3 words
                            # Avoid text that looks like author names (single words, usernames)
                            not (len(desc_text.split()) == 1 and '-' in desc_text) and
                            not (len(desc_text.split()) == 1 and desc_text.lower() == desc_text) and
                            # Avoid URLs and email-like patterns
                            '@' not in desc_text and
                            'github.com' not in desc_text.lower()):
                            description = desc_text[:200]  # Limit length
                            break
                
                # Extract URL - look for the main server link
                link_elem = card.find('a', href=True)
                if link_elem and link_elem.get('href'):
                    href = link_elem['href']
                    url = urljoin(base_url, href) if not href.startswith('http') else href
                    
                    # Only add if it's a real server page, not a search filter or navigation
                    if '/servers/' in url and url != base_url and not any(skip in url for skip in ['?q=', 'search', 'filter']):
                        results.append(SearchResult(
                            name=name,
                            description=description,
                            url=url,
                            source=source_name
                        ))
                
            except Exception as e:
                logger.error(f"Error parsing PulseMCP card: {e}")
                continue
        
        return results
    
    def _parse_mcpservers_results(self, soup, source_name: str, base_url: str) -> List[SearchResult]:
        """Parse MCPServers.org specific results - fix name/description extraction"""
        results = []
        
        # Look for server links that contain '/servers/' in the href
        server_links = soup.find_all('a', href=lambda x: x and '/servers/' in x)
        
        for link in server_links:
            try:
                href = link.get('href')
                url = urljoin(base_url, href) if not href.startswith('http') else href
                
                # Extract name from URL path as primary method
                server_path = href.split('/servers/')[-1] if '/servers/' in href else ""
                
                if '/' in server_path:
                    author, repo = server_path.split('/', 1)
                    name = f"{author}/{repo.replace('-', ' ')}"  # Make more readable
                else:
                    name = server_path.replace('-', ' ') or "Unknown Server"
                
                # For mcpservers.org, descriptions are typically not available on the listing page
                # Create a meaningful description from the URL structure, avoiding ad content
                description = f"MCP server by {author}" if '/' in server_path else "MCP server"
                
                # Try to find any additional context, but be very strict about ad filtering
                container = link.parent
                for _ in range(2):  # Only go up 2 parent levels
                    if container and container.parent:
                        container = container.parent
                    else:
                        break
                
                if container:
                    # Look for description but exclude pagination text and AD CONTENT
                    desc_candidates = container.find_all(['p', 'div', 'span'])
                    for desc_elem in desc_candidates:
                        if desc_elem:
                            desc_text = desc_elem.get_text(strip=True)
                            # Very strict filtering to avoid ads and irrelevant content
                            if (desc_text and len(desc_text) > 20 and len(desc_text) < 200 and
                                desc_text != name and
                                not any(skip in desc_text.lower() for skip in [
                                    # Pagination/UI text
                                    'showing', 'of', 'servers', 'page', 'view details', 'more',
                                    'next', 'prev', 'total', 'results', 'found',
                                    # Ad/sponsor content
                                    'sponsor', 'discover', 'extract', 'interact', 'automated access',
                                    'bright data', 'interface powering', 'public internet',
                                    'advertisement', 'promoted', 'featured', 'sponsored',
                                    # Generic content
                                    'click here', 'learn more', 'read more', 'get started'
                                ]) and
                                not desc_text.startswith('http') and
                                # Avoid single sentences that look like ads
                                not (desc_text.count('.') <= 1 and len(desc_text.split()) > 10)):
                                description = desc_text
                                break
                
                results.append(SearchResult(
                    name=name,
                    description=description,
                    url=url,
                    source=source_name
                ))
                
            except Exception as e:
                logger.error(f"Error parsing MCPServers.org link: {e}")
                continue
        
        return results
    
    def _parse_mcpserverfinder_results(self, soup, source_name: str, base_url: str) -> List[SearchResult]:
        """Parse MCPServerFinder specific results with improved description extraction"""
        results = []
        
        # Look for server result elements - try multiple selectors
        selectors = ['.server-card', '.result-item', '.search-result', '.server', '.mcp-server', '.card', '.listing']
        result_elements = []
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements and len(elements) > 1:
                result_elements = elements
                break
        
        if not result_elements:
            # Look for links that contain '/servers/' or similar patterns
            result_elements = soup.find_all('a', href=lambda x: x and ('/servers/' in x or '/server/' in x or '/mcp/' in x))
        
        # If still no elements, try broader approach - look for any elements with server-like content
        if not result_elements:
            # Look for divs or sections that might contain server information
            potential_containers = soup.find_all(['div', 'section', 'article'], class_=True)
            result_elements = [elem for elem in potential_containers if elem.find('a', href=True)]
        
        for element in result_elements[:50]:  # Limit to 50
            try:
                # Enhanced name extraction with more approaches
                name = ""
                name_candidates = [
                    element.find('h1'), element.find('h2'), element.find('h3'), element.find('h4'),
                    element.find(['span', 'div'], class_=lambda x: x and ('name' in x or 'title' in x or 'heading' in x) if x else False),
                    element.find('strong'), element.find('b'),
                    element.find(['div', 'span'], class_=lambda x: x and ('font-bold' in x or 'font-semibold' in x) if x else False)
                ]
                
                for name_elem in name_candidates:
                    if name_elem:
                        name_text = name_elem.get_text(strip=True)
                        if name_text and len(name_text) > 2 and name_text.lower() not in ['view', 'details', 'more', 'server']:
                            name = name_text
                            break
                
                # If still no name and element is a link, use link text
                if not name and element.name == 'a':
                    name = element.get_text(strip=True)
                
                # If no name yet, try to extract from URL
                if not name:
                    link_elem = element.find('a', href=True) if element.name != 'a' else element
                    if link_elem:
                        href = link_elem.get('href', '')
                        if '/servers/' in href:
                            server_path = href.split('/servers/')[-1]
                            name = server_path.replace('-', ' ').replace('_', ' ').title()
                
                # Extract URL
                if element.name == 'a':
                    href = element.get('href')
                else:
                    link_elem = element.find('a', href=True)
                    href = link_elem.get('href') if link_elem else ""
                
                url = urljoin(base_url, href) if href and not href.startswith('http') else href
                
                # ENHANCED description extraction - be more aggressive
                description = "No description available"
                
                # Try multiple approaches to find descriptions
                desc_approaches = [
                    # Approach 1: Look for specific description classes
                    lambda: element.find(['p', 'div'], class_=lambda x: x and ('desc' in x or 'summary' in x or 'content' in x or 'info' in x) if x else False),
                    # Approach 2: Look for any paragraph
                    lambda: element.find('p'),
                    # Approach 3: Look for text in spans or divs
                    lambda: element.find(['span', 'div'], class_=lambda x: x and ('text' in x or 'gray' in x) if x else False),
                    # Approach 4: Look in parent elements
                    lambda: element.parent.find('p') if element.parent else None,
                    lambda: element.parent.find(['div', 'span'], class_=lambda x: x and ('desc' in x or 'text' in x) if x else False) if element.parent else None,
                    # Approach 5: Look for any text content in child divs
                    lambda: next((div for div in element.find_all('div', recursive=False) 
                                if div.get_text(strip=True) and len(div.get_text(strip=True)) > 20), None),
                    # Approach 6: Look for sibling elements
                    lambda: element.find_next_sibling(['p', 'div']) if hasattr(element, 'find_next_sibling') else None
                ]
                
                for approach in desc_approaches:
                    try:
                        desc_elem = approach()
                        if desc_elem:
                            desc_text = desc_elem.get_text(strip=True)
                            if (desc_text and len(desc_text) > 15 and 
                                desc_text != name and
                                desc_text.lower() not in ['view details', 'learn more', 'read more', 'details', 'more', 'click here'] and
                                not desc_text.startswith('http') and
                                not desc_text.startswith('www.') and
                                # Avoid very short descriptions that are likely not meaningful
                                len(desc_text.split()) > 2 and
                                # Avoid descriptions that are just the name repeated
                                not (name.lower() in desc_text.lower() and len(desc_text.split()) <= 3)):
                                description = desc_text[:300]  # Limit length but allow longer descriptions
                                break
                    except Exception:
                        continue
                
                # Only add valid results with better validation
                if (name and url and name != "No name" and 
                    not any(skip in url.lower() for skip in ['search', 'filter', 'new', 'create', 'add', 'login', 'register']) and
                    len(name.strip()) > 2 and
                    # Ensure URL looks like a real server page
                    ('/server' in url.lower() or '/mcp' in url.lower() or base_url in url)):
                    results.append(SearchResult(
                        name=name,
                        description=description,
                        url=url,
                        source=source_name
                    ))
                
            except Exception as e:
                logger.error(f"Error parsing MCPServerFinder element: {e}")
                continue
        
        return results
    
    def _parse_generic_results(self, soup, source_name: str, base_url: str, search_url: str) -> List[SearchResult]:
        """Generic parsing for other sites with improved filtering and description extraction"""
        results = []
        
        # Try different common selectors for search results
        result_selectors = [
            '.server-card', '.result-item', '.search-result', '.mcp-server', 
            '.server-listing', '.server-item', '.card', '.result', '.entry',
            'article', '.project', '.repository', '.tool'
        ]
        
        result_elements = []
        for selector in result_selectors:
            elements = soup.select(selector)
            if elements and len(elements) > 1:  # Found multiple results
                result_elements = elements
                logger.info(f"Found {len(elements)} results using selector: {selector}")
                break
        
        if not result_elements:
            # Try finding links that look like individual results
            all_links = soup.find_all('a', href=True)
            result_elements = [link for link in all_links if self._looks_like_result_link(link, search_url)]
        
        for element in result_elements[:50]:  # Limit to 50 results
            result = self._extract_result_from_element_enhanced(element, {'name': source_name, 'url': base_url}, base_url, search_url)
            if result and result.name.strip() and self._is_valid_result(result, search_url):
                results.append(result)
        
        return results
    
    def _is_valid_result(self, result: SearchResult, search_url: str) -> bool:
        """Filter out garbage results and navigation links"""
        # Skip obvious navigation/utility links
        garbage_patterns = [
            '/new', '/create', '/add', '/search', '/filter', '/login', '/register',
            '/about', '/contact', '/help', '/faq', '/terms', '/privacy',
            'javascript:', 'mailto:', '#', '?page=', '?sort=', '?filter='
        ]
        
        # Skip if URL contains garbage patterns
        if any(pattern in result.url.lower() for pattern in garbage_patterns):
            return False
        
        # Skip if name is too generic or empty
        generic_names = [
            'new', 'create', 'add', 'search', 'filter', 'view', 'details', 'more',
            'home', 'about', 'contact', 'help', 'login', 'register', 'sign up'
        ]
        
        if (not result.name or 
            result.name.lower().strip() in generic_names or 
            len(result.name.strip()) < 3):
            return False
        
        # For cursor.directory, be more specific
        if 'cursor.directory' in search_url:
            # Skip utility pages
            if any(pattern in result.url for pattern in ['/mcp/new', '/new', '/create']):
                return False
            # Only include actual MCP server results
            if '/mcp/' in result.url and result.url.count('/') > 4:  # Has specific server path
                return True
            return False
        
        return True
    
    def _extract_result_from_element_enhanced(self, element, source_config: Dict[str, str], base_url: str, search_url: str) -> Optional[SearchResult]:
        """Enhanced version of result extraction with better description finding"""
        try:
            name = ""
            description = "No description available"
            url = ""
            
            # Enhanced name extraction with multiple approaches
            name_candidates = [
                element.find('h1'), element.find('h2'), element.find('h3'), element.find('h4'),
                element.find(['span', 'div'], class_=lambda x: x and ('title' in x or 'name' in x or 'heading' in x) if x else False),
                element.find('strong'), element.find('b'),
                element.find(['div', 'span'], class_=lambda x: x and 'text-lg' in x if x else False)
            ]
            
            for name_elem in name_candidates:
                if name_elem:
                    name_text = name_elem.get_text(strip=True)
                    if name_text and len(name_text) > 2:
                        name = name_text
                        break
            
            # If element is a link and no name found, use link text
            if not name and element.name == 'a':
                name = element.get_text(strip=True)
            
            # Enhanced description extraction with comprehensive search
            desc_candidates = [
                # Look for description-specific classes
                element.find(['p', 'div'], class_=lambda x: x and ('desc' in x or 'summary' in x or 'content' in x) if x else False),
                element.find(['span', 'div'], class_=lambda x: x and ('text-gray' in x or 'text-sm' in x) if x else False),
                # Look for any paragraph
                element.find('p'),
                # Look in parent elements
                element.parent.find('p') if element.parent else None,
                element.parent.find(['div', 'span'], class_=lambda x: x and ('desc' in x or 'text' in x) if x else False) if element.parent else None
            ]
            
            for desc_elem in desc_candidates:
                if desc_elem:
                    desc_text = desc_elem.get_text(strip=True)
                    if (desc_text and len(desc_text) > 15 and 
                        desc_text != name and
                        desc_text.lower() not in ['view details', 'learn more', 'read more', 'details', 'more', 'click here'] and
                        not desc_text.startswith('http') and
                        not desc_text.startswith('www.')):
                        description = desc_text[:200]  # Limit description length
                        break
            
            # Enhanced URL extraction with preference for result-specific links
            url_candidates = []
            
            if element.name == 'a':
                url_candidates.append(element.get('href'))
            
            # Look for links within the element
            links = element.find_all('a', href=True)
            for link in links:
                href = link.get('href')
                # Prioritize links that look like they go to individual items
                if any(pattern in href for pattern in ['/server', '/tool', '/mcp', '/project', '/repo']):
                    url_candidates.insert(0, href)  # Put at front of list
                else:
                    url_candidates.append(href)
            
            # Use the first valid URL
            for href in url_candidates:
                if href:
                    if not href.startswith('http'):
                        url = urljoin(base_url, href)
                    else:
                        url = href
                    break
            
            if name and url:
                return SearchResult(
                    name=name,
                    description=description,
                    url=url,
                    source=source_config.get('name', 'Unknown')
                )
                
        except Exception as e:
            logger.error(f"Error extracting result from element: {e}")
            
        return None
    
    def _looks_like_result_link(self, link, search_url: str) -> bool:
        """Check if a link looks like an individual search result"""
        href = link.get('href', '')
        text = link.get_text(strip=True)
        
        # Skip navigation, pagination, and other non-result links
        skip_patterns = ['next', 'prev', 'page', 'home', 'about', 'contact', 'login', 'register']
        if any(pattern in href.lower() or pattern in text.lower() for pattern in skip_patterns):
            return False
        
        # Look for links that seem to point to individual items
        result_patterns = ['/server', '/tool', '/agent', '/mcp', '/project', '/repo']
        return any(pattern in href.lower() for pattern in result_patterns) and len(text) > 3
    
    def _extract_result_from_element(self, element, source_config: Dict[str, str], base_url: str) -> Optional[SearchResult]:
        """Extract SearchResult data from a BeautifulSoup element"""
        try:
            name = ""
            description = ""
            url = ""
            
            # Try to find the name/title - prioritize headings and specific classes
            title_selectors = [
                'h1', 'h2', 'h3', 'h4', '.title', '.name', '.server-name', 
                '.server-title', '.card-title', '.result-title', '.entry-title',
                'strong', 'b', '.header', '.heading'
            ]
            for selector in title_selectors:
                title_elem = element.select_one(selector)
                if title_elem:
                    name = title_elem.get_text(strip=True)
                    if name and len(name) > 2:  # Meaningful name
                        break
            
            # Try to find description with more comprehensive selectors
            desc_selectors = [
                '.description', '.desc', '.summary', '.excerpt', '.content',
                '.server-description', '.card-text', '.result-description',
                '.entry-content', '.snippet', '.info', '.details', 'p'
            ]
            for selector in desc_selectors:
                desc_elem = element.select_one(selector)
                if desc_elem:
                    description = desc_elem.get_text(strip=True)
                    if description and len(description) > 10:  # Meaningful description
                        break
            
            # Improved URL extraction - look for primary action links first
            primary_link_selectors = [
                'a[href*="/server"]', 'a[href*="/tool"]', 'a[href*="/agent"]',
                'a[href*="/mcp"]', 'a[href*="/project"]', 'a[href*="/repo"]',
                '.server-link a', '.result-link a', '.card-link a',
                '.title a', '.name a', 'h1 a', 'h2 a', 'h3 a'
            ]
            
            # Try primary selectors first
            for selector in primary_link_selectors:
                link_elem = element.select_one(selector)
                if link_elem and link_elem.get('href'):
                    href = link_elem['href']
                    if self._is_valid_result_link(href):
                        url = self._build_absolute_url(href, base_url)
                        break
            
            # Fallback: find any link in the element if primary search failed
            if not url:
                link_elem = element.find('a', href=True)
                if link_elem:
                    href = link_elem['href']
                    if self._is_valid_result_link(href):
                        url = self._build_absolute_url(href, base_url)
            
            # If we're dealing with a link element directly
            if element.name == 'a' and element.get('href'):
                if not url:
                    href = element['href']
                    if self._is_valid_result_link(href):
                        url = self._build_absolute_url(href, base_url)
                if not name:
                    name = element.get_text(strip=True)
            
            # Use link text as name if no name found
            if not name and url:
                link_elem = element.find('a', href=True)
                if link_elem:
                    link_text = link_elem.get_text(strip=True)
                    if link_text and len(link_text) > 2:
                        name = link_text
            
            # Don't return empty or meaningless results
            if not name or len(name) < 2:
                return None
                
            return SearchResult(
                name=name,
                description=description or "No description available",
                url=url,
                source=source_config.get('name', 'Unknown')
            )
            
        except Exception as e:
            logger.error(f"Error extracting result from element: {e}")
            return None
    
    def _is_valid_result_link(self, href: str) -> bool:
        """Check if a link looks like a valid result link"""
        if not href:
            return False
        
        # Skip obviously non-result links
        skip_patterns = [
            'javascript:', 'mailto:', '#', 'tel:',
            '/search', '/category', '/tag', '/page',
            'facebook.com', 'twitter.com', 'linkedin.com',
            'next', 'prev', 'home', 'about', 'contact', 
            'login', 'register', 'privacy', 'terms'
        ]
        
        href_lower = href.lower()
        if any(pattern in href_lower for pattern in skip_patterns):
            return False
        
        # Prefer links that look like individual items
        good_patterns = [
            '/server', '/tool', '/agent', '/mcp', '/project', 
            '/repo', '/item', '/detail', '/view'
        ]
        
        return any(pattern in href_lower for pattern in good_patterns) or len(href) > 5
    
    def _build_absolute_url(self, href: str, base_url: str) -> str:
        """Build absolute URL from href and base URL"""
        if href.startswith('http'):
            return href
        elif href.startswith('/'):
            return urljoin(base_url, href)
        else:
            return urljoin(base_url + '/', href)
    
    def _basic_fallback_parsing(self, html: str, source_config: Dict[str, str]) -> List[SearchResult]:
        """Basic fallback parsing if BeautifulSoup fails"""
        results = []
        source_name = source_config.get('name', 'Unknown')
        base_url = source_config.get('url', '')
        
        # Look for links in the HTML using regex
        import re
        link_pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>'
        matches = re.findall(link_pattern, html, re.IGNORECASE)
        
        for href, text in matches[:20]:  # Limit to 20 results
            if len(text.strip()) > 3:  # Skip very short link texts
                url = urljoin(base_url, href) if not href.startswith('http') else href
                results.append(SearchResult(
                    name=text.strip(),
                    description=f"Found via basic parsing",
                    url=url,
                    source=source_name
                ))
        
        return results

    def _parse_scraped_content(self, html: str, source_config: Dict[str, str], query: str) -> List[SearchResult]:
        """Parse scraped HTML content using BeautifulSoup for better results"""
        # Use the same parsing logic as search results
        source_name = source_config.get('name', 'Unknown')
        results = self._parse_search_results_html(html, source_config, source_config.get('url', ''))
        
        # Additional debug logging for scraped content
        if results:
            self.debug_manager.save_search_results(
                source_name=source_name,
                query=query,
                results=results,
                raw_html=html,
                extraction_details={
                    "method": "scrape",
                    "base_url": source_config.get('url', ''),
                    "query": query
                }
            )
        
        return results
    
    def _parse_text_response(self, text: str, source_config: Dict[str, str]) -> List[SearchResult]:
        """Parse text response"""
        results = []
        source_name = source_config.get('name', 'Unknown')
        
        # Basic text parsing
        lines = text.split('\n')
        for line in lines[:10]:  # Limit to first 10 lines
            if line.strip():
                result = SearchResult(
                    name=line.strip()[:100],
                    description=f"Content from {source_name}",
                    source=source_name
                )
                results.append(result)
        
        return results

class LoadingDialog(ctk.CTkToplevel):
    """Loading dialog for search operations"""
    
    def __init__(self, parent, message="Searching..."):
        super().__init__(parent)
        self.title("Searching")
        self.geometry("400x150")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.geometry(f"+{parent.winfo_x() + 50}+{parent.winfo_y() + 50}")
        
        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.label = ctk.CTkLabel(main_frame, text=message, font=ctk.CTkFont(size=14))
        self.label.pack(pady=(10, 5))
        
        self.progress = ctk.CTkProgressBar(main_frame, mode="indeterminate")
        self.progress.pack(pady=(5, 10), padx=20, fill="x")
        self.progress.start()
        
        self.status_label = ctk.CTkLabel(main_frame, text="Initializing...", font=ctk.CTkFont(size=12))
        self.status_label.pack(pady=(0, 10))
    
    def update_status(self, status: str):
        """Update status message"""
        self.status_label.configure(text=status)
        self.update()
    
    def close(self):
        """Close the dialog"""
        self.progress.stop()
        self.destroy()

class SearchManager:
    """Manages searches across multiple sources"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.cache_manager = CacheManager()
        self.search_client = BaseSearchClient(config_manager, self.cache_manager)
        self.active_searches = {}
        self.results = {}
        
    def search_category(self, category: str, query: str, progress_callback=None) -> Dict[str, List[SearchResult]]:
        """Search all sources in a category"""
        categories = self.config_manager.get_categories()
        if category not in categories:
            logger.error(f"Category not found: {category}")
            return {}
        
        sources = categories[category]
        results = {}
        failed_sources = []
        
        for i, source_id in enumerate(sources):
            if progress_callback:
                progress_callback(f"Searching {source_id}...", i, len(sources))
            
            try:
                source_results = self.search_client.search(source_id, query)
                if source_results:
                    results[source_id] = source_results
                else:
                    failed_sources.append(source_id)
            except Exception as e:
                logger.error(f"Error searching {source_id}: {e}")
                failed_sources.append(source_id)
        
        # Retry failed sources once
        if failed_sources and progress_callback:
            progress_callback("Retrying failed sources...", len(sources), len(sources))
            
            for source_id in failed_sources[:]:  # Copy list to avoid modification during iteration
                try:
                    time.sleep(1)  # Brief delay before retry
                    source_results = self.search_client.search(source_id, query, use_cache=False)
                    if source_results:
                        results[source_id] = source_results
                        failed_sources.remove(source_id)
                except Exception as e:
                    logger.error(f"Retry failed for {source_id}: {e}")
        
        self.results[category] = results
        return results

class MCPSearchGUI(ctk.CTk):
    """Main GUI application for MCP Search"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize managers
        self.config_manager = ConfigManager()
        self.search_manager = SearchManager(self.config_manager)
        self.export_manager = ExportManager()
        
        # Initialize theme manager first
        self.theme_manager = DynamicThemeManager(self)
        
        # Apply saved theme
        saved_theme = self.config_manager.get_current_theme()
        if saved_theme and saved_theme != 'default':
            self.theme_manager.load_and_apply_theme(saved_theme)
        
        self.title(Config.WINDOW_TITLE)
        self.geometry(Config.WINDOW_SIZE)
        
        # Application state
        self.current_results = {}
        self.selected_results = {}
        self.loading_dialog = None
        self.search_in_progress = False
        
        # UI setup
        self._setup_ui()
        self._bind_events()
        
        logger.info("MCP Search GUI initialized")
    
    def _setup_ui(self):
        """Setup the user interface"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Main frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(4, weight=1)

        self._create_header_section()
        self._create_search_section()
        self._create_category_section()
        self._create_button_section()
        self._create_results_section()
    
    def _create_header_section(self):
        """Create header with theme selector"""
        self.header_frame = ctk.CTkFrame(self.main_frame)
        self.header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)
        
        # Title and theme selector in same row
        title_theme_frame = ctk.CTkFrame(self.header_frame)
        title_theme_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        title_theme_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            title_theme_frame,
            text="MCP Search - Universal Search for AI Tools",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        # Theme selector
        theme_frame = ctk.CTkFrame(title_theme_frame)
        theme_frame.grid(row=0, column=1, padx=10, pady=5, sticky="e")
        
        theme_label = ctk.CTkLabel(theme_frame, text="Theme:", font=ctk.CTkFont(size=12))
        theme_label.grid(row=0, column=0, padx=(10, 5), pady=5)
        
        # Get available themes
        available_themes = self.theme_manager.get_available_themes()
        theme_options = ["Choose Style"] + available_themes
        
        current_theme = self.config_manager.get_current_theme()
        if current_theme in available_themes:
            default_value = current_theme
        else:
            default_value = "Choose Style"
        
        self.theme_selector = ctk.CTkOptionMenu(
            theme_frame,
            values=theme_options,
            command=self.change_theme,
            width=150
        )
        self.theme_selector.set(default_value)
        self.theme_selector.grid(row=0, column=1, padx=(0, 10), pady=5)
    
    def _create_search_section(self):
        """Create search input section"""
        self.search_frame = ctk.CTkFrame(self.main_frame)
        self.search_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.search_frame.grid_columnconfigure(0, weight=1)

        search_label = ctk.CTkLabel(
            self.search_frame,
            text="Search for MCP Servers, DXT Tools, AI Agents, Commands, AI Tools, or AI Prompts:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        search_label.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="w")

        # Search entry with history dropdown
        entry_frame = ctk.CTkFrame(self.search_frame)
        entry_frame.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="ew")
        entry_frame.grid_columnconfigure(0, weight=1)
        
        self.search_entry = ctk.CTkEntry(
            entry_frame,
            placeholder_text="e.g., database MCP server, Claude desktop extension, AI writing assistant...",
            font=ctk.CTkFont(size=12),
            height=35
        )
        self.search_entry.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ew")
        
        # History dropdown
        history = self.config_manager.get_search_history()
        history_options = ["Recent Searches"] + history if history else ["Recent Searches"]
        
        self.history_dropdown = ctk.CTkOptionMenu(
            entry_frame,
            values=history_options,
            command=self.select_from_history,
            width=150
        )
        self.history_dropdown.grid(row=0, column=1, padx=(5, 10), pady=10)
    
    def _create_category_section(self):
        """Create category selection section"""
        self.category_frame = ctk.CTkFrame(self.main_frame)
        self.category_frame.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        category_label = ctk.CTkLabel(
            self.category_frame,
            text="Select Categories to Search:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        category_label.grid(row=0, column=0, padx=20, pady=(15, 10), sticky="w")
        
        # Category checkboxes
        self.category_vars = {}
        self.category_checkboxes = {}
        
        categories = self.config_manager.get_categories()
        checkbox_frame = ctk.CTkFrame(self.category_frame)
        checkbox_frame.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="ew")
        
        # Arrange checkboxes in 2 columns
        col = 0
        row = 0
        for category_id, sources in categories.items():
            # Create nice display name
            display_name = category_id.replace('_', ' ').title()
            source_count = len(sources)
            checkbox_text = f"{display_name} ({source_count} sources)"
            
            var = ctk.BooleanVar(value=True)  # Default to checked
            self.category_vars[category_id] = var
            
            checkbox = ctk.CTkCheckBox(
                checkbox_frame,
                text=checkbox_text,
                variable=var,
                font=ctk.CTkFont(size=12)
            )
            checkbox.grid(row=row, column=col, padx=10, pady=5, sticky="w")
            self.category_checkboxes[category_id] = checkbox
            
            col += 1
            if col > 1:  # 2 columns
                col = 0
                row += 1
        
        # Select/Deselect all buttons
        button_frame = ctk.CTkFrame(checkbox_frame)
        button_frame.grid(row=row+1, column=0, columnspan=2, pady=(10, 0))
        
        select_all_btn = ctk.CTkButton(
            button_frame,
            text="Select All",
            command=self.select_all_categories,
            width=100,
            height=25
        )
        select_all_btn.grid(row=0, column=0, padx=5, pady=5)
        
        deselect_all_btn = ctk.CTkButton(
            button_frame,
            text="Deselect All",
            command=self.deselect_all_categories,
            width=100,
            height=25
        )
        deselect_all_btn.grid(row=0, column=1, padx=5, pady=5)
    
    def _create_button_section(self):
        """Create button section"""
        self.button_frame = ctk.CTkFrame(self.main_frame)
        self.button_frame.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.button_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        self.search_button = ctk.CTkButton(
            self.button_frame,
            text="🔍 Search All Selected Categories",
            command=self.start_search,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40
        )
        self.search_button.grid(row=0, column=0, padx=2, pady=10, sticky="ew")

        self.clear_button = ctk.CTkButton(
            self.button_frame,
            text="🗑️ Clear Results",
            command=self.clear_results,
            fg_color="gray",
            hover_color="darkgray",
            height=40
        )
        self.clear_button.grid(row=0, column=1, padx=2, pady=10, sticky="ew")

        self.validate_button = ctk.CTkButton(
            self.button_frame,
            text="✅ Validate Sources",
            command=self.validate_sources,
            fg_color="orange",
            hover_color="darkorange",
            height=40
        )
        self.validate_button.grid(row=0, column=2, padx=2, pady=10, sticky="ew")

        self.export_button = ctk.CTkButton(
            self.button_frame,
            text="📊 Export Results",
            command=self.show_export_dialog,
            fg_color="green",
            hover_color="darkgreen",
            height=40
        )
        self.export_button.grid(row=0, column=3, padx=2, pady=10, sticky="ew")

        self.settings_button = ctk.CTkButton(
            self.button_frame,
            text="⚙️ Settings",
            command=self.show_settings,
            fg_color="purple",
            hover_color="darkviolet",
            height=40
        )
        self.settings_button.grid(row=0, column=4, padx=2, pady=10, sticky="ew")
    
    def _create_results_section(self):
        """Create results display section with tabs"""
        self.results_frame = ctk.CTkFrame(self.main_frame)
        self.results_frame.grid(row=4, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.results_frame.grid_columnconfigure(0, weight=1)
        self.results_frame.grid_rowconfigure(1, weight=1)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self.results_frame,
            text="Enter a search term, select categories, and click Search to begin",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.grid(row=0, column=0, padx=20, pady=(15, 5))
        
        # Tabview for results
        self.tabview = ctk.CTkTabview(self.results_frame)
        self.tabview.grid(row=1, column=0, padx=20, pady=(5, 15), sticky="nsew")
        
        # Initially hidden
        self.tabview.grid_remove()
        
        # Store tab content
        self.tab_frames = {}
        self.tab_listboxes = {}
        self.tab_details = {}
    
    def _bind_events(self):
        """Bind keyboard and other events"""
        self.search_entry.bind("<Return>", lambda e: self.start_search())
        self.search_entry.bind("<Control-a>", lambda e: self.search_entry.select_range(0, "end"))
        self.bind("<Control-l>", lambda e: self.search_entry.focus())
        self.bind("<F5>", lambda e: self.start_search())
        self.bind("<Escape>", lambda e: self.clear_results())

    def change_theme(self, theme_name):
        """Handle theme change"""
        if theme_name == "Choose Style":
            return
        
        self.theme_manager.load_and_apply_theme(theme_name)
        self.config_manager.set_current_theme(theme_name)
    
    def select_from_history(self, selected):
        """Handle selection from search history"""
        if selected == "Recent Searches" or not selected:
            return
        
        self.search_entry.delete(0, "end")
        self.search_entry.insert(0, selected)
    
    def select_all_categories(self):
        """Select all category checkboxes"""
        for var in self.category_vars.values():
            var.set(True)
    
    def deselect_all_categories(self):
        """Deselect all category checkboxes"""
        for var in self.category_vars.values():
            var.set(False)
    
    def validate_input(self, search_term: str) -> bool:
        """Validate search input"""
        if not search_term.strip():
            self.show_error("Please enter a search term")
            return False
        
        if len(search_term) > Config.MAX_SEARCH_LENGTH:
            self.show_error(f"Search term too long (max {Config.MAX_SEARCH_LENGTH} characters)")
            return False
        
        # Check if any categories are selected
        selected_categories = [cat for cat, var in self.category_vars.items() if var.get()]
        if not selected_categories:
            self.show_error("Please select at least one category to search")
            return False
        
        return True
    
    def start_search(self):
        """Start the search operation"""
        if self.search_in_progress:
            return
        
        search_term = self.search_entry.get().strip()
        
        if not self.validate_input(search_term):
            return
        
        # Add to search history
        self.config_manager.add_to_search_history(search_term)
        
        # Update history dropdown
        history = self.config_manager.get_search_history()
        history_options = ["Recent Searches"] + history if history else ["Recent Searches"]
        self.history_dropdown.configure(values=history_options)
        
        # Get selected categories
        selected_categories = [cat for cat, var in self.category_vars.items() if var.get()]
        
        self.search_in_progress = True
        self.search_button.configure(state="disabled", text="Searching...")
        self.clear_results(keep_status=True)
        
        # Show loading dialog
        self.loading_dialog = LoadingDialog(self, "Searching across multiple sources...")
        
        # Start search in background thread
        threading.Thread(
            target=self._perform_search,
            args=(search_term, selected_categories),
            daemon=True
        ).start()
    
    def _perform_search(self, search_term: str, categories: List[str]):
        """Perform the actual search operation"""
        all_results = {}
        total_categories = len(categories)
        
        def progress_callback(status, current, total):
            if self.loading_dialog:
                self.loading_dialog.update_status(f"{status} ({current}/{total})")
        
        try:
            for i, category in enumerate(categories):
                if self.loading_dialog:
                    self.loading_dialog.update_status(f"Searching {category.replace('_', ' ').title()}...")
                
                category_results = self.search_manager.search_category(
                    category, search_term, progress_callback
                )
                
                if category_results:
                    all_results[category] = category_results
            
            # Update UI in main thread
            self.after(0, lambda: self._handle_search_success(all_results, search_term))
            
        except Exception as e:
            error_msg = f"Search failed: {str(e)}"
            self.after(0, lambda: self._handle_search_error(error_msg))
    
    def _handle_search_success(self, all_results: Dict[str, Dict[str, List[SearchResult]]], search_term: str):
        """Handle successful search results"""
        self._close_loading_dialog()
        
        self.current_results = all_results
        total_results = 0
        
        # Clear existing tabs
        for tab_name in list(self.tabview._tab_dict.keys()):
            self.tabview.delete(tab_name)
        
        self.tab_frames = {}
        self.tab_listboxes = {}
        self.tab_details = {}
        
        if all_results:
            # Create tabs for each category with results
            for category, category_results in all_results.items():
                category_total = sum(len(results) for results in category_results.values())
                total_results += category_total
                
                if category_total > 0:
                    self._create_category_tab(category, category_results)
            
            if total_results > 0:
                self.tabview.grid()
                self.status_label.configure(
                    text=f"Found {total_results} results across {len(all_results)} categories. Click items to view details and open links."
                )
            else:
                self.tabview.grid_remove()
                self.status_label.configure(text="No results found. Try different search terms or check more categories.")
        else:
            self.tabview.grid_remove()
            self.status_label.configure(text="No results found. Try different search terms or check more categories.")
        
        self.search_button.configure(state="normal", text="🔍 Search All Selected Categories")
        self.search_in_progress = False
    
    def _handle_search_error(self, error_msg: str):
        """Handle search errors"""
        self._close_loading_dialog()
        self.show_error(error_msg)
        self.search_button.configure(state="normal", text="🔍 Search All Selected Categories")
        self.search_in_progress = False
    
    def _close_loading_dialog(self):
        """Close loading dialog if open"""
        if self.loading_dialog:
            self.loading_dialog.close()
            self.loading_dialog = None
    
    def _create_category_tab(self, category: str, category_results: Dict[str, List[SearchResult]]):
        """Create a tab for category results"""
        display_name = category.replace('_', ' ').title()
        total_results = sum(len(results) for results in category_results.values())
        tab_name = f"{display_name} ({total_results})"
        
        # Add tab
        self.tabview.add(tab_name)
        tab_frame = self.tabview.tab(tab_name)
        
        # Configure grid
        tab_frame.grid_columnconfigure(1, weight=1)
        tab_frame.grid_rowconfigure(0, weight=1)
        
        # Results list on the left
        list_frame = ctk.CTkFrame(tab_frame)
        list_frame.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")
        list_frame.grid_rowconfigure(1, weight=1)
        
        list_label = ctk.CTkLabel(list_frame, text="Results:", font=ctk.CTkFont(size=14, weight="bold"))
        list_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        
        # Create listbox with results
        listbox = CTkListbox(list_frame, width=300, command=lambda selected: self.on_result_select(category, selected))
        listbox.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        
        # Populate listbox
        for source_id, results in category_results.items():
            for result in results:
                display_text = f"[{source_id}] {result.display_name}"
                listbox.insert("end", display_text)
        
        self.tab_listboxes[category] = listbox
        
        # Details panel on the right
        details_frame = ctk.CTkScrollableFrame(tab_frame)
        details_frame.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="nsew")
        details_frame.grid_columnconfigure(0, weight=1)
        
        # Default message
        default_label = ctk.CTkLabel(
            details_frame,
            text="Select a result from the list to view details",
            font=ctk.CTkFont(size=14)
        )
        default_label.grid(row=0, column=0, padx=20, pady=50)
        
        self.tab_details[category] = details_frame
        self.tab_frames[category] = tab_frame
    
    def on_result_select(self, category: str, selected_text: str):
        """Handle result selection"""
        if not selected_text or category not in self.current_results:
            return
        
        # Parse the selected text to find the actual result
        # Format: "[source_id] result_name"
        if not selected_text.startswith('['):
            return
        
        try:
            source_end = selected_text.index(']')
            source_id = selected_text[1:source_end]
            result_name = selected_text[source_end + 2:]  # Skip '] '
        except (ValueError, IndexError):
            return
        
        # Find the actual result
        result = None
        if source_id in self.current_results[category]:
            for r in self.current_results[category][source_id]:
                if r.display_name == result_name:
                    result = r
                    break
        
        if result:
            self._update_details_panel(category, result)
    
    def _update_details_panel(self, category: str, result: SearchResult):
        """Update the details panel with result information"""
        details_frame = self.tab_details[category]
        
        # Clear existing content
        for widget in details_frame.winfo_children():
            widget.destroy()
        
        # Result name
        name_label = ctk.CTkLabel(
            details_frame,
            text=result.display_name,
            font=ctk.CTkFont(size=18, weight="bold")
        )
        name_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Source
        source_label = ctk.CTkLabel(
            details_frame,
            text=f"Source: {result.source}",
            font=ctk.CTkFont(size=12)
        )
        source_label.grid(row=1, column=0, padx=20, pady=(0, 5), sticky="w")
        
        # Category
        if result.category:
            category_label = ctk.CTkLabel(
                details_frame,
                text=f"Category: {result.category}",
                font=ctk.CTkFont(size=12)
            )
            category_label.grid(row=2, column=0, padx=20, pady=(0, 5), sticky="w")
        
        # Description
        if result.description:
            desc_label = ctk.CTkLabel(
                details_frame,
                text="Description:",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            desc_label.grid(row=3, column=0, padx=20, pady=(15, 5), sticky="w")
            
            desc_text = ctk.CTkTextbox(details_frame, height=100, wrap="word")
            desc_text.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="ew")
            desc_text.insert("1.0", result.description)
            desc_text.configure(state="disabled")
        
        # URLs
        url_row = 5
        if result.github_url:
            github_button = ctk.CTkButton(
                details_frame,
                text="🔗 Open GitHub Repository",
                command=lambda: self.open_url(result.github_url),
                width=200,
                height=35
            )
            github_button.grid(row=url_row, column=0, padx=20, pady=5, sticky="w")
            url_row += 1
        
        if result.url and result.url != result.github_url:
            url_button = ctk.CTkButton(
                details_frame,
                text="🌐 Open Website",
                command=lambda: self.open_url(result.url),
                width=200,
                height=35,
                fg_color="green",
                hover_color="darkgreen"
            )
            url_button.grid(row=url_row, column=0, padx=20, pady=5, sticky="w")
            url_row += 1
        
        # Last updated
        if result.last_updated:
            updated_label = ctk.CTkLabel(
                details_frame,
                text=f"Last Updated: {result.last_updated}",
                font=ctk.CTkFont(size=12)
            )
            updated_label.grid(row=url_row, column=0, padx=20, pady=(15, 5), sticky="w")
        
        # Additional info
        if result.additional_info:
            info_label = ctk.CTkLabel(
                details_frame,
                text="Additional Information:",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            info_label.grid(row=url_row+1, column=0, padx=20, pady=(15, 5), sticky="w")
            
            info_text = ctk.CTkTextbox(details_frame, height=80, wrap="word")
            info_text.grid(row=url_row+2, column=0, padx=20, pady=(0, 20), sticky="ew")
            
            # Format additional info nicely
            info_str = ""
            for key, value in result.additional_info.items():
                if isinstance(value, (str, int, float)) and value:
                    info_str += f"{key}: {value}\n"
            
            info_text.insert("1.0", info_str)
            info_text.configure(state="disabled")
    
    def open_url(self, url: str):
        """Open URL in default browser"""
        if url:
            try:
                webbrowser.open(url)
                logger.info(f"Opened URL: {url}")
            except Exception as e:
                logger.error(f"Error opening URL {url}: {e}")
                self.show_error(f"Could not open URL: {url}")
    
    def clear_results(self, keep_status: bool = False):
        """Clear search results"""
        self.current_results = {}
        self.selected_results = {}
        
        # Hide tabview
        self.tabview.grid_remove()
        
        # Clear tabs
        for tab_name in list(self.tabview._tab_dict.keys()):
            self.tabview.delete(tab_name)
        
        self.tab_frames = {}
        self.tab_listboxes = {}
        self.tab_details = {}
        
        if not keep_status:
            self.status_label.configure(text="Enter a search term, select categories, and click Search to begin")
    
    def validate_sources(self):
        """Comprehensive validation of all configured sources"""
        if self.search_in_progress:
            return
        
        # Confirm with user since this is a comprehensive test
        result = messagebox.askyesno(
            "Source Validation",
            "This will test all 50+ configured sources for:\n\n"
            "• Connectivity (can we reach the site?)\n"
            "• Functionality (does search work?)\n" 
            "• Parsing (can we extract results?)\n\n"
            "This may take several minutes. Continue?"
        )
        
        if not result:
            return
        
        self.search_in_progress = True
        self.validate_button.configure(state="disabled", text="Validating...")
        
        # Show loading dialog
        self.loading_dialog = LoadingDialog(self, "Validating sources...")
        
        # Start validation in background thread
        threading.Thread(
            target=self._perform_validation,
            daemon=True
        ).start()
    
    def _perform_validation(self):
        """Perform comprehensive source validation"""
        def progress_callback(status, current, total):
            if self.loading_dialog:
                self.loading_dialog.update_status(f"{status} ({current}/{total})")
        
        try:
            # Create validator and run comprehensive validation
            validator = SourceValidator(self.config_manager)
            validation_results = validator.validate_all_sources(progress_callback)
            
            # Calculate summary statistics
            total_sources = sum(len(category_results) for category_results in validation_results.values())
            working_sources = sum(1 for category_results in validation_results.values() 
                                for result in category_results.values() 
                                if result.get('overall_status') == 'working')
            failed_sources = sum(1 for category_results in validation_results.values() 
                               for result in category_results.values() 
                               if result.get('overall_status') == 'failed')
            
            # Update UI in main thread
            self.after(0, lambda: self._handle_validation_success(validation_results, total_sources, working_sources, failed_sources))
            
        except Exception as e:
            error_msg = f"Validation failed: {str(e)}"
            self.after(0, lambda: self._handle_validation_error(error_msg))
    
    def _handle_validation_success(self, validation_results: Dict, total_sources: int, working_sources: int, failed_sources: int):
        """Handle successful validation completion"""
        self._close_loading_dialog()
        
        # Show results summary with option to open report
        success_rate = (working_sources / total_sources * 100) if total_sources > 0 else 0
        
        result = messagebox.askyesno(
            "Validation Complete",
            f"Source validation completed!\n\n"
            f"📊 Summary:\n"
            f"• Total sources tested: {total_sources}\n"
            f"• Working sources: {working_sources}\n"
            f"• Failed sources: {failed_sources}\n"
            f"• Success rate: {success_rate:.1f}%\n\n"
            f"Would you like to open the detailed validation report?"
        )
        
        if result:
            # Generate and open the report
            try:
                validator = SourceValidator(self.config_manager)
                report_file = validator.generate_validation_report(validation_results)
                
                # Open the report file
                import subprocess
                subprocess.run(['start', str(report_file)], shell=True)
                
            except Exception as e:
                messagebox.showerror("Error", f"Error opening validation report: {str(e)}")
        
        self.validate_button.configure(state="normal", text="✅ Validate Sources")
        self.search_in_progress = False
    
    def _handle_validation_error(self, error_msg: str):
        """Handle validation errors"""
        self._close_loading_dialog()
        self.show_error(error_msg)
        self.validate_button.configure(state="normal", text="✅ Validate Sources")
        self.search_in_progress = False
    
    def show_export_dialog(self):
        """Show export options dialog"""
        if not self.current_results:
            self.show_error("No search results to export. Please perform a search first.")
            return
        
        # Create export dialog
        export_window = ctk.CTkToplevel(self)
        export_window.title("Export Search Results")
        export_window.geometry("500x400")
        export_window.transient(self)
        export_window.grab_set()
        
        # Center on parent
        export_window.geometry(f"+{self.winfo_x() + 200}+{self.winfo_y() + 150}")
        
        # Main frame
        main_frame = ctk.CTkFrame(export_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Export Search Results",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(10, 20))
        
        # Results summary
        total_results = sum(len(source_results) for category_results in self.current_results.values() 
                          for source_results in category_results.values())
        summary_label = ctk.CTkLabel(
            main_frame,
            text=f"📊 Ready to export {total_results} results from {len(self.current_results)} categories",
            font=ctk.CTkFont(size=14)
        )
        summary_label.pack(pady=(0, 20))
        
        # Format selection
        format_label = ctk.CTkLabel(
            main_frame,
            text="Select Export Format:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        format_label.pack(pady=(0, 10))
        
        # Format radio buttons
        format_var = ctk.StringVar(value="csv")
        
        csv_radio = ctk.CTkRadioButton(
            main_frame,
            text="📄 CSV - Spreadsheet format (Excel compatible)",
            variable=format_var,
            value="csv"
        )
        csv_radio.pack(pady=5, anchor="w", padx=20)
        
        json_radio = ctk.CTkRadioButton(
            main_frame,
            text="🔧 JSON - Structured data format (programmers)",
            variable=format_var,
            value="json"
        )
        json_radio.pack(pady=5, anchor="w", padx=20)
        
        pdf_radio = ctk.CTkRadioButton(
            main_frame,
            text="📑 PDF - Formatted report (presentation)",
            variable=format_var,
            value="pdf"
        )
        pdf_radio.pack(pady=5, anchor="w", padx=20)
        
        # Description for selected format
        format_info = ctk.CTkTextbox(main_frame, height=80, wrap="word")
        format_info.pack(fill="x", padx=20, pady=(20, 10))
        
        def update_format_info():
            format_descriptions = {
                "csv": "CSV format exports all results in a spreadsheet-compatible format. Each row contains one result with columns for category, source, name, description, URL, etc. Perfect for analysis in Excel or Google Sheets.",
                "json": "JSON format exports structured data with complete metadata. Includes nested categories, sources, and all result details. Ideal for developers and automated processing.",
                "pdf": "PDF format creates a formatted report with tables and sections for each category. Professional appearance suitable for presentations and documentation."
            }
            format_info.delete("1.0", "end")
            format_info.insert("1.0", format_descriptions.get(format_var.get(), ""))
            format_info.configure(state="disabled")
        
        # Update info when format changes
        csv_radio.configure(command=update_format_info)
        json_radio.configure(command=update_format_info)
        pdf_radio.configure(command=update_format_info)
        update_format_info()  # Set initial info
        
        # Buttons frame
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", pady=(20, 10))
        
        def export_results():
            selected_format = format_var.get()
            search_term = self.search_entry.get().strip() or "search_results"
            
            # File dialog
            file_extensions = {
                "csv": [("CSV files", "*.csv")],
                "json": [("JSON files", "*.json")],
                "pdf": [("PDF files", "*.pdf")]
            }
            
            default_filename = f"mcp_search_{search_term}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{selected_format}"
            
            file_path = filedialog.asksaveasfilename(
                title=f"Save {selected_format.upper()} Export",
                defaultextension=f".{selected_format}",
                filetypes=file_extensions[selected_format],
                initialvalue=default_filename
            )
            
            if file_path:
                try:
                    export_manager = ExportManager()
                    success = export_manager.export_results(
                        self.current_results,
                        search_term,
                        selected_format,
                        file_path
                    )
                    
                    if success:
                        export_window.destroy()
                        
                        # Show success with option to open file
                        result = messagebox.askyesno(
                            "Export Complete",
                            f"Results exported successfully!\n\n"
                            f"File: {file_path}\n"
                            f"Format: {selected_format.upper()}\n"
                            f"Results: {total_results}\n\n"
                            f"Would you like to open the exported file?"
                        )
                        
                        if result:
                            try:
                                import subprocess
                                subprocess.run(['start', file_path], shell=True)
                            except Exception as e:
                                self.show_error(f"Could not open file: {e}")
                    else:
                        self.show_error("Export failed. Please check the file path and try again.")
                        
                except Exception as e:
                    self.show_error(f"Export error: {str(e)}")
        
        export_btn = ctk.CTkButton(
            button_frame,
            text="📥 Export Results",
            command=export_results,
            width=150,
            height=35,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        export_btn.pack(side="left", padx=(20, 10), pady=10)
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=export_window.destroy,
            width=100,
            height=35,
            fg_color="gray",
            hover_color="darkgray"
        )
        cancel_btn.pack(side="right", padx=(10, 20), pady=10)
    
    def show_settings(self):
        """Show settings dialog"""
        # Create settings window
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("Settings")
        settings_window.geometry("600x500")
        settings_window.transient(self)
        settings_window.grab_set()
        
        # Center on parent
        settings_window.geometry(f"+{self.winfo_x() + 100}+{self.winfo_y() + 100}")
        
        # Settings content
        settings_frame = ctk.CTkScrollableFrame(settings_window)
        settings_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # API Keys section
        api_label = ctk.CTkLabel(settings_frame, text="API Keys", font=ctk.CTkFont(size=16, weight="bold"))
        api_label.pack(pady=(0, 10), anchor="w")
        
        # GitHub API Key
        github_frame = ctk.CTkFrame(settings_frame)
        github_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(github_frame, text="GitHub API Key:").pack(side="left", padx=(10, 5), pady=10)
        github_entry = ctk.CTkEntry(github_frame, placeholder_text="Enter GitHub API key", width=300)
        github_entry.pack(side="left", padx=(0, 10), pady=10)
        github_entry.insert(0, self.config_manager.get_api_key('github_api_key'))
        
        # Cache settings
        cache_label = ctk.CTkLabel(settings_frame, text="Cache Settings", font=ctk.CTkFont(size=16, weight="bold"))
        cache_label.pack(pady=(20, 10), anchor="w")
        
        cache_info = ctk.CTkLabel(
            settings_frame,
            text="Cache settings can be configured in the config/conf.ini file.\n"
                 "Current cache location: cache/ directory",
            font=ctk.CTkFont(size=12)
        )
        cache_info.pack(pady=5, anchor="w")
        
        # Clear cache button
        clear_cache_btn = ctk.CTkButton(
            settings_frame,
            text="Clear Cache",
            command=self.clear_cache,
            width=150
        )
        clear_cache_btn.pack(pady=10, anchor="w")
        
        # Save button
        def save_settings():
            # Save API keys
            if 'API_KEYS' not in self.config_manager.config:
                self.config_manager.config.add_section('API_KEYS')
            
            self.config_manager.config['API_KEYS']['github_api_key'] = github_entry.get()
            self.config_manager.save_config()
            
            settings_window.destroy()
            self.show_info("Settings saved successfully!")
        
        save_btn = ctk.CTkButton(
            settings_window,
            text="Save Settings",
            command=save_settings,
            width=150,
            height=35
        )
        save_btn.pack(side="bottom", pady=20)
    
    def clear_cache(self):
        """Clear search cache"""
        try:
            cache_dir = Config.CACHE_DIR
            if os.path.exists(cache_dir):
                for file in os.listdir(cache_dir):
                    file_path = os.path.join(cache_dir, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
            
            self.show_info("Cache cleared successfully!")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            self.show_error(f"Error clearing cache: {e}")
    
    def show_error(self, message: str):
        """Show error message"""
        logger.error(message)
        messagebox.showerror("Error", message)
    
    def show_info(self, message: str):
        """Show info message"""
        logger.info(message)
        messagebox.showinfo("Information", message)

def main():
    """Main application entry point"""
    try:
        # Set appearance mode
        ctk.set_appearance_mode("system")  # "system", "dark", "light"
        
        # Create and run application
        app = MCPSearchGUI()
        app.mainloop()
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Application error: {e}\nTraceback:\n{error_details}")
        print(f"Full error traceback:\n{error_details}")
        messagebox.showerror("Application Error", f"An error occurred: {e}\nCheck console for details.")

if __name__ == "__main__":
    main()
