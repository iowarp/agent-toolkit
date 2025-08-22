#!/usr/bin/env python3
"""
NDP MCP Server for National Data Platform integration.
Provides tools for dataset discovery, details, downloading, and geospatial analysis.
"""

import os
import sys
import json
import asyncio
import tempfile
import logging
from typing import Dict, List, Optional, Any
from fastmcp import FastMCP
from dotenv import load_dotenv

# NDP Client class definition
class NDPClient:
    """Client for interacting with the NDP API."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        import aiohttp
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_organizations(self) -> List[Dict]:
        """Fetch all organizations from the NDP API."""
        async with self.session.get(f"{self.base_url}/organizations") as response:
            response.raise_for_status()
            data = await response.json()
            return data.get("organizations", [])
    
    async def search_datasets(self, query: str, organization: Optional[str] = None, limit: int = 10) -> Dict:
        """Search for datasets in the NDP catalog."""
        params = {"q": query, "limit": limit}
        if organization:
            params["organization"] = organization
        
        async with self.session.get(f"{self.base_url}/search", params=params) as response:
            response.raise_for_status()
            return await response.json()
    
    async def get_dataset_details(self, dataset_id: str) -> Dict:
        """Get complete metadata for a specific dataset."""
        async with self.session.get(f"{self.base_url}/datasets/{dataset_id}") as response:
            response.raise_for_status()
            data = await response.json()
            return data.get("dataset", {})
    
    async def download_file(self, url: str) -> bytes:
        """Download a file from a URL."""
        async with self.session.get(url) as response:
            response.raise_for_status()
            return await response.read()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp: FastMCP = FastMCP("NDPServer")

# NDP API configuration
NDP_BASE_URL = os.getenv("NDP_BASE_URL", "https://api.datacollaboratory.org")

# Search cache for chunking
search_cache = {}
CHUNK_THRESHOLD = 50

# Tool definitions
@mcp.tool(
    name="list_organizations",
    description="List all available organizations from the NDP API"
)
async def list_organizations_tool() -> dict:
    """List all available organizations from the NDP API."""
    return await _list_organizations()

@mcp.tool(
    name="search_datasets",
    description="Search for datasets across the NDP catalog with intelligent chunking"
)
async def search_datasets_tool(
    query: str, 
    organization: Optional[str] = None, 
    limit: int = 10
) -> dict:
    """Search for datasets across the NDP catalog."""
    return await _search_datasets(query, organization, limit)

@mcp.tool(
    name="get_dataset_details",
    description="Retrieve complete metadata for a specific dataset"
)
async def get_dataset_details_tool(dataset_id: str) -> dict:
    """Retrieve complete metadata for a specific dataset."""
    return await _get_dataset_details(dataset_id)

@mcp.tool(
    name="download_dataset_resources",
    description="Download dataset files from dataset resources"
)
async def download_dataset_resources_tool(
    dataset_id: str, 
    resource_types: Optional[List[str]] = None
) -> dict:
    """Download dataset files from dataset resources."""
    return await _download_dataset_resources(dataset_id, resource_types)

@mcp.tool(
    name="download_file_from_url",
    description="Download a file directly from a URL and save it to a specified location"
)
async def download_file_from_url_tool(url: str, output_path: str) -> dict:
    """Download a file directly from a URL and save it to a specified location."""
    return await _download_file_from_url(url, output_path)

@mcp.tool(
    name="analyze_geospatial_data",
    description="Analyze geospatial data from a dataset with comprehensive insights"
)
async def analyze_geospatial_data_tool(dataset_id: str) -> dict:
    """Analyze geospatial data from a dataset."""
    return await _analyze_geospatial_data(dataset_id)

@mcp.tool(
    name="create_multi_series_plot",
    description="Create a multi-series line plot with multiple y-columns against a single x-column, perfect for time series data like GNSS measurements"
)
async def create_multi_series_plot_tool(
    file_path: str,
    x_column: str,
    y_columns: List[str],
    title: str = "Multi-Series Line Plot",
    output_path: str = "multi_series_plot.png",
    figure_size: str = "15x12",
    dpi: int = 300
) -> dict:
    """Create a multi-series line plot with multiple y-columns against a single x-column."""
    return await _create_multi_series_plot(file_path, x_column, y_columns, title, output_path, figure_size, dpi)

@mcp.tool(
    name="create_multi_panel_plot",
    description="Create a multi-panel plot with separate subplots for each y-column, perfect for GNSS time series with East, North, Up components"
)
async def create_multi_panel_plot_tool(
    file_path: str,
    x_column: str,
    y_columns: List[str],
    title: str = "Multi-Panel Time Series Plot",
    output_path: str = "multi_panel_plot.png",
    figure_size: str = "15x12",
    dpi: int = 300,
    layout: str = "vertical"
) -> dict:
    """Create a multi-panel plot with separate subplots for each y-column."""
    return await _create_multi_panel_plot(file_path, x_column, y_columns, title, output_path, figure_size, dpi, layout)

# Helper functions
async def _list_organizations() -> dict:
    """List all available organizations from the NDP API."""
    try:
        async with NDPClient(NDP_BASE_URL) as client:
            organizations = await client.get_organizations()
            
            result_text = "Available NDP Organizations:\n\n"
            for org in organizations:
                result_text += f"- **{org.get('name', 'Unknown')}** (ID: {org.get('id', 'N/A')})\n"
                if org.get('description'):
                    result_text += f"  Description: {org['description']}\n"
                result_text += "\n"
            
        return {"status": "success", "result": result_text, "organizations": organizations}
    except Exception as e:
        logger.error(f"Error listing organizations: {e}")
        return {"status": "error", "error": str(e)}

async def _search_datasets(query: str, organization: Optional[str] = None, limit: int = 10) -> dict:
    """Search for datasets across the NDP catalog with intelligent chunking."""
    try:
        # Check if search exists in cache
        cache_key = f"{query}_{organization}_{limit}"
        if cache_key in search_cache:
            chunk_id = search_cache[cache_key].get('next_chunk', 1)
            return await _get_chunk(cache_key, chunk_id)
            
        async with NDPClient(NDP_BASE_URL) as client:
            search_result = await client.search_datasets(query, organization, limit)
            
            results = search_result.get('result', {}).get('results', [])
            
            if len(results) > CHUNK_THRESHOLD:
                # Implement chunking
                search_cache[cache_key] = {
                    'results': results,
                    'next_chunk': 1,
                    'total_chunks': (len(results) + 9) // 10  # 10 results per chunk
                }
                return await _get_chunk(cache_key, 1)
            else:
                return _format_search_results(results, query, organization)
        
    except Exception as e:
        logger.error(f"Error searching datasets: {e}")
        return {"status": "error", "error": str(e)}

async def _get_chunk(cache_key: str, chunk_id: int) -> dict:
    """Get a specific chunk of search results."""
    if cache_key not in search_cache:
        raise Exception("Search results not found in cache")
    
    cache_data = search_cache[cache_key]
    results = cache_data['results']
    chunk_size = 10
    start_idx = (chunk_id - 1) * chunk_size
    end_idx = start_idx + chunk_size
    
    chunk_results = results[start_idx:end_idx]
    
    result_text = _format_search_results_text(chunk_results, cache_key, chunk_id, cache_data['total_chunks'])
    
    return {"status": "success", "result": result_text, "chunk_id": chunk_id, "total_chunks": cache_data['total_chunks']}

def _format_search_results(results: List[Dict], query: str, organization: Optional[str] = None) -> dict:
    """Format search results for display."""
    result_text = _format_search_results_text(results, None, 1, 1)
    return {"status": "success", "result": result_text, "results": results}

def _format_search_results_text(results: List[Dict], cache_key: Optional[str], chunk_id: int, total_chunks: int) -> str:
    """Format search results as text."""
    result_text = f"Found {len(results)} datasets"
    if total_chunks > 1:
        result_text += f" (Chunk {chunk_id} of {total_chunks})"
    result_text += ":\n\n"
    
    for i, dataset in enumerate(results, 1):
        result_text += f"{i}. **{dataset.get('title', dataset.get('name', 'Untitled'))}**\n"
        result_text += f"   - ID: `{dataset.get('id', 'N/A')}`\n"
        result_text += f"   - Organization: {dataset.get('owner_org', 'Unknown')}\n"
        if dataset.get('notes'):
            result_text += f"   - Description: {dataset['notes'][:100]}...\n"
        result_text += "\n"
    
    if total_chunks > 1 and chunk_id < total_chunks:
        result_text += f"\nTo get the next chunk, use the search_datasets tool with the same parameters.\n"
    
    return result_text

async def _get_dataset_details(dataset_id: str) -> dict:
    """Retrieve complete metadata for a specific dataset."""
    try:
        async with NDPClient(NDP_BASE_URL) as client:
            dataset = await client.get_dataset_details(dataset_id)
            
            if not dataset:
                return {"status": "error", "error": f"Dataset with ID '{dataset_id}' not found."}
            
            result_text = f"**Dataset Details: {dataset.get('title', dataset.get('name', 'Untitled'))}**\n\n"
            result_text += f"- **ID**: `{dataset.get('id', 'N/A')}`\n"
            result_text += f"- **Name**: {dataset.get('name', 'N/A')}\n"
            result_text += f"- **Organization**: {dataset.get('owner_org', 'N/A')}\n"
            result_text += f"- **Created**: {dataset.get('metadata_created', 'N/A')}\n"
            result_text += f"- **Modified**: {dataset.get('metadata_modified', 'N/A')}\n"
            
            if dataset.get('notes'):
                result_text += f"- **Description**: {dataset['notes']}\n"
            
            if dataset.get('tags'):
                result_text += f"- **Tags**: {', '.join([tag['name'] for tag in dataset['tags']])}\n"
            
            # Resources
            resources = dataset.get('resources', [])
            if resources:
                result_text += f"\n**Resources ({len(resources)}):**\n"
                for i, resource in enumerate(resources, 1):
                    result_text += f"{i}. **{resource.get('name', 'Unnamed Resource')}**\n"
                    result_text += f"   - Format: {resource.get('format', 'Unknown')}\n"
                    result_text += f"   - URL: {resource.get('url', 'N/A')}\n"
                    if resource.get('description'):
                        result_text += f"   - Description: {resource['description']}\n"
                    result_text += "\n"
            
            # Extras
            extras = dataset.get('extras', [])
            if extras:
                result_text += "**Additional Metadata:**\n"
                for extra in extras:
                    result_text += f"- {extra.get('key', 'Unknown')}: {extra.get('value', 'N/A')}\n"
            
        return {"status": "success", "result": result_text, "dataset": dataset}
        
    except Exception as e:
        logger.error(f"Error getting dataset details: {e}")
        return {"status": "error", "error": str(e)}

async def _download_file_from_url(url: str, output_path: str) -> dict:
    """Download a file directly from a URL and save it to a specified location."""
    try:
        import aiohttp
        import os
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    
                    with open(output_path, 'wb') as f:
                        f.write(content)
                    
                    file_size = len(content)
                    result_text = f"Successfully downloaded file from {url}\n"
                    result_text += f"Saved to: {output_path}\n"
                    result_text += f"File size: {file_size} bytes"
                    
                    return {
                        "status": "success",
                        "result": result_text,
                        "file_path": output_path,
                        "file_size": file_size,
                        "url": url
                    }
                else:
                    error_msg = f"Failed to download file. HTTP status: {response.status}"
                    return {"status": "error", "error": error_msg}
                    
    except Exception as e:
        logger.error(f"Error downloading file from URL: {e}")
        return {"status": "error", "error": str(e)}

async def _download_dataset_resources(dataset_id: str, resource_types: Optional[List[str]] = None) -> dict:
    """Download dataset files from dataset resources."""
    try:
        async with NDPClient(NDP_BASE_URL) as client:
            # Get dataset details first
            dataset = await client.get_dataset_details(dataset_id)
            if not dataset:
                return {"status": "error", "error": f"Dataset with ID '{dataset_id}' not found."}
            
            resources = dataset.get('resources', [])
            if not resources:
                return {"status": "error", "error": "No resources found for this dataset."}
            
            # Filter resources by type if specified
            if resource_types:
                resources = [r for r in resources if r.get('format', '').upper() in [rt.upper() for rt in resource_types]]
            
            result_text = f"**Downloading Resources for Dataset: {dataset.get('title', dataset.get('name', 'Untitled'))}**\n\n"
            
            downloaded_files = []
            
            for i, resource in enumerate(resources, 1):
                try:
                    result_text += f"{i}. Downloading: {resource.get('name', 'Unnamed Resource')} ({resource.get('format', 'Unknown')})\n"
                    
                    # Download the file
                    file_content = await client.download_file(resource['url'])
                    
                    # Save to temporary file
                    file_ext = _get_file_extension(resource.get('format', ''))
                    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                        temp_file.write(file_content)
                        temp_file_path = temp_file.name
                    
                    downloaded_files.append({
                        'name': resource.get('name', f'resource_{i}'),
                        'format': resource.get('format', 'Unknown'),
                        'path': temp_file_path,
                        'size': len(file_content)
                    })
                    
                    result_text += f"   ✅ Downloaded: {temp_file_path} ({len(file_content)} bytes)\n"
                    
                except Exception as e:
                    result_text += f"   ❌ Failed to download: {str(e)}\n"
                
                result_text += "\n"
            
            result_text += f"**Summary**: Downloaded {len(downloaded_files)} files successfully.\n"
            result_text += "Files are saved in temporary locations and can be accessed for analysis.\n"
            
            # Add file paths to result
            if downloaded_files:
                result_text += "\n**Downloaded Files:**\n"
                for file_info in downloaded_files:
                    result_text += f"- {file_info['name']} ({file_info['format']}): {file_info['path']}\n"
            
        return {"status": "success", "result": result_text, "downloaded_files": downloaded_files}
        
    except Exception as e:
        logger.error(f"Error downloading dataset resources: {e}")
        return {"status": "error", "error": str(e)}

def _get_file_extension(format_type: str) -> str:
    """Get file extension based on format type."""
    format_map = {
        'CSV': '.csv',
        'JSON': '.json',
        'GEOJSON': '.geojson',
        'SHAPE': '.shp',
        'KML': '.kml',
        'KMZ': '.kmz',
        'XML': '.xml',
        'TXT': '.txt',
        'PDF': '.pdf',
        'ZIP': '.zip',
        'XLSX': '.xlsx',
        'XLS': '.xls'
    }
    return format_map.get(format_type.upper(), '.dat')

async def _analyze_geospatial_data(dataset_id: str) -> dict:
    """Analyze geospatial data from a dataset with comprehensive insights."""
    try:
        async with NDPClient(NDP_BASE_URL) as client:
            # Get dataset details
            dataset = await client.get_dataset_details(dataset_id)
            if not dataset:
                return {"status": "error", "error": f"Dataset with ID '{dataset_id}' not found."}
            
            result_text = f"**Geospatial Analysis: {dataset.get('title', dataset.get('name', 'Untitled'))}**\n\n"
            
            # Analyze resources
            resources = dataset.get('resources', [])
            geospatial_resources = []
            
            for resource in resources:
                format_type = resource.get('format', '').upper()
                if format_type in ['GEOJSON', 'SHAPE', 'KML', 'KMZ']:
                    geospatial_resources.append(resource)
            
            if not geospatial_resources:
                result_text += "❌ No geospatial resources found in this dataset.\n"
                result_text += "Supported formats: GeoJSON, Shapefile, KML, KMZ\n"
                return {"status": "success", "result": result_text}
            
            result_text += f"✅ Found {len(geospatial_resources)} geospatial resource(s):\n\n"
            
            for i, resource in enumerate(geospatial_resources, 1):
                result_text += f"{i}. **{resource.get('name', 'Unnamed Resource')}**\n"
                result_text += f"   - Format: {resource.get('format', 'Unknown')}\n"
                result_text += f"   - URL: {resource.get('url', 'N/A')}\n"
                
                if resource.get('description'):
                    result_text += f"   - Description: {resource['description']}\n"
                
                result_text += "\n"
            
            # Additional analysis recommendations
            result_text += "**Analysis Recommendations:**\n"
            result_text += "- Use download_dataset_resources to download the geospatial files\n"
            result_text += "- Load files in GIS software (QGIS, ArcGIS) for detailed analysis\n"
            result_text += "- Consider coordinate system and projection information\n"
            result_text += "- Check for attribute data and metadata completeness\n"
            
        return {"status": "success", "result": result_text, "geospatial_resources": geospatial_resources}
        
    except Exception as e:
        logger.error(f"Error analyzing geospatial data: {e}")
        return {"status": "error", "error": str(e)}

async def _create_multi_series_plot(
    file_path: str,
    x_column: str,
    y_columns: List[str],
    title: str,
    output_path: str,
    figure_size: str,
    dpi: int
) -> dict:
    """Create a multi-series line plot with multiple y-columns against a single x-column."""
    try:
        import pandas as pd
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        from datetime import datetime
        
        # Load the data
        df = pd.read_csv(file_path)
        
        # Validate columns exist
        if x_column not in df.columns:
            return {"status": "error", "error": f"X-column '{x_column}' not found in data"}
        
        missing_y_columns = [col for col in y_columns if col not in df.columns]
        if missing_y_columns:
            return {"status": "error", "error": f"Y-columns not found: {missing_y_columns}"}
        
        # Parse figure size
        try:
            width, height = map(int, figure_size.split('x'))
        except ValueError:
            width, height = 15, 12  # Default size
        
        # Create the plot
        fig, ax = plt.subplots(figsize=(width, height))
        
        # Define colors for different series
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
        
        # Convert time column if it's numeric (nanoseconds since epoch)
        if df[x_column].dtype in ['int64', 'float64']:
            # Assume nanoseconds since epoch
            df['datetime'] = pd.to_datetime(df[x_column], unit='ns')
            x_data = df['datetime']
        else:
            # Try to parse as datetime
            try:
                x_data = pd.to_datetime(df[x_column])
            except:
                x_data = df[x_column]
        
        # Plot each y-column
        for i, y_col in enumerate(y_columns):
            color = colors[i % len(colors)]
            ax.plot(x_data, df[y_col], 
                   color=color, 
                   linewidth=0.8, 
                   alpha=0.8, 
                   label=y_col)
        
        # Customize the plot
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('Position (meters)', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Format x-axis for datetime
        if hasattr(x_data, 'dt'):
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        
        # Save the plot
        plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
        plt.close()
        
        # Generate summary statistics
        stats = {}
        for y_col in y_columns:
            stats[y_col] = {
                'mean': float(df[y_col].mean()),
                'std': float(df[y_col].std()),
                'min': float(df[y_col].min()),
                'max': float(df[y_col].max())
            }
        
        result_text = f"✅ Successfully created multi-series line plot\n"
        result_text += f"📁 Saved to: {output_path}\n"
        result_text += f"📊 Figure size: {width}x{height} inches\n"
        result_text += f"🖼️ DPI: {dpi}\n"
        result_text += f"📈 Series plotted: {', '.join(y_columns)}\n"
        result_text += f"📅 Time range: {x_data.min()} to {x_data.max()}\n"
        result_text += f"📊 Data points: {len(df)}"
        
        return {
            "status": "success",
            "result": result_text,
            "output_path": output_path,
            "figure_size": f"{width}x{height}",
            "dpi": dpi,
            "series": y_columns,
            "data_points": len(df),
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"Error creating multi-series plot: {e}")
        return {"status": "error", "error": str(e)}

async def _create_multi_panel_plot(
    file_path: str,
    x_column: str,
    y_columns: List[str],
    title: str,
    output_path: str,
    figure_size: str,
    dpi: int,
    layout: str
) -> dict:
    """Create a multi-panel plot with separate subplots for each y-column."""
    try:
        import pandas as pd
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        from datetime import datetime
        
        # Load the data
        df = pd.read_csv(file_path)
        
        # Validate columns exist
        if x_column not in df.columns:
            return {"status": "error", "error": f"X-column '{x_column}' not found in data"}
        
        missing_y_columns = [col for col in y_columns if col not in df.columns]
        if missing_y_columns:
            return {"status": "error", "error": f"Y-columns not found: {missing_y_columns}"}
        
        # Parse figure size
        try:
            width, height = map(int, figure_size.split('x'))
        except ValueError:
            width, height = 15, 12  # Default size
        
        # Convert time column if it's numeric (nanoseconds since epoch)
        if df[x_column].dtype in ['int64', 'float64']:
            # Assume nanoseconds since epoch
            df['datetime'] = pd.to_datetime(df[x_column], unit='ns')
            x_data = df['datetime']
        else:
            # Try to parse as datetime
            try:
                x_data = pd.to_datetime(df[x_column])
            except:
                x_data = df[x_column]
        
        # Create subplots based on layout
        n_panels = len(y_columns)
        if layout.lower() == "horizontal":
            fig, axes = plt.subplots(1, n_panels, figsize=(width, height))
            if n_panels == 1:
                axes = [axes]
        else:  # vertical layout (default)
            fig, axes = plt.subplots(n_panels, 1, figsize=(width, height))
            if n_panels == 1:
                axes = [axes]
        
        # Define colors for different components
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c']  # Blue, Orange, Green for East, North, Up
        
        # Plot each component in its own subplot
        for i, (y_col, ax) in enumerate(zip(y_columns, axes)):
            color = colors[i % len(colors)]
            
            # Plot the data
            ax.plot(x_data, df[y_col], color=color, linewidth=0.8, alpha=0.8)
            
            # Customize subplot
            ax.set_title(f'{y_col.upper()} Component', fontsize=14, fontweight='bold')
            ax.set_ylabel('Position (meters)', fontsize=12)
            ax.grid(True, alpha=0.3)
            
            # Format x-axis for datetime
            if hasattr(x_data, 'dt'):
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
            
            # Only show x-label for bottom subplot (vertical) or all subplots (horizontal)
            if layout.lower() == "vertical" and i < n_panels - 1:
                ax.set_xlabel('')
            else:
                ax.set_xlabel('Time', fontsize=12)
        
        # Add main title
        fig.suptitle(title, fontsize=16, fontweight='bold', y=0.98)
        
        # Adjust layout
        plt.tight_layout()
        plt.subplots_adjust(top=0.92)  # Make room for suptitle
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        
        # Save the plot
        plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
        plt.close()
        
        # Generate summary statistics
        stats = {}
        for y_col in y_columns:
            stats[y_col] = {
                'mean': float(df[y_col].mean()),
                'std': float(df[y_col].std()),
                'min': float(df[y_col].min()),
                'max': float(df[y_col].max())
            }
        
        result_text = f"✅ Successfully created multi-panel plot\n"
        result_text += f"📁 Saved to: {output_path}\n"
        result_text += f"📊 Figure size: {width}x{height} inches\n"
        result_text += f"🖼️ DPI: {dpi}\n"
        result_text += f"📈 Panels: {n_panels} ({', '.join(y_columns)})\n"
        result_text += f"📐 Layout: {layout}\n"
        result_text += f"📅 Time range: {x_data.min()} to {x_data.max()}\n"
        result_text += f"📊 Data points: {len(df)}"
        
        return {
            "status": "success",
            "result": result_text,
            "output_path": output_path,
            "figure_size": f"{width}x{height}",
            "dpi": dpi,
            "panels": y_columns,
            "layout": layout,
            "data_points": len(df),
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"Error creating multi-panel plot: {e}")
        return {"status": "error", "error": str(e)}

def main():
    """
    Main entry point to start the FastMCP server using the specified transport.
    Chooses between stdio and SSE based on MCP_TRANSPORT environment variable.
    """
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    if transport == "sse":
        host = os.getenv("MCP_SSE_HOST", "0.0.0.0")
        port = int(os.getenv("MCP_SSE_PORT", "8000"))
        print(f"Starting SSE on {host}:{port}", file=sys.stderr)
        mcp.run(transport="sse", host=host, port=port)
    else:
        print("Starting stdio transport", file=sys.stderr)
        mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
