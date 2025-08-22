"""
NDP MCP Server Package

A Model Context Protocol (MCP) server for National Data Platform integration.
"""

__version__ = "1.0.0"
__author__ = "NDP MCP Team"
__email__ = "ndp-mcp@example.com"

from .ndp_mcp_server import NDPClient, main

__all__ = ["NDPClient", "main"]
