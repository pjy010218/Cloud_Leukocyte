# -*- coding: utf-8 -*-
import random
from typing import Dict, List, Tuple, Optional
from hierarchical_policy_engine import HierarchicalPolicyEngine, TrieNode

# Constants for Actions
ACTION_ALLOW = 0
ACTION_SUPPRESS = 1

# Constants for Feature Quantization
ANOMALY_LOW = 0
ANOMALY_MED = 1
ANOMALY_HIGH = 2

ENTROPY_LOW = 0
ENTROPY_HIGH = 1

FREQ_LOW = 0
FREQ_HIGH = 1

class EvolutionaryAgent:
    """
    RL-Based Evolutionary Agent using Q-Learning.
    Evolves security policy by interacting with traffic.
    """
    def __init__(self, engine: HierarchicalPolicyEngine, 
                 learning_rate=0.1, discount_factor=0.9, epsilon=0.1):
        self.engine = engine
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = epsilon
        
        # Q-Table: {(State): [Q_ALLOW, Q_SUPPRESS]}
        # State: (TrieNodeID, AnomalyBin, EntropyBin, FreqBin)
        self.q_table: Dict[Tuple[int, int, int, int], List[float]] = {}

    def get_state(self, path: str, features: Dict[str, float]) -> Tuple[int, int, int, int]:
        """
        Constructs the state from path and features.
        State = (TrieNodeID, Quantized_Anomaly, Quantized_Entropy, Quantized_Frequency)
        """
        # 1. Path Abstraction: Get Trie Node ID
        # We need to traverse the Trie to find the node. 
        # If it doesn't exist, we might need to simulate its existence or use a default "Unknown" node ID.
        # For this simulation, we assume the engine creates nodes as we access them (or we create them here).
        # To avoid modifying the engine's state purely for observation, we should check existence.
        # However, allow/suppress actions WILL create nodes.
        # Let's use a helper to get or create the node ID for the sake of state stability.
        node = self._get_or_create_node(path)
        node_id = id(node)

        # 2. Feature Quantization
        anomaly = features.get('anomaly_score', 0.0)
        if anomaly < 0.3:
            q_anomaly = ANOMALY_LOW
        elif anomaly < 0.7:
            q_anomaly = ANOMALY_MED
        else:
            q_anomaly = ANOMALY_HIGH

        entropy = features.get('entropy', 0.0)
        q_entropy = ENTROPY_LOW if entropy < 4.0 else ENTROPY_HIGH

        frequency = features.get('frequency', 0.0)
        q_freq = FREQ_LOW if frequency < 10 else FREQ_HIGH

        return (node_id, q_anomaly, q_entropy, q_freq)

    def _get_or_create_node(self, path: str) -> TrieNode:
        """Helper to get the TrieNode for a path, creating it if necessary."""
        node = self.engine.root
        if not path:
            return node
        parts = path.split('.')
        for part in parts:
            if part not in node.children:
                node.children[part] = TrieNode()
            node = node.children[part]
        return node

    def choose_action(self, state: Tuple[int, int, int, int]) -> int:
        """Epsilon-Greedy Action Selection."""
        if state not in self.q_table:
            self.q_table[state] = [0.0, 0.0]

        if random.random() < self.epsilon:
            return random.choice([ACTION_ALLOW, ACTION_SUPPRESS])
        
        q_values = self.q_table[state]
        # If Q-values are equal, choose randomly to avoid bias
        if q_values[ACTION_ALLOW] == q_values[ACTION_SUPPRESS]:
            return random.choice([ACTION_ALLOW, ACTION_SUPPRESS])
        
        return q_values.index(max(q_values))

    def learn(self, state: Tuple[int, int, int, int], action: int, reward: float, next_state: Tuple[int, int, int, int]):
        """Q-Learning Update."""
        if state not in self.q_table:
            self.q_table[state] = [0.0, 0.0]
        if next_state not in self.q_table:
            self.q_table[next_state] = [0.0, 0.0]

        predict = self.q_table[state][action]
        target = reward + self.gamma * max(self.q_table[next_state])
        self.q_table[state][action] += self.lr * (target - predict)

def run_evolutionary_simulation():
    print("--- 🧬 Starting Evolutionary Agent Simulation ---")
    
    # 1. Environment Setup
    engine = HierarchicalPolicyEngine()
    agent = EvolutionaryAgent(engine)
    
    # 2. Simulation Parameters
    episodes = 1000
    
    # Metrics
    false_positives = 0
    false_negatives = 0
    total_attacks = 0
    total_legit = 0
    
    history_fp = []
    history_fn = []

    # Traffic Patterns
    # Normal: Low Anomaly, Low/High Entropy, Low/High Freq
    # Attack: High Anomaly, High Entropy (often), High Freq (sometimes)
    
    for episode in range(episodes):
        # Generate Traffic
        is_attack = random.random() < 0.3 # 30% Attack Traffic
        
        if is_attack:
            path = random.choice(["payload.content", "user.input", "db.query"])
            features = {
                'anomaly_score': random.uniform(0.6, 1.0), # High Anomaly
                'entropy': random.uniform(3.5, 8.0),       # Higher Entropy
                'frequency': random.randint(5, 50)
            }
            severity = features['anomaly_score'] # Use anomaly score as severity
            total_attacks += 1
        else:
            path = random.choice(["user.profile", "home.index", "static.image"])
            features = {
                'anomaly_score': random.uniform(0.0, 0.4), # Low Anomaly
                'entropy': random.uniform(0.0, 4.5),
                'frequency': random.randint(0, 20)
            }
            severity = 0
            total_legit += 1

        # 1. Observe State
        state = agent.get_state(path, features)
        
        # 2. Choose Action
        action = agent.choose_action(state)
        
        # 3. Enforce Action (Simulation)
        # In a real system, we would call engine.allow_path or engine.suppress_path
        # But here, the action is per-packet decision. 
        # The engine's state (allow/suppress) acts as the "Policy" that the agent is building.
        # If Agent chooses SUPPRESS, we call engine.suppress_path(path).
        # If Agent chooses ALLOW, we call engine.allow_path(path).
        
        if action == ACTION_SUPPRESS:
            engine.suppress_path(path)
            decision = "BLOCKED"
        else:
            engine.allow_path(path)
            decision = "ALLOWED"

        # 4. Calculate Reward
        reward = 0
        
        if is_attack:
            if action == ACTION_SUPPRESS:
                # Correct Suppress
                reward = 50 * severity
            else:
                # False Negative (Missed Attack)
                reward = -100 * severity
                false_negatives += 1
        else:
            if action == ACTION_ALLOW:
                # Correct Allow
                reward = 10
            else:
                # False Positive (Blocked Normal)
                reward = -50
                false_positives += 1
        
        # Latency Penalty for Suppression
        if action == ACTION_SUPPRESS:
            reward -= 0.1

        # 5. Learn
        # Next state is effectively the same path/features for this simplified packet-based sim,
        # or we could sample the NEXT packet. 
        # Q-Learning assumes we transition to a new state. 
        # Let's assume the next state is a new random packet (independent samples).
        # For the sake of the update, we generate a dummy next state or just use the current one 
        # if we treat this as a terminal state for the "packet processing" episode.
        # Actually, let's just use the same state as 'next_state' implies the policy's effect on future.
        # But since traffic is IID (Independent Identically Distributed) in this simple sim, 
        # 'next_state' doesn't depend on 'action'.
        # We will just sample a new random packet for next_state to follow standard Q-learning form.
        
        # Sample next packet (simplified)
        next_is_attack = random.random() < 0.3
        if next_is_attack:
            n_path = random.choice(["payload.content", "user.input", "db.query"])
            n_feat = {'anomaly_score': 0.8, 'entropy': 5.0, 'frequency': 20}
        else:
            n_path = random.choice(["user.profile", "home.index", "static.image"])
            n_feat = {'anomaly_score': 0.2, 'entropy': 2.0, 'frequency': 5}
            
        next_state = agent.get_state(n_path, n_feat)
        
        agent.learn(state, action, reward, next_state)
        
        # Logging every 100 episodes
        if (episode + 1) % 100 == 0:
            fp_rate = false_positives / total_legit if total_legit > 0 else 0
            fn_rate = false_negatives / total_attacks if total_attacks > 0 else 0
            history_fp.append(fp_rate)
            history_fn.append(fn_rate)
            print(f"Episode {episode+1}: FP Rate={fp_rate:.2f}, FN Rate={fn_rate:.2f}, Epsilon={agent.epsilon:.2f}")
            
            # Decay Epsilon
            agent.epsilon = max(0.01, agent.epsilon * 0.95)
            
            # Reset counters for interval stats (optional, but cumulative is requested to show convergence)
            # Actually, let's keep cumulative to show overall performance, 
            # or reset to show "current" performance. 
            # Resetting gives a better view of "learning progress".
            false_positives = 0
            false_negatives = 0
            total_attacks = 0
            total_legit = 0

    print("\n--- 📊 Final Results ---")
    print("Final Q-Table Sizes:", len(agent.q_table))
    print("Sample Q-Values (payload.content):")
    
    # Check a specific path state
    # We need to reconstruct the state to query q_table.
    # Let's just iterate and print a few.
    for i, (state, q_vals) in enumerate(agent.q_table.items()):
        if i > 5: break
        print(f"State {state}: Allow={q_vals[0]:.2f}, Suppress={q_vals[1]:.2f}")

if __name__ == "__main__":
    run_evolutionary_simulation()
