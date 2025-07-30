# BP5 Variable Chunking

## Overview

The BP5 chunking capability provides memory-efficient reading of large variables from ADIOS BP5 files. When variables contain more than 1000 elements, the system automatically switches to chunked reading to prevent memory overflows and token limit issues in AI interactions.

## When Chunking is Used

Chunking is automatically triggered when:
- Variables have >1000 total elements
- The AI tool `read_variable_at_step` would consume too much memory
- Large multi-dimensional arrays need to be processed incrementally

## Core Implementation

### Key Files

- `src/implementation/bp5_read_variable_chunk.py`: Core chunking implementation
- `src/mcp_handlers.py:108-148`: MCP handler integration  
- `src/server.py:109-118`: Tool registration and API

### Chunking Algorithm

The chunking system works along the first dimension of variables:

1. **Chunk Size Calculation**: `max(100, min(500, total_elements // 100))`
   - This formula ensures chunk sizes between 100-500 elements, using roughly 1% of total elements
2. **Dimension Processing**: Only chunks along the first dimension, preserving other dimensions
3. **Memory Management**: Uses ADIOS2's selection API to read only the requested chunk

## AI Tool Integration

### `read_variable_chunk` Tool

**Purpose**: Read large variables in manageable chunks

**Parameters**:
- `filename` (str): Absolute path to BP5 file
- `variable_name` (str): Name of variable to read
- `target_step` (int): Step index to read from
- `start_index` (int, optional): Starting index along first dimension (default: 0)

**Returns**:
```json
{
  "value": [...],  // Flattened data array
  "chunk_info": {
    "is_complete": boolean,
    "current_chunk": int,
    "total_chunks": int,
    "start_index": int,
    "end_index": int,
    "next_start_index": int | null,
    "chunk_size": int,
    "total_elements_first_dim": int,
    "variable_shape": [int, ...]
  }
}
```

### Usage Pattern for AI

1. **Check Variable Size**: Use `inspect_variables` to determine if chunking is needed
2. **Initial Chunk**: Call `read_variable_chunk` with default parameters
3. **Subsequent Chunks**: Use `next_start_index` from previous response
4. **Continue**: Until `is_complete` is `True`

## Technical Details

### Memory Efficiency

- **Selective Reading**: Only requested chunk is loaded into memory
- **ADIOS2 Integration**: Uses `set_selection()` for efficient I/O
- **Flattened Output**: Multi-dimensional chunks are flattened to lists

### Error Handling

- **Step Validation**: Checks if target step exists
- **Variable Validation**: Verifies variable exists in file
- **Index Bounds**: Validates start_index against variable dimensions
- **Graceful Degradation**: Falls back to scalar handling for 0-dimensional variables

### Chunk Metadata

The `chunk_info` provides complete context for iterative processing:
- Progress tracking (`current_chunk` / `total_chunks`)
- Boundary information (`start_index`, `end_index`)
- Navigation assistance (`next_start_index`)
- Shape preservation (`variable_shape`)

## Benefits for AI Interactions

1. **Token Efficiency**: Prevents overwhelming AI context with massive datasets
2. **Memory Safety**: Avoids out-of-memory errors on large variables
3. **Progressive Processing**: Enables iterative analysis of large datasets
4. **Automatic Sizing**: Dynamic chunk size based on variable characteristics
5. **Complete Context**: Rich metadata enables intelligent processing decisions

## Integration Points

The chunking system integrates seamlessly with the existing ADIOS MCP infrastructure:
- **Handler Layer**: `mcp_handlers.py` provides async wrapper with automatic sizing
- **Server Layer**: `server.py` exposes the tool with comprehensive documentation
- **Implementation Layer**: `bp5_read_variable_chunk.py` handles low-level ADIOS2 operations

This architecture ensures that AI agents can efficiently work with large scientific datasets while maintaining memory safety and performance.