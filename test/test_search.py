#!/usr/bin/env python3
"""
Test script to verify MCP Search functionality without GUI
Tests the core search and parsing functionality
"""

import sys
import os
import configparser
import requests
import logging
from pathlib import Path
from bs4 import BeautifulSoup
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleConfigManager:
    """Simplified config manager for testing"""
    def __init__(self, config_file="config/conf.ini"):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

    def get_source_config(self, source_id):
        section = f"SOURCE_{source_id}"
        if section in self.config:
            return dict(self.config[section])
        return None

    def get_api_key(self, key_name):
        return self.config.get('API_KEYS', key_name, fallback='')

def test_url_param_search(source_id, query="memory"):
    """Test a single url_param source"""
    config_mgr = SimpleConfigManager()
    source_config = config_mgr.get_source_config(source_id)

    if not source_config:
        return {"error": f"Source {source_id} not found"}

    search_method = source_config.get('search_method', '')
    if search_method != 'url_param':
        return {"error": f"Source uses {search_method}, not url_param"}

    # Build search URL
    search_endpoint = source_config.get('search_endpoint', '')
    search_url = search_endpoint.replace('{query}', query)

    logger.info(f"Testing {source_id}: {search_url}")

    try:
        # Make request
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(search_url, headers=headers, timeout=30)
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Count potential result elements
        result_counts = {}

        # Try different selectors
        selectors = [
            ('server-cards', 'div[data-test-id*="mcp-server"]'),
            ('server-links', 'a[href*="/servers/"]'),
            ('result-cards', '.result-card, .search-result, .server-card'),
            ('all-links', 'a[href]'),
        ]

        for name, selector in selectors:
            elements = soup.select(selector)
            result_counts[name] = len(elements)

        # Get sample URLs
        server_links = soup.find_all('a', href=lambda x: x and '/servers/' in x)
        sample_urls = [link.get('href') for link in server_links[:5]]

        return {
            "status": "success",
            "url": search_url,
            "response_code": response.status_code,
            "response_length": len(response.text),
            "result_counts": result_counts,
            "sample_urls": sample_urls,
            "has_data_test_id": bool(soup.find_all(attrs={"data-test-id": True}))
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "url": search_url
        }

def test_awesome_list(source_id, query="memory"):
    """Test a single awesome_list source"""
    config_mgr = SimpleConfigManager()
    source_config = config_mgr.get_source_config(source_id)

    if not source_config:
        return {"error": f"Source {source_id} not found"}

    search_method = source_config.get('search_method', '')
    if search_method != 'awesome_list':
        return {"error": f"Source uses {search_method}, not awesome_list"}

    repo = source_config.get('search_repo', '')
    search_file = source_config.get('search_file', 'README.md')

    logger.info(f"Testing {source_id}: {repo}/{search_file}")

    try:
        # Get GitHub token
        github_token = config_mgr.get_api_key('github_api_key')
        headers = {'User-Agent': 'MCP_Search_Test/1.0'}
        if github_token:
            headers['Authorization'] = f'token {github_token}'

        # Fetch README content
        content_url = f"https://api.github.com/repos/{repo}/contents/{search_file}"
        response = requests.get(content_url, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()

        # Decode base64 content
        import base64
        if 'content' in data:
            readme_content = base64.b64decode(data['content']).decode('utf-8')

            # Count markdown links
            import re
            links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', readme_content)

            # Filter for query
            matching_links = [link for link in links if query.lower() in link[0].lower() or query.lower() in link[1].lower()]

            return {
                "status": "success",
                "repo": repo,
                "file": search_file,
                "content_length": len(readme_content),
                "total_links": len(links),
                "matching_links": len(matching_links),
                "sample_matches": matching_links[:3] if matching_links else []
            }
        else:
            return {"status": "error", "error": "No content in response"}

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "repo": repo
        }

def main():
    """Run tests on key sources"""
    print("=" * 80)
    print("MCP SEARCH - FUNCTIONALITY TEST")
    print("=" * 80)

    # Test url_param sources
    print("\n### Testing URL_PARAM Sources ###\n")
    url_param_sources = ['pulsemcp.com', 'mcpservers.org', 'mcpserverfinder.com']

    url_param_results = {}
    for source in url_param_sources:
        result = test_url_param_search(source)
        url_param_results[source] = result

        if result.get('status') == 'success':
            print(f"✓ {source}")
            print(f"  URL: {result['url']}")
            print(f"  Response: {result['response_code']} ({result['response_length']} bytes)")
            print(f"  Result counts: {result['result_counts']}")
            print(f"  Sample URLs: {result['sample_urls'][:2]}")
        else:
            print(f"✗ {source}")
            print(f"  Error: {result.get('error', 'Unknown error')}")
        print()

    # Test awesome_list sources
    print("\n### Testing AWESOME_LIST Sources ###\n")
    awesome_sources = [
        'github_modelcontextprotocol_servers',
        'github_punkpeye_awesome_mcp_servers',
        'github_serp_ai_awesome_mcp_servers'
    ]

    awesome_results = {}
    for source in awesome_sources:
        result = test_awesome_list(source)
        awesome_results[source] = result

        if result.get('status') == 'success':
            print(f"✓ {source}")
            print(f"  Repo: {result['repo']}")
            print(f"  Content: {result['content_length']} chars")
            print(f"  Links: {result['total_links']} total, {result['matching_links']} matching")
            if result.get('sample_matches'):
                print(f"  Samples: {result['sample_matches'][0][0][:40]}...")
        else:
            print(f"✗ {source}")
            print(f"  Error: {result.get('error', 'Unknown error')}")
        print()

    # Save results
    results = {
        "url_param": url_param_results,
        "awesome_list": awesome_results
    }

    output_file = "test_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Results saved to {output_file}")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    url_success = sum(1 for r in url_param_results.values() if r.get('status') == 'success')
    awesome_success = sum(1 for r in awesome_results.values() if r.get('status') == 'success')

    print(f"URL_PARAM sources: {url_success}/{len(url_param_sources)} successful")
    print(f"AWESOME_LIST sources: {awesome_success}/{len(awesome_sources)} successful")

if __name__ == "__main__":
    main()
