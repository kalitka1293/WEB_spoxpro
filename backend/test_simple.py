"""
Simple test to verify property-based testing works with reduced examples.
"""

import pytest
from hypothesis import given, strategies as st, settings


class TestSimpleProperties:
    """Simple property-based tests to verify reduced examples work."""
    
    @given(x=st.integers(min_value=1, max_value=100))
    @settings(max_examples=20)
    def test_reduced_examples_work(self, x):
        """Test that reduced examples setting works correctly."""
        assert x > 0
        assert x <= 100
    
    @given(text=st.text(min_size=1, max_size=50))
    @settings(max_examples=10)
    def test_text_property(self, text):
        """Test text property with reduced examples."""
        assert len(text) >= 1
        assert len(text) <= 50