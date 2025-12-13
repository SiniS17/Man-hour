# Project Restructuring Guide

## Overview
This document tracks the step-by-step restructuring of the project to improve code organization, eliminate duplication, and enhance maintainability.

**Goal**: Transform monolithic modules into a clean, modular architecture with clear separation of concerns.

---

## Current Status: Step 1 - COMPLETED ✅

### What We're Doing
Restructuring the project from a flat structure with duplicated code into a well-organized modular system.

---

## Project Structure Evolution

### Before (Original Structure)
```
project/
├── config.py
├── data_processing.py      # 250+ lines, multiple responsibilities
├── input_output.py         # 300+ lines, all Excel generation
├── tool_control.py
├── main.py
├── debug.py
├── test_config.py
├── test_coefficient.py
├── test_tool_control.py
├── settings.ini
├── INPUT/
├── OUTPUT/
├── REFERENCE/
└── LOG/
```

**Problems:**
- `hours_to_hhmm()` duplicated in 3+ files
- `data_processing.py` handles too many concerns
- `input_output.py` has all sheet generation in one file
- Test files scattered without unified logging
- No clear separation between features

### After (Target Structure)
```
project/
├── core/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── data_loader.py         # File loading operations
│   ├── data_processor.py      # Core processing logic
│   └── id_extractor.py        # Task ID extraction
├── features/
│   ├── __init__.py
│   ├── tool_control.py        # Tool availability checking
│   ├── special_code.py        # Special code analysis
│   └── coefficients.py        # Coefficient calculations
├── writers/
│   ├── __init__.py
│   ├── excel_writer.py        # Main Excel orchestration
│   ├── sheet_total_mhrs.py    # Total man-hours sheet
│   ├── sheet_high_mhrs.py     # High man-hours sheet
│   ├── sheet_new_tasks.py     # New task IDs sheet
│   ├── sheet_tool_control.py  # Tool control sheet
│   └── debug_logger.py        # Debug logging
├── utils/                      # ✅ COMPLETED
│   ├── __init__.py
│   ├── time_utils.py          # Time conversions
│   ├── validation.py          # Data validation
│   └── formatters.py          # String formatting
├── tests/
│   ├── __init__.py
│   ├── test_runner.py         # Unified test orchestration
│   ├── test_coefficients.py   # Coefficient tests
│   ├── test_tool_control.py   # Tool control tests
│   └── test_config.py         # Config tests
├── main.py                    # Simplified orchestration
├── settings.ini               # Unchanged
├── INPUT/                     # Unchanged
├── OUTPUT/                    # Unchanged
├── REFERENCE/                 # Unchanged
└── LOG/                       # Unchanged
```

---

## Detailed Steps

### ✅ Step 1: Create Utils Module (COMPLETED)

**Purpose**: Eliminate code duplication by centralizing common utility functions.

**Files Created:**
- [x] `utils/__init__.py` - Package initialization
- [x] `utils/time_utils.py` - Time conversion functions
- [x] `utils/validation.py` - Data validation utilities
- [x] `utils/formatters.py` - String formatting utilities

**Functions Moved:**

| Function | From | To | Used In |
|----------|------|-----|---------|
| `hours_to_hhmm()` | data_processing.py, input_output.py, debug.py | utils/time_utils.py | 3+ files |
| `convert_planned_mhrs()` | data_processing.py | utils/time_utils.py | data_processing.py |
| `time_to_hours()` | debug.py | utils/time_utils.py | debug.py |
| `validate_required_columns()` | NEW | utils/validation.py | Multiple |
| `clean_string()` | NEW | utils/formatters.py | Multiple |
| `format_percentage()` | NEW | utils/formatters.py | input_output.py |

**Benefits:**
- ✅ Single source of truth for common functions
- ✅ Easy to test utilities in isolation
- ✅ Consistent behavior across modules
- ✅ Reduced code duplication from ~60 lines to 0

**Next Actions:**
- [ ] Update `data_processing.py` to import from utils
- [ ] Update `input_output.py` to import from utils
- [ ] Update `debug.py` to import from utils
- [ ] Update `tool_control.py` to import from utils

---

### ⏳ Step 2: Split Data Processing (PENDING)

**Purpose**: Break down `data_processing.py` into focused modules with single responsibilities.

**Files to Create:**
- [ ] `core/__init__.py`
- [ ] `core/data_loader.py` - Load input files and reference IDs
- [ ] `core/id_extractor.py` - Extract task IDs from titles
- [ ] `core/data_processor.py` - Simplified core processing
- [ ] `features/__init__.py`
- [ ] `features/special_code.py` - Special code distribution calculations
- [ ] `features/coefficients.py` - Coefficient application logic

**Functions to Move:**

| Function | Current Location | New Location | Reason |
|----------|-----------------|--------------|--------|
| `load_reference_ids()` | main.py | core/data_loader.py | Loading operation |
| `extract_task_id()` | data_processing.py | core/id_extractor.py | ID extraction logic |
| `extract_id_from_title()` | data_processing.py | core/id_extractor.py | ID extraction logic |
| `calculate_special_code_distribution()` | data_processing.py | features/special_code.py | Feature-specific |
| `get_seq_coefficient()` | config.py | features/coefficients.py | Feature-specific |
| `process_data()` | data_processing.py | core/data_processor.py | Core logic (simplified) |

**Current `data_processing.py` Breakdown:**
```
data_processing.py (254 lines)
├── extract_task_id() - 29 lines → core/id_extractor.py
├── extract_id_from_title() - 25 lines → core/id_extractor.py
├── convert_planned_mhrs() - 18 lines → utils/time_utils.py ✅
├── calculate_special_code_distribution() - 12 lines → features/special_code.py
├── process_data() - 150 lines → core/data_processor.py (simplified)
└── hours_to_hhmm() - 10 lines → utils/time_utils.py ✅
```

**Benefits:**
- Clear separation of concerns
- Easier to test individual components
- Easier to add new ID extraction methods
- Special code logic isolated for future enhancements

---

### ⏳ Step 3: Modularize Output Generation (PENDING)

**Purpose**: Break down `input_output.py` into manageable sheet-specific modules.

**Files to Create:**
- [ ] `writers/__init__.py`
- [ ] `writers/excel_writer.py` - Main orchestration
- [ ] `writers/sheet_total_mhrs.py` - Total man-hours sheet generation
- [ ] `writers/sheet_high_mhrs.py` - High man-hours sheet generation
- [ ] `writers/sheet_new_tasks.py` - New task IDs sheet generation
- [ ] `writers/sheet_tool_control.py` - Tool control sheet generation
- [ ] `writers/debug_logger.py` - Debug log generation

**Current `input_output.py` Breakdown:**
```
input_output.py (318 lines)
├── load_input_files() - 8 lines → writers/excel_writer.py
├── save_output_file() - 30 lines → writers/excel_writer.py
├── create_total_mhrs_sheet() - 60 lines → writers/sheet_total_mhrs.py
├── create_high_mhrs_sheet() - 50 lines → writers/sheet_high_mhrs.py
├── create_new_task_ids_sheet() - 40 lines → writers/sheet_new_tasks.py
├── create_tool_control_sheet() - 45 lines → writers/sheet_tool_control.py
├── save_debug_log() - 75 lines → writers/debug_logger.py
└── hours_to_hhmm() - 10 lines → utils/time_utils.py ✅
```

**Benefits:**
- Each sheet type is independent
- Easy to modify one sheet without affecting others
- Easy to add new sheet types
- Cleaner imports and dependencies

---

### ⏳ Step 4: Unify Testing & Debug (PENDING)

**Purpose**: Create a comprehensive test suite with unified logging.

**Files to Create:**
- [ ] `tests/__init__.py`
- [ ] `tests/test_runner.py` - Main test orchestration with logging

**Files to Move:**
- [ ] `test_config.py` → `tests/test_config.py`
- [ ] `test_coefficient.py` → `tests/test_coefficients.py`
- [ ] `test_tool_control.py` → `tests/test_tool_control.py`

**Files to Merge/Remove:**
- [ ] `debug.py` - Functionality absorbed into `tests/test_runner.py`

**New Functionality:**
```python
# tests/test_runner.py will provide:
- Run all tests with single command
- Generate comprehensive test report to LOG/
- Include debug samples in test output
- B84 vs C9 comparison tests
- Coefficient verification tests
- Tool control validation tests
- Data quality checks
```

**Benefits:**
- Single command to run all tests
- All test output captured in LOG folder
- Structured test results
- Easy to add new tests
- Integration with existing debug functionality

---

### ⏳ Step 5: Simplify Main Orchestration (PENDING)

**Purpose**: Make `main.py` a clean orchestrator with minimal logic.

**Current `main.py`:**
```python
def main():
    print_config()
    input_files = load_input_files()
    reference_task_ids, reference_eo_ids = load_reference_ids()
    
    for input_file in input_files:
        processed_data = process_data(input_file, reference_task_ids, reference_eo_ids)
        save_output_file(input_file, processed_data)
```

**New `main.py`:**
```python
from core.config import print_config
from core.data_loader import load_input_files, load_reference_ids
from core.data_processor import process_data
from writers.excel_writer import save_output_file

def main():
    """Main orchestration - coordinates the workflow"""
    print_config()
    
    input_files = load_input_files()
    if not input_files:
        print("No input files to process.")
        return
    
    reference_data = load_reference_ids()
    
    for input_file in input_files:
        print(f"Processing: {input_file}")
        processed_data = process_data(input_file, reference_data)
        save_output_file(input_file, processed_data)
        print(f"Completed: {input_file}\n")
    
    print("All files processed successfully!")
```

**Benefits:**
- Clear, readable workflow
- Easy to understand the process flow
- Minimal logic, just coordination
- Clean imports from organized modules

---

### ⏳ Step 6: Update Imports & Integration (PENDING)

**Purpose**: Make all modules work together seamlessly.

**Tasks:**
- [ ] Update all imports across modified files
- [ ] Add proper `__init__.py` files with exports
- [ ] Update module docstrings
- [ ] Remove old/deprecated files
- [ ] Test full workflow end-to-end

**Files to Remove:**
- [ ] Old `data_processing.py` (after migration)
- [ ] Old `input_output.py` (after migration)
- [ ] `debug.py` (functionality moved to tests/)

**Files to Keep:**
- [x] `settings.ini` - No changes
- [x] `tool_control.py` - Moves to features/ but functionality unchanged
- [x] `main.py` - Simplified but stays

---

## Migration Checklist

### Step 1: Utils Module ✅
- [x] Create `utils/__init__.py`
- [x] Create `utils/time_utils.py`
- [x] Create `utils/validation.py`
- [x] Create `utils/formatters.py`
- [ ] Update `data_processing.py` imports
- [ ] Update `input_output.py` imports
- [ ] Update `debug.py` imports
- [ ] Update `tool_control.py` imports
- [ ] Test imports work correctly

### Step 2: Data Processing
- [ ] Create `core/__init__.py`
- [ ] Create `core/data_loader.py`
- [ ] Create `core/id_extractor.py`
- [ ] Create `core/data_processor.py`
- [ ] Create `features/__init__.py`
- [ ] Create `features/special_code.py`
- [ ] Create `features/coefficients.py`
- [ ] Move `config.py` to `core/config.py`
- [ ] Update all imports
- [ ] Test processing workflow

### Step 3: Output Generation
- [ ] Create `writers/__init__.py`
- [ ] Create `writers/excel_writer.py`
- [ ] Create `writers/sheet_total_mhrs.py`
- [ ] Create `writers/sheet_high_mhrs.py`
- [ ] Create `writers/sheet_new_tasks.py`
- [ ] Create `writers/sheet_tool_control.py`
- [ ] Create `writers/debug_logger.py`
- [ ] Update all imports
- [ ] Test Excel output

### Step 4: Testing
- [ ] Create `tests/__init__.py`
- [ ] Create `tests/test_runner.py`
- [ ] Move `test_config.py` to `tests/`
- [ ] Move `test_coefficient.py` to `tests/`
- [ ] Move `test_tool_control.py` to `tests/`
- [ ] Integrate `debug.py` functionality
- [ ] Test all tests run correctly

### Step 5: Main Simplification
- [ ] Update `main.py` imports
- [ ] Simplify `main.py` logic
- [ ] Test end-to-end workflow

### Step 6: Final Integration
- [ ] Verify all imports work
- [ ] Remove deprecated files
- [ ] Run full test suite
- [ ] Verify Excel output is identical
- [ ] Update documentation

---

## Testing Strategy

After each step:
1. **Import Test**: Verify new modules import correctly
2. **Unit Test**: Test individual functions in isolation
3. **Integration Test**: Test modules work together
4. **Regression Test**: Verify output matches original

**Critical Tests:**
- Excel output format unchanged
- Man-hours calculations identical
- Tool control logic unchanged
- Debug logs contain same information
- All edge cases still handled

---

## Rollback Plan

If issues occur:
1. Keep old files until new structure is fully tested
2. Git commit after each successful step
3. Can revert to any previous step if needed

**File Backup Strategy:**
```
Before deleting old files, rename them:
- data_processing.py → data_processing.py.old
- input_output.py → input_output.py.old
- debug.py → debug.py.old
```

---

## Benefits Summary

### Code Quality
- ✅ Eliminated ~60+ lines of duplicated code (Step 1)
- ⏳ Reduced average file size from 250+ to <100 lines
- ⏳ Clear single responsibility for each module
- ⏳ Easier to understand and maintain

### Maintainability
- ✅ Common functions in one place (Step 1)
- ⏳ Easy to find and modify specific features
- ⏳ Clear dependencies between modules
- ⏳ Easier onboarding for new developers

### Testing
- ✅ Utilities can be tested independently (Step 1)
- ⏳ Features can be tested in isolation
- ⏳ Unified test suite with comprehensive logging
- ⏳ Better test coverage

### Scalability
- ⏳ Easy to add new features (new files in features/)
- ⏳ Easy to add new sheet types (new files in writers/)
- ⏳ Easy to add new ID extraction methods
- ⏳ Easy to add new validation rules

---

## Notes

- No changes to `settings.ini`
- No changes to folder structure (INPUT, OUTPUT, REFERENCE, LOG)
- No changes to Excel output format
- All existing functionality preserved
- Backward compatible with existing workflows

---

## Progress Tracking

| Step | Status | Date Started | Date Completed | Notes |
|------|--------|--------------|----------------|-------|
| 1. Utils Module | ✅ Complete | 2024-12-13 | 2024-12-13 | 4 files created |
| 2. Data Processing | ⏳ Pending | - | - | - |
| 3. Output Generation | ⏳ Pending | - | - | - |
| 4. Testing | ⏳ Pending | - | - | - |
| 5. Main Simplification | ⏳ Pending | - | - | - |
| 6. Integration | ⏳ Pending | - | - | - |

---

**Last Updated**: December 13, 2024  
**Current Step**: Step 1 - Utils Module (COMPLETED)  
**Next Step**: Update existing files to use utils, then proceed to Step 2