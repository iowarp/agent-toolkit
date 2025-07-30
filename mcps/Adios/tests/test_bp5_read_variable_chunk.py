import pytest
import numpy as np
from unittest.mock import Mock, patch
from src.implementation.bp5_read_variable_chunk import read_variable_chunked


class TestReadVariableChunked:
    @patch("src.implementation.bp5_read_variable_chunk.adios2.Adios")
    def test_read_variable_chunk_1d_first_chunk(self, mock_adios_class):
        # Setup mocks
        mock_adios = Mock()
        mock_adios_class.return_value = mock_adios
        mock_io = Mock()
        mock_adios.declare_io.return_value = mock_io
        mock_engine = Mock()
        mock_io.open.return_value = mock_engine
        
        mock_engine.steps.return_value = 5
        mock_var = Mock()
        mock_io.inquire_variable.return_value = mock_var
        mock_var.shape.return_value = [100]  # 1D array with 100 elements
        
        # Mock the read operation
        def mock_get(var, data):
            # Simulate reading first 10 elements
            data[:] = np.arange(10, dtype=np.float64)
        mock_engine.get.side_effect = mock_get
        
        result = read_variable_chunked("test.bp", "data", 0, 0, 10)
        
        assert result["data"] == list(range(10))
        assert result["chunk_info"]["is_complete"] is False
        assert result["chunk_info"]["current_chunk"] == 1
        assert result["chunk_info"]["total_chunks"] == 10
        assert result["chunk_info"]["start_index"] == 0
        assert result["chunk_info"]["end_index"] == 10
        assert result["chunk_info"]["next_start_index"] == 10
        assert result["chunk_info"]["total_elements_first_dim"] == 100
        assert result["chunk_info"]["variable_shape"] == [100]

    @patch("src.implementation.bp5_read_variable_chunk.adios2.Adios")
    def test_read_variable_chunk_1d_last_chunk(self, mock_adios_class):
        # Setup mocks
        mock_adios = Mock()
        mock_adios_class.return_value = mock_adios
        mock_io = Mock()
        mock_adios.declare_io.return_value = mock_io
        mock_engine = Mock()
        mock_io.open.return_value = mock_engine
        
        mock_engine.steps.return_value = 5
        mock_var = Mock()
        mock_io.inquire_variable.return_value = mock_var
        mock_var.shape.return_value = [95]  # 95 elements total
        
        def mock_get(var, data):
            # Simulate reading last 5 elements
            data[:] = np.arange(90, 95, dtype=np.float64)
        mock_engine.get.side_effect = mock_get
        
        result = read_variable_chunked("test.bp", "data", 0, 90, 10)
        
        assert result["data"] == [90.0, 91.0, 92.0, 93.0, 94.0]
        assert result["chunk_info"]["is_complete"] is True
        assert result["chunk_info"]["current_chunk"] == 10
        assert result["chunk_info"]["total_chunks"] == 10
        assert result["chunk_info"]["next_start_index"] is None

    @patch("src.implementation.bp5_read_variable_chunk.adios2.Adios")
    def test_read_variable_chunk_2d_array(self, mock_adios_class):
        # Setup mocks
        mock_adios = Mock()
        mock_adios_class.return_value = mock_adios
        mock_io = Mock()
        mock_adios.declare_io.return_value = mock_io
        mock_engine = Mock()
        mock_io.open.return_value = mock_engine
        
        mock_engine.steps.return_value = 5
        mock_var = Mock()
        mock_io.inquire_variable.return_value = mock_var
        mock_var.shape.return_value = [20, 5]  # 2D array 20x5
        
        def mock_get(var, data):
            # Simulate reading first 3 rows (3x5 = 15 elements)
            data[:] = np.arange(15, dtype=np.float64).reshape(3, 5)
        mock_engine.get.side_effect = mock_get
        
        result = read_variable_chunked("test.bp", "data", 0, 0, 3)
        
        assert len(result["data"]) == 15  # 3 rows * 5 columns
        assert result["data"] == list(range(15))  # Flattened
        assert result["chunk_info"]["is_complete"] is False
        assert result["chunk_info"]["total_elements_first_dim"] == 20
        assert result["chunk_info"]["variable_shape"] == [20, 5]

    @patch("src.implementation.bp5_read_variable_chunk.adios2.Adios")
    def test_read_variable_chunk_scalar(self, mock_adios_class):
        # Setup mocks
        mock_adios = Mock()
        mock_adios_class.return_value = mock_adios
        mock_io = Mock()
        mock_adios.declare_io.return_value = mock_io
        mock_engine = Mock()
        mock_io.open.return_value = mock_engine
        
        mock_engine.steps.return_value = 5
        mock_var = Mock()
        mock_io.inquire_variable.return_value = mock_var
        mock_var.shape.return_value = []  # Scalar
        
        def mock_get(var, data):
            data[()] = 42.5
        mock_engine.get.side_effect = mock_get
        
        result = read_variable_chunked("test.bp", "temperature", 0, 0, 10)
        
        assert result["data"] == 42.5
        assert result["chunk_info"]["is_complete"] is True
        assert result["chunk_info"]["total_elements"] == 1
        assert result["chunk_info"]["current_chunk"] == 1
        assert result["chunk_info"]["total_chunks"] == 1

    @patch("src.implementation.bp5_read_variable_chunk.adios2.Adios")
    def test_read_variable_chunk_step_not_found(self, mock_adios_class):
        # Setup mocks
        mock_adios = Mock()
        mock_adios_class.return_value = mock_adios
        mock_io = Mock()
        mock_adios.declare_io.return_value = mock_io
        mock_engine = Mock()
        mock_io.open.return_value = mock_engine
        
        mock_engine.steps.return_value = 3  # Only 3 steps available
        
        with pytest.raises(ValueError, match="Step 5 not found. Max step: 2"):
            read_variable_chunked("test.bp", "data", 5, 0, 10)

    @patch("src.implementation.bp5_read_variable_chunk.adios2.Adios")
    def test_read_variable_chunk_variable_not_found(self, mock_adios_class):
        # Setup mocks
        mock_adios = Mock()
        mock_adios_class.return_value = mock_adios
        mock_io = Mock()
        mock_adios.declare_io.return_value = mock_io
        mock_engine = Mock()
        mock_io.open.return_value = mock_engine
        
        mock_engine.steps.return_value = 5
        mock_io.inquire_variable.return_value = None  # Variable not found
        
        with pytest.raises(ValueError, match="Variable 'nonexistent' not found"):
            read_variable_chunked("test.bp", "nonexistent", 0, 0, 10)

    @patch("src.implementation.bp5_read_variable_chunk.adios2.Adios")
    def test_read_variable_chunk_start_index_out_of_bounds(self, mock_adios_class):
        # Setup mocks
        mock_adios = Mock()
        mock_adios_class.return_value = mock_adios
        mock_io = Mock()
        mock_adios.declare_io.return_value = mock_io
        mock_engine = Mock()
        mock_io.open.return_value = mock_engine
        
        mock_engine.steps.return_value = 5
        mock_var = Mock()
        mock_io.inquire_variable.return_value = mock_var
        mock_var.shape.return_value = [50]  # Array with 50 elements
        
        with pytest.raises(ValueError, match="start_index 60 >= total_elements 50"):
            read_variable_chunked("test.bp", "data", 0, 60, 10)

    @patch("src.implementation.bp5_read_variable_chunk.adios2.Adios")
    def test_read_variable_chunk_3d_array(self, mock_adios_class):
        # Setup mocks
        mock_adios = Mock()
        mock_adios_class.return_value = mock_adios
        mock_io = Mock()
        mock_adios.declare_io.return_value = mock_io
        mock_engine = Mock()
        mock_io.open.return_value = mock_engine
        
        mock_engine.steps.return_value = 5
        mock_var = Mock()
        mock_io.inquire_variable.return_value = mock_var
        mock_var.shape.return_value = [10, 4, 3]  # 3D array 10x4x3
        
        def mock_get(var, data):
            # Simulate reading first 2 "slices" along first dimension (2x4x3 = 24 elements)
            data[:] = np.arange(24, dtype=np.float64).reshape(2, 4, 3)
        mock_engine.get.side_effect = mock_get
        
        result = read_variable_chunked("test.bp", "data", 0, 0, 2)
        
        assert len(result["data"]) == 24  # 2 * 4 * 3
        assert result["data"] == list(range(24))  # Flattened
        assert result["chunk_info"]["total_elements_first_dim"] == 10
        assert result["chunk_info"]["variable_shape"] == [10, 4, 3]

    @patch("src.implementation.bp5_read_variable_chunk.adios2.Adios")
    def test_read_variable_chunk_single_element_remaining(self, mock_adios_class):
        # Setup mocks
        mock_adios = Mock()
        mock_adios_class.return_value = mock_adios
        mock_io = Mock()
        mock_adios.declare_io.return_value = mock_io
        mock_engine = Mock()
        mock_io.open.return_value = mock_engine
        
        mock_engine.steps.return_value = 5
        mock_var = Mock()
        mock_io.inquire_variable.return_value = mock_var
        mock_var.shape.return_value = [21]  # 21 elements, chunk size 10
        
        def mock_get(var, data):
            # Simulate reading the last element
            data[:] = np.array([20.0], dtype=np.float64)
        mock_engine.get.side_effect = mock_get
        
        result = read_variable_chunked("test.bp", "data", 0, 20, 10)
        
        assert result["data"] == [20.0]
        assert result["chunk_info"]["is_complete"] is True
        assert result["chunk_info"]["chunk_size"] == 1
        assert result["chunk_info"]["current_chunk"] == 3
        assert result["chunk_info"]["total_chunks"] == 3

    @patch("src.implementation.bp5_read_variable_chunk.adios2.Adios")
    def test_read_variable_chunk_engine_close_called(self, mock_adios_class):
        # Setup mocks
        mock_adios = Mock()
        mock_adios_class.return_value = mock_adios
        mock_io = Mock()
        mock_adios.declare_io.return_value = mock_io
        mock_engine = Mock()
        mock_io.open.return_value = mock_engine
        
        mock_engine.steps.return_value = 5
        mock_var = Mock()
        mock_io.inquire_variable.return_value = mock_var
        mock_var.shape.return_value = [10]
        
        def mock_get(var, data):
            data[:] = np.arange(5, dtype=np.float64)
        mock_engine.get.side_effect = mock_get
        
        read_variable_chunked("test.bp", "data", 0, 0, 5)
        
        # Verify engine was properly closed
        mock_engine.close.assert_called_once()

    @patch("src.implementation.bp5_read_variable_chunk.adios2.Adios")
    def test_read_variable_chunk_engine_close_on_exception(self, mock_adios_class):
        # Setup mocks
        mock_adios = Mock()
        mock_adios_class.return_value = mock_adios
        mock_io = Mock()
        mock_adios.declare_io.return_value = mock_io
        mock_engine = Mock()
        mock_io.open.return_value = mock_engine
        
        mock_engine.steps.return_value = 5
        mock_var = Mock()
        mock_io.inquire_variable.return_value = mock_var
        mock_var.shape.return_value = [10]
        
        # Make the get operation raise an exception
        mock_engine.get.side_effect = RuntimeError("Read failed")
        
        with pytest.raises(RuntimeError, match="Read failed"):
            read_variable_chunked("test.bp", "data", 0, 0, 5)
        
        # Verify engine was still closed despite the exception
        mock_engine.close.assert_called_once()

    @patch("src.implementation.bp5_read_variable_chunk.adios2.Adios")
    def test_read_variable_chunk_default_parameters(self, mock_adios_class):
        # Setup mocks
        mock_adios = Mock()
        mock_adios_class.return_value = mock_adios
        mock_io = Mock()
        mock_adios.declare_io.return_value = mock_io
        mock_engine = Mock()
        mock_io.open.return_value = mock_engine
        
        mock_engine.steps.return_value = 5
        mock_var = Mock()
        mock_io.inquire_variable.return_value = mock_var
        mock_var.shape.return_value = [2000]  # Large array to test default chunk size
        
        def mock_get(var, data):
            # Should get 1000 elements by default
            data[:] = np.arange(1000, dtype=np.float64)
        mock_engine.get.side_effect = mock_get
        
        # Call with default start_index=0 and chunk_size=1000
        result = read_variable_chunked("test.bp", "data", 0)
        
        assert len(result["data"]) == 1000
        assert result["chunk_info"]["chunk_size"] == 1000
        assert result["chunk_info"]["total_chunks"] == 2