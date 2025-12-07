import unittest
import sys
import os
import random

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evolutionary_agent import EvolutionaryAgent, ACTION_ALLOW, ACTION_SUPPRESS
from hierarchical_policy_engine import HierarchicalPolicyEngine

class TestEvolutionaryAgent(unittest.TestCase):
    def setUp(self):
        self.engine = HierarchicalPolicyEngine()
        self.agent = EvolutionaryAgent(self.engine, learning_rate=0.1, epsilon=0.0) # Zero epsilon for deterministic testing

    def test_get_state(self):
        path = "test.path"
        features = {'anomaly_score': 0.1, 'entropy': 2.0, 'frequency': 5}
        state = self.agent.get_state(path, features)
        self.assertIsInstance(state, tuple)
        self.assertEqual(len(state), 4)

    def test_choose_action_deterministic(self):
        # With epsilon=0, should choose max Q-value
        state = (1, 0, 0, 0)
        self.agent.q_table[state] = [10.0, 5.0] # Allow > Suppress
        action = self.agent.choose_action(state)
        self.assertEqual(action, ACTION_ALLOW)
        
        self.agent.q_table[state] = [5.0, 10.0] # Suppress > Allow
        action = self.agent.choose_action(state)
        self.assertEqual(action, ACTION_SUPPRESS)

    def test_learn(self):
        state = (1, 0, 0, 0)
        next_state = (2, 0, 0, 0)
        action = ACTION_ALLOW
        reward = 10
        
        # Initial Q-value is 0
        self.agent.learn(state, action, reward, next_state)
        
        # Q(s,a) = 0 + lr * (reward + gamma*max(Q(s')) - 0)
        # Q(s,a) = 0.1 * (10 + 0.9*0 - 0) = 1.0
        q_val = self.agent.q_table[state][action]
        self.assertAlmostEqual(q_val, 1.0)

if __name__ == '__main__':
    unittest.main()
