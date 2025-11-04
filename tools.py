"""
MCP Search Tools - Source Validation and Export Functionality

This module contains the tools for validating sources and exporting search results.
Separated from the main application for better code organization.
"""

import requests
import json
import csv
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from urllib.parse import quote
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class SourceValidator:
    """Comprehensive source validation and testing framework"""
    
    def __init__(self, config_manager, debug_dir: str = "debug_results"):
        self.config_manager = config_manager
        self.debug_dir = Path(debug_dir)
        self.validation_dir = self.debug_dir / "validation"
        self.validation_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup validation logger
        self.validation_log_path = self.validation_dir / f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.logger = logging.getLogger('source_validator')
        self.logger.setLevel(logging.INFO)
        
        # Create file handler for validation log
        handler = logging.FileHandler(self.validation_log_path, encoding='utf-8')
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # Create session for testing
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MCP_Search_Validator/1.0 (Testing)'
        })
    
    def validate_all_sources(self, progress_callback=None) -> Dict[str, Dict]:
        """Validate all configured sources comprehensively"""
        self.logger.info("=== STARTING COMPREHENSIVE SOURCE VALIDATION ===")
        
        categories = self.config_manager.get_categories()
        all_results = {}
        total_sources = sum(len(sources) for sources in categories.values())
        current_source = 0
        
        for category, sources in categories.items():
            if progress_callback:
                progress_callback(f"Validating category: {category}", current_source, total_sources)
            
            category_results = {}
            
            for source_id in sources:
                current_source += 1
                if progress_callback:
                    progress_callback(f"Testing {source_id}...", current_source, total_sources)
                
                try:
                    validation_result = self.validate_source(source_id)
                    category_results[source_id] = validation_result
                    
                    # Log summary
                    status = "PASS" if validation_result['overall_status'] == 'working' else "FAIL"
                    self.logger.info(f"{status} {source_id}: {validation_result['summary']}")
                    
                except Exception as e:
                    self.logger.error(f"CRITICAL ERROR validating {source_id}: {e}")
                    category_results[source_id] = {
                        'overall_status': 'error',
                        'summary': f'Critical validation error: {e}',
                        'connectivity': False,
                        'functionality': False,
                        'parsing': False,
                        'error': str(e)
                    }
            
            all_results[category] = category_results
        
        # Generate comprehensive report
        report_path = self.generate_validation_report(all_results)
        
        self.logger.info("=== VALIDATION COMPLETE ===")
        self.logger.info(f"Report saved to: {report_path}")
        
        return all_results
    
    def validate_source(self, source_id: str, test_query: str = "memory") -> Dict[str, Any]:
        """Comprehensive validation of a single source"""
        source_config = self.config_manager.get_source_config(source_id)
        if not source_config:
            return {
                'overall_status': 'error',
                'summary': 'Source configuration not found',
                'connectivity': False,
                'functionality': False,
                'parsing': False,
                'error': 'Missing configuration'
            }
        
        source_name = source_config.get('name', source_id)
        base_url = source_config.get('url', '')
        search_method = source_config.get('search_method', 'scrape')
        
        self.logger.info(f"\n--- VALIDATING: {source_name} ({source_id}) ---")
        
        validation_result = {
            'source_id': source_id,
            'source_name': source_name,
            'base_url': base_url,
            'search_method': search_method,
            'connectivity': False,
            'functionality': False,
            'parsing': False,
            'overall_status': 'failed',
            'summary': '',
            'details': {},
            'recommendations': []
        }
        
        # Test 1: Connectivity Test
        connectivity_result = self._test_connectivity(source_config)
        validation_result['connectivity'] = connectivity_result['success']
        validation_result['details']['connectivity'] = connectivity_result
        
        if not connectivity_result['success']:
            validation_result['summary'] = f"Connectivity failed: {connectivity_result['error']}"
            validation_result['recommendations'].append("Check URL and network connectivity")
            return validation_result
        
        # Test 2: Search Functionality Test
        functionality_result = self._test_search_functionality(source_config, test_query)
        validation_result['functionality'] = functionality_result['success']
        validation_result['details']['functionality'] = functionality_result
        
        if not functionality_result['success']:
            validation_result['summary'] = f"Search functionality failed: {functionality_result['error']}"
            validation_result['recommendations'].extend(functionality_result.get('recommendations', []))
            return validation_result
        
        # Test 3: Result Parsing Test
        parsing_result = self._test_result_parsing(source_config, test_query, functionality_result.get('raw_response'))
        validation_result['parsing'] = parsing_result['success']
        validation_result['details']['parsing'] = parsing_result
        
        # Determine overall status
        if validation_result['connectivity'] and validation_result['functionality'] and validation_result['parsing']:
            validation_result['overall_status'] = 'working'
            validation_result['summary'] = f"All tests passed - found {parsing_result.get('result_count', 0)} results"
        else:
            validation_result['overall_status'] = 'partial'
            validation_result['summary'] = f"Partial functionality - parsing issues"
            validation_result['recommendations'].extend(parsing_result.get('recommendations', []))
        
        return validation_result
    
    def _test_connectivity(self, source_config: Dict[str, str]) -> Dict[str, Any]:
        """Test basic connectivity to source"""
        base_url = source_config.get('url', '')
        if not base_url:
            return {'success': False, 'error': 'No URL configured', 'status_code': None}
        
        try:
            response = self.session.get(base_url, timeout=10)
            success = response.status_code == 200
            
            return {
                'success': success,
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'error': None if success else f"HTTP {response.status_code}"
            }
        except requests.RequestException as e:
            return {
                'success': False,
                'status_code': None,
                'error': str(e)
            }
    
    def _test_search_functionality(self, source_config: Dict[str, str], test_query: str) -> Dict[str, Any]:
        """Test search functionality based on configured method"""
        search_method = source_config.get('search_method', 'scrape')
        
        try:
            if search_method == 'url_param':
                return self._test_url_param_search(source_config, test_query)
            elif search_method == 'api':
                return self._test_api_search(source_config, test_query)
            elif search_method == 'github_api':
                return self._test_github_api_search(source_config, test_query)
            elif search_method == 'awesome_list':
                return self._test_awesome_list_search(source_config, test_query)
            elif search_method == 'scrape':
                return self._test_scrape_search(source_config, test_query)
            else:
                return {
                    'success': False,
                    'error': f'Unknown search method: {search_method}',
                    'recommendations': ['Update search_method to valid value: url_param, api, github_api, awesome_list, scrape']
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Search test failed: {e}',
                'recommendations': ['Check search configuration and endpoint']
            }
    
    def _test_url_param_search(self, source_config: Dict[str, str], test_query: str) -> Dict[str, Any]:
        """Test URL parameter search method"""
        search_endpoint = source_config.get('search_endpoint', '')
        if not search_endpoint:
            return {
                'success': False,
                'error': 'No search_endpoint configured for url_param method',
                'recommendations': ['Add search_endpoint = https://site.com/search?q={query}']
            }
        
        try:
            search_url = search_endpoint.format(query=quote(test_query))
            response = self.session.get(search_url, timeout=15)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'search_url': search_url,
                    'status_code': response.status_code,
                    'content_length': len(response.text),
                    'raw_response': response.text
                }
            else:
                return {
                    'success': False,
                    'error': f'Search returned HTTP {response.status_code}',
                    'search_url': search_url,
                    'recommendations': ['Check search endpoint URL and parameters']
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'URL param search failed: {e}',
                'recommendations': ['Verify search_endpoint URL format and connectivity']
            }
    
    def _test_api_search(self, source_config: Dict[str, str], test_query: str) -> Dict[str, Any]:
        """Test API search method"""
        search_endpoint = source_config.get('search_endpoint', '')
        if not search_endpoint:
            return {
                'success': False,
                'error': 'No search_endpoint configured for api method',
                'recommendations': ['Add search_endpoint for API']
            }
        
        try:
            if '{query}' in search_endpoint:
                api_url = search_endpoint.format(query=quote(test_query))
                response = self.session.get(api_url, timeout=15)
            else:
                params = {'q': test_query}
                response = self.session.get(search_endpoint, params=params, timeout=15)
            
            if response.status_code == 200:
                try:
                    json_data = response.json()
                    return {
                        'success': True,
                        'api_url': response.url,
                        'status_code': response.status_code,
                        'response_type': 'json',
                        'raw_response': response.text
                    }
                except json.JSONDecodeError:
                    return {
                        'success': True,
                        'api_url': response.url,
                        'status_code': response.status_code,
                        'response_type': 'text',
                        'raw_response': response.text,
                        'warning': 'Response is not valid JSON'
                    }
            else:
                return {
                    'success': False,
                    'error': f'API returned HTTP {response.status_code}',
                    'api_url': response.url,
                    'recommendations': ['Check API endpoint and authentication']
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'API search failed: {e}',
                'recommendations': ['Verify API endpoint and parameters']
            }
    
    def _test_github_api_search(self, source_config: Dict[str, str], test_query: str) -> Dict[str, Any]:
        """Test GitHub API search method"""
        repo = source_config.get('search_repo', '')
        if not repo:
            return {
                'success': False,
                'error': 'No search_repo configured for github_api method',
                'recommendations': ['Add search_repo = owner/repository']
            }
        
        try:
            github_token = self.config_manager.get_api_key('github_api_key')
            headers = {}
            if github_token:
                headers['Authorization'] = f'token {github_token}'
            
            search_url = "https://api.github.com/search/code"
            params = {
                'q': f'{test_query} repo:{repo}',
                'sort': 'indexed',
                'order': 'desc'
            }
            
            response = self.session.get(search_url, params=params, headers=headers, timeout=15)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'api_url': response.url,
                    'status_code': response.status_code,
                    'raw_response': response.text
                }
            elif response.status_code == 401:
                return {
                    'success': False,
                    'error': 'GitHub API authentication failed',
                    'recommendations': ['Check GitHub API key in settings', 'Ensure API key has repo access permissions']
                }
            else:
                return {
                    'success': False,
                    'error': f'GitHub API returned HTTP {response.status_code}',
                    'recommendations': ['Check repository name and permissions']
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'GitHub API search failed: {e}',
                'recommendations': ['Verify GitHub API configuration']
            }
    
    def _test_awesome_list_search(self, source_config: Dict[str, str], test_query: str) -> Dict[str, Any]:
        """Test awesome list search method"""
        repo = source_config.get('search_repo', '')
        search_file = source_config.get('search_file', 'README.md')
        
        if not repo:
            return {
                'success': False,
                'error': 'No search_repo configured for awesome_list method',
                'recommendations': ['Add search_repo = owner/repository']
            }
        
        try:
            github_token = self.config_manager.get_api_key('github_api_key')
            headers = {}
            if github_token:
                headers['Authorization'] = f'token {github_token}'
            
            content_url = f"https://api.github.com/repos/{repo}/contents/{search_file}"
            response = self.session.get(content_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'content' in data:
                        import base64
                        readme_content = base64.b64decode(data['content']).decode('utf-8')
                        return {
                            'success': True,
                            'api_url': response.url,
                            'status_code': response.status_code,
                            'content_length': len(readme_content),
                            'raw_response': readme_content[:5000]  # First 5000 chars for validation
                        }
                    else:
                        return {
                            'success': False,
                            'error': 'No content found in repository file',
                            'recommendations': [f'Check if {search_file} exists in {repo}']
                        }
                except json.JSONDecodeError:
                    return {
                        'success': False,
                        'error': 'Invalid JSON response from GitHub API',
                        'recommendations': ['Check repository and file path']
                    }
            elif response.status_code == 401:
                return {
                    'success': False,
                    'error': 'GitHub API authentication failed',
                    'recommendations': ['Check GitHub API key in settings']
                }
            elif response.status_code == 404:
                return {
                    'success': False,
                    'error': f'Repository or file not found: {repo}/{search_file}',
                    'recommendations': ['Verify repository name and file path']
                }
            else:
                return {
                    'success': False,
                    'error': f'GitHub API returned HTTP {response.status_code}',
                    'recommendations': ['Check repository access permissions']
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Awesome list search failed: {e}',
                'recommendations': ['Verify GitHub API configuration and repository access']
            }
    
    def _test_scrape_search(self, source_config: Dict[str, str], test_query: str) -> Dict[str, Any]:
        """Test scrape search method"""
        base_url = source_config.get('url', '')
        if not base_url:
            return {
                'success': False,
                'error': 'No URL configured for scrape method',
                'recommendations': ['Add url = https://site.com/']
            }
        
        try:
            response = self.session.get(base_url, timeout=15)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'base_url': base_url,
                    'status_code': response.status_code,
                    'content_length': len(response.text),
                    'raw_response': response.text
                }
            else:
                return {
                    'success': False,
                    'error': f'Scraping returned HTTP {response.status_code}',
                    'base_url': base_url,
                    'recommendations': ['Check URL accessibility']
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Scraping failed: {e}',
                'recommendations': ['Verify URL and connectivity']
            }
    
    def _test_result_parsing(self, source_config: Dict[str, str], test_query: str, raw_response: str = None) -> Dict[str, Any]:
        """Test result parsing functionality"""
        if not raw_response:
            return {
                'success': False,
                'error': 'No response content to parse',
                'result_count': 0
            }
        
        try:
            # Use existing parsing logic to test result extraction
            from bs4 import BeautifulSoup
            
            search_method = source_config.get('search_method', 'scrape')
            source_name = source_config.get('name', 'Test')
            base_url = source_config.get('url', '')
            
            if search_method in ['url_param', 'scrape']:
                soup = BeautifulSoup(raw_response, 'html.parser')
                
                # Test site-specific parsing
                if 'pulsemcp.com' in base_url:
                    server_cards = soup.find_all('div', {'data-test-id': lambda x: x and 'mcp-server-grid-card' in x})
                    result_count = len(server_cards)
                elif 'mcpservers.org' in base_url:
                    server_links = soup.find_all('a', href=lambda x: x and '/servers/' in x)
                    result_count = len(server_links)
                elif 'mcpserverfinder.com' in base_url:
                    # Try multiple selectors
                    selectors = ['.server-card', '.result-item', '.search-result']
                    result_count = 0
                    for selector in selectors:
                        elements = soup.select(selector)
                        if elements:
                            result_count = len(elements)
                            break
                else:
                    # Generic parsing
                    all_links = soup.find_all('a', href=True)
                    result_count = len([link for link in all_links if len(link.get_text(strip=True)) > 3])
                
                # Check if results make sense
                has_meaningful_content = result_count > 0
                has_too_many_results = result_count > 500  # Probably parsing navigation
                
                if has_meaningful_content and not has_too_many_results:
                    return {
                        'success': True,
                        'result_count': result_count,
                        'parsing_method': 'site_specific' if 'pulsemcp.com' in base_url or 'mcpservers.org' in base_url else 'generic'
                    }
                elif has_too_many_results:
                    return {
                        'success': False,
                        'error': f'Too many results ({result_count}) - likely parsing navigation',
                        'result_count': result_count,
                        'recommendations': ['Improve CSS selectors to target actual results', 'Add better filtering logic']
                    }
                else:
                    return {
                        'success': False,
                        'error': 'No meaningful results found in response',
                        'result_count': 0,
                        'recommendations': ['Check if search returns results', 'Improve parsing selectors', 'Verify search endpoint']
                    }
            
            elif search_method == 'api':
                try:
                    data = json.loads(raw_response)
                    # Basic validation that it's a reasonable API response
                    if isinstance(data, dict) and any(key in data for key in ['results', 'data', 'items']):
                        return {
                            'success': True,
                            'result_count': 'unknown',
                            'parsing_method': 'api_json'
                        }
                    else:
                        return {
                            'success': False,
                            'error': 'API response does not contain expected result structure',
                            'recommendations': ['Verify API response format', 'Update parsing logic']
                        }
                except json.JSONDecodeError:
                    return {
                        'success': False,
                        'error': 'API response is not valid JSON',
                        'recommendations': ['Check API endpoint returns JSON', 'Consider changing to url_param method']
                    }
            
            elif search_method in ['github_api', 'awesome_list']:
                if search_method == 'github_api':
                    try:
                        data = json.loads(raw_response)
                        if 'items' in data:
                            return {
                                'success': True,
                                'result_count': len(data['items']),
                                'parsing_method': 'github_api'
                            }
                        else:
                            return {
                                'success': False,
                                'error': 'GitHub API response missing items',
                                'recommendations': ['Verify search query and repository access']
                            }
                    except json.JSONDecodeError:
                        return {
                            'success': False,
                            'error': 'GitHub API response is not valid JSON',
                            'recommendations': ['Check GitHub API configuration']
                        }
                else:  # awesome_list
                    # Check if content contains markdown list items
                    lines = raw_response.split('\n')
                    list_items = [line for line in lines if line.strip().startswith(('- [', '* [', '1. ['))]
                    
                    if list_items:
                        return {
                            'success': True,
                            'result_count': len(list_items),
                            'parsing_method': 'awesome_list_markdown'
                        }
                    else:
                        return {
                            'success': False,
                            'error': 'No markdown list items found in awesome list',
                            'result_count': 0,
                            'recommendations': ['Check if README.md contains list items', 'Verify repository content']
                        }
            
            return {
                'success': False,
                'error': f'Parsing not implemented for method: {search_method}',
                'recommendations': ['Implement parsing logic for this search method']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Parsing test failed: {e}',
                'recommendations': ['Check parsing logic and content format']
            }
    
    def generate_validation_report(self, validation_results: Dict[str, Dict]) -> str:
        """Generate comprehensive HTML validation report"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        report_file = self.validation_dir / f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        # Calculate summary statistics
        total_sources = sum(len(category_results) for category_results in validation_results.values())
        working_sources = 0
        partial_sources = 0
        failed_sources = 0
        
        for category_results in validation_results.values():
            for result in category_results.values():
                status = result.get('overall_status', 'failed')
                if status == 'working':
                    working_sources += 1
                elif status == 'partial':
                    partial_sources += 1
                else:
                    failed_sources += 1
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>MCP Search - Source Validation Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .summary {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .stat-box {{ text-align: center; padding: 15px; border-radius: 8px; min-width: 120px; }}
                .working {{ background: #d4edda; color: #155724; }}
                .partial {{ background: #fff3cd; color: #856404; }}
                .failed {{ background: #f8d7da; color: #721c24; }}
                .category {{ margin: 20px 0; border: 1px solid #ddd; border-radius: 8px; }}
                .category-header {{ background: #007bff; color: white; padding: 15px; font-weight: bold; }}
                .source {{ margin: 10px 0; padding: 15px; border-left: 4px solid #ddd; }}
                .source.working {{ border-left-color: #28a745; background: #f8fff9; }}
                .source.partial {{ border-left-color: #ffc107; background: #fffbf0; }}
                .source.failed {{ border-left-color: #dc3545; background: #fff5f5; }}
                .source-name {{ font-weight: bold; font-size: 16px; }}
                .source-url {{ color: #666; font-size: 12px; }}
                .tests {{ margin: 10px 0; }}
                .test {{ display: inline-block; margin: 2px 5px; padding: 3px 8px; border-radius: 3px; font-size: 11px; }}
                .test.pass {{ background: #28a745; color: white; }}
                .test.fail {{ background: #dc3545; color: white; }}
                .details {{ margin: 10px 0; font-size: 12px; color: #666; }}
                .recommendations {{ margin: 10px 0; }}
                .recommendations ul {{ margin: 5px 0; padding-left: 20px; }}
                .recommendations li {{ margin: 2px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>MCP Search - Source Validation Report</h1>
                    <p>Generated: {timestamp}</p>
                    <p>Total Sources Tested: {total_sources}</p>
                </div>
                
                <div class="summary">
                    <div class="stat-box working">
                        <h3>{working_sources}</h3>
                        <p>Working</p>
                    </div>
                    <div class="stat-box partial">
                        <h3>{partial_sources}</h3>
                        <p>Partial</p>
                    </div>
                    <div class="stat-box failed">
                        <h3>{failed_sources}</h3>
                        <p>Failed</p>
                    </div>
                </div>
        """
        
        # Add category sections
        for category, category_results in validation_results.items():
            display_category = category.replace('_', ' ').title()
            html_content += f"""
                <div class="category">
                    <div class="category-header">{display_category} ({len(category_results)} sources)</div>
            """
            
            for source_id, result in category_results.items():
                status = result.get('overall_status', 'failed')
                source_name = result.get('source_name', source_id)
                base_url = result.get('base_url', 'No URL')
                summary = result.get('summary', 'No summary')
                
                # Test status indicators
                connectivity = result.get('connectivity', False)
                functionality = result.get('functionality', False)
                parsing = result.get('parsing', False)
                
                html_content += f"""
                    <div class="source {status}">
                        <div class="source-name">{source_name}</div>
                        <div class="source-url">{base_url}</div>
                        <div class="tests">
                            <span class="test {'pass' if connectivity else 'fail'}">Connectivity</span>
                            <span class="test {'pass' if functionality else 'fail'}">Functionality</span>
                            <span class="test {'pass' if parsing else 'fail'}">Parsing</span>
                        </div>
                        <div class="details">{summary}</div>
                """
                
                # Add recommendations if any
                recommendations = result.get('recommendations', [])
                if recommendations:
                    html_content += """
                        <div class="recommendations">
                            <strong>Recommendations:</strong>
                            <ul>
                    """
                    for rec in recommendations:
                        html_content += f"<li>{rec}</li>"
                    html_content += "</ul></div>"
                
                html_content += "</div>"
            
            html_content += "</div>"
        
        html_content += """
            </div>
        </body>
        </html>
        """
        
        # Write report file
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Also save JSON version
        json_file = self.validation_dir / f"validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(validation_results, f, indent=2, ensure_ascii=False)
        
        return str(report_file)


class ExportManager:
    """Manages export of search results to various formats"""
    
    def __init__(self):
        self.supported_formats = ['csv', 'json', 'pdf']
    
    def export_results(self, results: Dict[str, Dict[str, List]], 
                      search_term: str, export_format: str, file_path: str) -> bool:
        """Export search results to specified format"""
        try:
            if export_format.lower() == 'csv':
                return self._export_csv(results, search_term, file_path)
            elif export_format.lower() == 'json':
                return self._export_json(results, search_term, file_path)
            elif export_format.lower() == 'pdf':
                return self._export_pdf(results, search_term, file_path)
            else:
                raise ValueError(f"Unsupported export format: {export_format}")
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False
    
    def _export_csv(self, results: Dict[str, Dict[str, List]], 
                   search_term: str, file_path: str) -> bool:
        """Export results to CSV format"""
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Search Term', 'Category', 'Source', 'Name', 'Description', 'URL', 'GitHub URL', 'Last Updated']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for category, category_results in results.items():
                for source_id, source_results in category_results.items():
                    for result in source_results:
                        writer.writerow({
                            'Search Term': search_term,
                            'Category': category.replace('_', ' ').title(),
                            'Source': result.source,
                            'Name': result.name,
                            'Description': result.description,
                            'URL': result.url,
                            'GitHub URL': result.github_url,
                            'Last Updated': result.last_updated
                        })
        
        return True
    
    def _export_json(self, results: Dict[str, Dict[str, List]], 
                    search_term: str, file_path: str) -> bool:
        """Export results to JSON format"""
        export_data = {
            'search_term': search_term,
            'export_timestamp': datetime.now().isoformat(),
            'total_categories': len(results),
            'total_results': sum(len(source_results) for category_results in results.values() 
                               for source_results in category_results.values()),
            'categories': {}
        }
        
        for category, category_results in results.items():
            category_data = {
                'display_name': category.replace('_', ' ').title(),
                'sources': {}
            }
            
            for source_id, source_results in category_results.items():
                source_data = {
                    'source_name': source_results[0].source if source_results else source_id,
                    'result_count': len(source_results),
                    'results': []
                }
                
                for result in source_results:
                    result_data = {
                        'name': result.name,
                        'description': result.description,
                        'url': result.url,
                        'github_url': result.github_url,
                        'category': result.category,
                        'source': result.source,
                        'last_updated': result.last_updated,
                        'additional_info': result.additional_info
                    }
                    source_data['results'].append(result_data)
                
                category_data['sources'][source_id] = source_data
            
            export_data['categories'][category] = category_data
        
        with open(file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(export_data, jsonfile, indent=2, ensure_ascii=False)
        
        return True
    
    def _export_pdf(self, results: Dict[str, Dict[str, List]], 
                   search_term: str, file_path: str) -> bool:
        """Export results to PDF format"""
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
        except ImportError:
            logger.error("reportlab library not available for PDF export")
            return False
        
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        story.append(Paragraph(f"MCP Search Results: {search_term}", title_style))
        
        # Summary
        total_results = sum(len(source_results) for category_results in results.values() 
                          for source_results in category_results.values())
        summary_text = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>"
        summary_text += f"Search Term: {search_term}<br/>"
        summary_text += f"Total Categories: {len(results)}<br/>"
        summary_text += f"Total Results: {total_results}"
        
        story.append(Paragraph(summary_text, styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Results by category
        for category, category_results in results.items():
            category_display = category.replace('_', ' ').title()
            category_total = sum(len(source_results) for source_results in category_results.values())
            
            # Category header
            category_style = ParagraphStyle(
                'CategoryHeader',
                parent=styles['Heading2'],
                fontSize=14,
                spaceBefore=20,
                spaceAfter=10
            )
            story.append(Paragraph(f"{category_display} ({category_total} results)", category_style))
            
            # Create table for category results
            table_data = [['Name', 'Source', 'Description']]
            
            for source_id, source_results in category_results.items():
                for result in source_results:
                    # Truncate long descriptions
                    description = result.description[:100] + "..." if len(result.description) > 100 else result.description
                    table_data.append([
                        Paragraph(result.name, styles['Normal']),
                        Paragraph(result.source, styles['Normal']),
                        Paragraph(description, styles['Normal'])
                    ])
            
            if len(table_data) > 1:  # More than just header
                table = Table(table_data, colWidths=[2*inch, 1.5*inch, 3*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                story.append(table)
                story.append(Spacer(1, 10))
        
        # Build PDF
        doc.build(story)
        return True
