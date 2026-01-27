# spoXpro Backend Tests

This directory contains comprehensive tests for the spoXpro e-commerce backend, including both unit tests and property-based tests.

## Test Structure

- `conftest.py` - Test configuration and fixtures
- `test_product_properties.py` - Property-based tests for product database models

## Property-Based Testing

Property-based tests use Hypothesis to generate random test data and verify that universal properties hold across all inputs. Each property test runs with a minimum of 100 iterations to ensure comprehensive coverage.

### Current Properties

1. **Product Data Integrity** (`test_product_properties.py`)
   - **Feature**: spoxpro-backend, Property 1: Product Data Integrity
   - **Validates**: Requirements 1.1, 1.4
   - **Property**: For any product data with all required fields, storing and retrieving the product should preserve all field values including name, description, type relationships, sizes with quantities, and metadata

## Running Tests

```bash
# Run all tests
python -m pytest backend/tests/ -v

# Run specific property test
python -m pytest backend/tests/test_product_properties.py -v

# Run with coverage
python -m pytest backend/tests/ --cov=backend --cov-report=html
```

## Test Database

Tests use in-memory SQLite databases for fast execution and isolation. Each test gets a fresh database instance to ensure no interference between tests.

## Test Data Generation

Property tests use Hypothesis strategies to generate:
- Valid product data with all field combinations
- Product sizes with different combinations of valid clothing sizes
- JSON fields with various structures including empty lists and complex nested data
- Foreign key relationships with helper table data

The tests verify complete data integrity across all database operations and relationships.