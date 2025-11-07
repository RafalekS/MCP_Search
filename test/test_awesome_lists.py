#!/usr/bin/env python3
"""
Comprehensive test of all awesome_list GitHub sources
"""

import sys
import configparser
import requests
import logging
import base64
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# GitHub sources from config
AWESOME_LIST_SOURCES = [
    # MCP Servers (7)
    'github_modelcontextprotocol_servers',
    'github_punkpeye_awesome_mcp_servers',
    'github_serp_ai_awesome_mcp_servers',
    'github_pipedreamhq_awesome_mcp_servers',
    'github_docker_mcp_servers',
    'github_evalstate_hf_mcp_server',
    'github_milisp_mcp_linker',
    # DXT Tools (2)
    'github_samihalawa_awesome_claude_dxt',
    'github_milisp_awesome_claude_dxt',
    # AI Agents (2)
    'github_ai_agent_hub_mcp_marketplace',
    'github_ai_agent_hub_ai_agent_marketplace_index_mcp',
    # Commands (3)
    'github_hesreallyhim_awesome_claude_code',
    'github_qdhenry_claude_command_suite',
    'github_zebbern_claude_code_guide',
    # AI Tools (2)
    'github_shubhamsaboo_awesome_llm_apps',
    'github_sindresorhus_awesome',
]

def get_source_config(source_id):
    """Get source configuration"""
    config = configparser.ConfigParser()
    config.read('config/conf.ini')

    section = f"SOURCE_{source_id}"
    if section in config:
        return dict(config[section])
    return None

def test_awesome_source(source_id):
    """Test a single awesome_list source"""
    source_config = get_source_config(source_id)

    if not source_config:
        return {"status": "error", "error": "Source not found in config"}

    repo = source_config.get('search_repo', '')
    search_file = source_config.get('search_file', 'README.md')

    if not repo:
        return {"status": "error", "error": "No search_repo configured"}

    try:
        # Get GitHub API
        config = configparser.ConfigParser()
        config.read('config/conf.ini')
        github_token = config.get('API_KEYS', 'github_api_key', fallback='')

        headers = {'User-Agent': 'MCP_Search_Test/1.0'}
        if github_token:
            headers['Authorization'] = f'token {github_token}'

        # Fetch README
        content_url = f"https://api.github.com/repos/{repo}/contents/{search_file}"
        response = requests.get(content_url, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()

        if 'content' in data:
            readme_content = base64.b64decode(data['content']).decode('utf-8')

            # Count markdown links
            import re
            links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', readme_content)

            # Filter out navigation links
            skip_patterns = ['table of contents', 'contributing', 'license', 'readme', 'back to top']
            tool_links = [
                link for link in links
                if not any(skip in link[0].lower() for skip in skip_patterns)
                and len(link[0]) > 2
                and not link[1].startswith('#')  # Skip anchor links
            ]

            return {
                "status": "success",
                "repo": repo,
                "file": search_file,
                "content_length": len(readme_content),
                "total_links": len(links),
                "tool_links": len(tool_links),
                "sample_tools": [f"{link[0][:40]}... → {link[1][:50]}..." for link in tool_links[:3]]
            }
        else:
            return {"status": "error", "error": "No content in response"}

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return {"status": "error", "error": f"Repository or file not found: {repo}/{search_file}"}
        elif e.response.status_code == 401:
            return {"status": "error", "error": "GitHub authentication failed - check API token"}
        else:
            return {"status": "error", "error": f"HTTP {e.response.status_code}: {str(e)}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def main():
    """Test all awesome_list sources"""
    print("=" * 80)
    print("COMPREHENSIVE AWESOME_LIST SOURCES TEST")
    print("=" * 80)

    results = {}
    success_count = 0
    error_count = 0

    for source_id in AWESOME_LIST_SOURCES:
        print(f"\nTesting {source_id}...")
        result = test_awesome_source(source_id)
        results[source_id] = result

        if result['status'] == 'success':
            success_count += 1
            print(f"  ✓ SUCCESS")
            print(f"    Repo: {result['repo']}")
            print(f"    Content: {result['content_length']:,} chars")
            print(f"    Links: {result['total_links']} total, {result['tool_links']} tools/servers")
            if result['sample_tools']:
                print(f"    Samples:")
                for sample in result['sample_tools']:
                    print(f"      - {sample}")
        else:
            error_count += 1
            print(f"  ✗ ERROR: {result['error']}")

    # Save results
    output_file = "awesome_list_test_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total sources tested: {len(AWESOME_LIST_SOURCES)}")
    print(f"✓ Successful: {success_count}")
    print(f"✗ Errors: {error_count}")
    print(f"Success rate: {success_count/len(AWESOME_LIST_SOURCES)*100:.1f}%")
    print(f"\nResults saved to: {output_file}")

    # Categorize errors
    if error_count > 0:
        print("\nERROR BREAKDOWN:")
        error_types = {}
        for source_id, result in results.items():
            if result['status'] == 'error':
                error_msg = result['error']
                if '404' in error_msg or 'not found' in error_msg.lower():
                    error_type = "Repository/File Not Found (404)"
                elif '401' in error_msg or 'authentication' in error_msg.lower():
                    error_type = "Authentication Failed (401)"
                else:
                    error_type = "Other Error"

                if error_type not in error_types:
                    error_types[error_type] = []
                error_types[error_type].append(source_id)

        for error_type, sources in error_types.items():
            print(f"  {error_type}: {len(sources)} sources")
            for source in sources:
                print(f"    - {source}")

if __name__ == "__main__":
    main()
