"""Basic validation tests for HDF5 MCP v2.0 implementation."""
import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


def test_imports():
    """Test that all modules can be imported."""
    try:
        from server import HDF5Server, run_server
        from tools import HDF5Tools, ToolRegistry, get_tools
        from resources import ResourceManager
        from cache import LRUCache
        from config import get_config
        from transports.sse_transport import SSETransport, SUPPORTED_VERSIONS
        from transports.stdio_transport import StdioTransport
        from transports.base import BaseTransport, TransportConfig, TransportType
        assert True
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")


def test_tool_registry():
    """Test tool registry has tools registered."""
    from tools import ToolRegistry
    tools = ToolRegistry.get_tools()
    assert len(tools) > 20, f"Expected 20+ tools, got {len(tools)}"


def test_tool_categories():
    """Test tools are properly categorized."""
    from tools import ToolRegistry
    categories = ToolRegistry.get_categories()

    expected_categories = {'file', 'dataset', 'attribute', 'performance', 'discovery', 'navigation'}
    actual_categories = set(categories.keys())

    assert expected_categories.issubset(actual_categories), \
        f"Missing categories: {expected_categories - actual_categories}"


def test_lru_cache():
    """Test LRU cache implementation."""
    from cache import LRUCache

    cache = LRUCache(capacity=3)

    # Add items
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)

    # Verify retrieval
    assert cache.get("a") == 1
    assert cache.get("b") == 2
    assert cache.get("c") == 3

    # Add 4th item - should evict "a" (oldest)
    cache.put("d", 4)
    assert cache.get("a") is None
    assert cache.get("d") == 4


def test_sse_protocol_versions():
    """Test SSE transport supports required protocol versions."""
    from transports.sse_transport import SUPPORTED_VERSIONS

    assert '2025-06-18' in SUPPORTED_VERSIONS
    assert '2025-03-26' in SUPPORTED_VERSIONS


def test_sse_localhost_binding():
    """Test SSE transport enforces localhost binding."""
    from transports.sse_transport import SSETransport
    from transports.base import TransportConfig, TransportType

    # Test default config
    transport = SSETransport()
    assert transport.config.host == '127.0.0.1', "Default should be localhost"

    # Test 0.0.0.0 is overridden
    config = TransportConfig(
        transport_type=TransportType.SSE,
        host='0.0.0.0'
    )
    transport = SSETransport(config)
    assert transport.config.host == '127.0.0.1', "0.0.0.0 should be overridden to localhost"


def test_config_loading():
    """Test configuration loads successfully."""
    from config import get_config

    config = get_config()
    assert config is not None
    assert hasattr(config, 'storage')
    assert hasattr(config, 'cache')


def test_resource_manager_initialization():
    """Test resource manager can be initialized."""
    from resources import ResourceManager
    from pathlib import Path

    rm = ResourceManager(data_dir=Path("data"), cache_capacity=100)
    assert rm is not None
    assert rm.cache_capacity == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
