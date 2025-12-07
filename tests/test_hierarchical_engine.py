import unittest
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hierarchical_policy_engine import HierarchicalPolicyEngine

class TestHierarchicalPolicyEngine(unittest.TestCase):
    def setUp(self):
        self.engine = HierarchicalPolicyEngine()

    def test_allow_path(self):
        path = "user.profile.view"
        self.engine.allow_path(path)
        self.assertEqual(self.engine.check_access(path), "ALLOWED")
        
    def test_suppress_path(self):
        path = "payload.malicious"
        self.engine.suppress_path(path)
        self.assertEqual(self.engine.check_access(path), "BLOCKED_SUPPRESSED")
        
    def test_suppress_overrides_allow(self):
        path = "user.input"
        self.engine.allow_path(path)
        self.engine.suppress_path(path)
        self.assertEqual(self.engine.check_access(path), "BLOCKED_SUPPRESSED")
        
    def test_not_found(self):
        self.assertEqual(self.engine.check_access("unknown.path"), "DENIED_NOT_FOUND")

    def test_transduction(self):
        source_engine = HierarchicalPolicyEngine()
        source_engine.suppress_path("shared.vulnerability")
        
        target_engine = HierarchicalPolicyEngine()
        # Ensure target doesn't have it yet
        self.assertEqual(target_engine.check_access("shared.vulnerability"), "DENIED_NOT_FOUND")
        
        # Transduce
        target_engine.transduce_immunity(source_engine)
        
        # Check if immunity transferred (Proactive Immunity)
        # Note: The implementation creates the node if it's suppressed in source
        self.assertEqual(target_engine.check_access("shared.vulnerability"), "BLOCKED_SUPPRESSED")

if __name__ == '__main__':
    unittest.main()
