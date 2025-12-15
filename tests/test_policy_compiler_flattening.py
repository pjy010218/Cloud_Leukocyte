# -*- coding: utf-8 -*-
import unittest
import sys
import os
import time
import dataclasses

# Adjust path to import modules from parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from policy_compiler import compile_to_data_plane_artifact
try:
    from hierarchical_policy_engine_cython import HierarchicalPolicyEngine
except ImportError:
    from hierarchical_policy_engine import HierarchicalPolicyEngine

class TestPolicyCompilerFlattening(unittest.TestCase):
    
    def setUp(self):
        self.engine = HierarchicalPolicyEngine()
        
    def test_flattening_correctness(self):
        """Verify that flatten() correctly exports allowed paths."""
        self.engine.allow_path("user.name")
        self.engine.allow_path("user.email")
        self.engine.allow_path("order.id")
        
        flattened = self.engine.flatten()
        expected = {"user.name", "user.email", "order.id"}
        
        self.assertEqual(set(flattened), expected)
        
    def test_suppression_handling(self):
        """Verify that suppressed paths are NOT included in the flattened list."""
        self.engine.allow_path("payload.header")
        self.engine.allow_path("payload.content")
        self.engine.suppress_path("payload.content")
        
        flattened = self.engine.flatten()
        self.assertIn("payload.header", flattened)
        self.assertNotIn("payload.content", flattened)
        
    def test_artifact_generation(self):
        """Verify that the compiler generates the correct O(1) map."""
        self.engine.allow_path("api.v1.resource")
        
        artifact = compile_to_data_plane_artifact(self.engine, "/test", 1)
        
        self.assertIn("api.v1.resource", artifact.allowed_fields_map)
        self.assertEqual(artifact.allowed_fields_map["api.v1.resource"], 1)
        
    def test_lookup_performance(self):
        """Verify O(1) lookup performance of the generated map."""
        # Populate with many fields
        for i in range(10000):
            self.engine.allow_path(f"data.field_{i}")
            
        artifact = compile_to_data_plane_artifact(self.engine, "/perf", 1)
        lookup_map = artifact.allowed_fields_map
        
        start_time = time.perf_counter()
        # Perform 100,000 lookups
        for i in range(100000):
            _ = "data.field_5000" in lookup_map
        end_time = time.perf_counter()
        
        avg_time = (end_time - start_time) / 100000
        print(f"\nAverage Lookup Time (Map): {avg_time * 1e6:.4f} µs")
        
        # Should be very fast (< 0.2 µs usually)
        self.assertLess(avg_time, 1e-6) # < 1 µs

if __name__ == '__main__':
    unittest.main()
