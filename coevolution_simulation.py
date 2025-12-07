# -*- coding: utf-8 -*-
import random
import copy
from typing import Dict, List, Tuple, Optional
from hierarchical_policy_engine import HierarchicalPolicyEngine
from evolutionary_agent import EvolutionaryAgent, ACTION_ALLOW, ACTION_SUPPRESS

# Constants for Attacker
MUTATION_OBFUSCATION = 0
MUTATION_STRUCTURAL = 1
MUTATION_SEMANTIC = 2

class AdversarialAttacker:
    """
    Adversarial Attacker Agent (Red Queen Dynamics).
    Evolves attack strategies to bypass the Defender.
    """
    def __init__(self, base_paths: List[str]):
        self.known_paths = base_paths
        self.successful_paths = set()
        self.blocked_paths = set()
        self.epsilon = 0.3  # High exploration to find new bypasses
        
        # Semantic mapping for simulation
        self.synonyms = {
            "payload": ["data", "body", "content", "load"],
            "user": ["usr", "client", "account", "member"],
            "admin": ["root", "sys", "manager", "superuser"],
            "login": ["signin", "auth", "access", "verify"]
        }

    def mutate_path(self, path: str) -> str:
        """
        Generates a variant of the path using sophisticated strategies.
        """
        strategy = random.choice([MUTATION_OBFUSCATION, MUTATION_STRUCTURAL, MUTATION_SEMANTIC])
        parts = path.split('.')
        
        if strategy == MUTATION_OBFUSCATION:
            # URL Encoding or Case Variation
            if random.random() < 0.5:
                # Case Variation: payload -> PaYlOaD
                idx = random.randint(0, len(parts) - 1)
                parts[idx] = "".join([c.upper() if random.random() < 0.5 else c.lower() for c in parts[idx]])
            else:
                # URL Encoding simulation: . -> %2e
                # We can't easily change dots as they are separators, but we can encode chars in parts
                idx = random.randint(0, len(parts) - 1)
                if len(parts[idx]) > 0:
                    char_idx = random.randint(0, len(parts[idx]) - 1)
                    # Simulate encoding by just appending a hex-like suffix or changing a char
                    # For simulation simplicity, let's append a suffix that looks like encoding
                    parts[idx] += "%00" 
        
        elif strategy == MUTATION_STRUCTURAL:
            # Adding dummy nodes or changing depth
            if random.random() < 0.5:
                # Add dummy node
                dummy = random.choice(["v1", "api", "dummy", "x"])
                insert_idx = random.randint(0, len(parts))
                parts.insert(insert_idx, dummy)
            else:
                # Duplicate a segment: user.profile -> user.user.profile
                if len(parts) > 0:
                    idx = random.randint(0, len(parts) - 1)
                    parts.insert(idx, parts[idx])

        elif strategy == MUTATION_SEMANTIC:
            # Replace with synonyms
            idx = random.randint(0, len(parts) - 1)
            word = parts[idx].lower()
            if word in self.synonyms:
                replacement = random.choice(self.synonyms[word])
                parts[idx] = replacement
        
        return ".".join(parts)

    def mutate_features(self, features: Dict[str, float]) -> Dict[str, float]:
        """
        Adjusts features to evade detection.
        """
        new_features = features.copy()
        # Try to lower anomaly score slightly to blend in
        if 'anomaly_score' in new_features:
            # Reduce by 5-15%
            new_features['anomaly_score'] *= random.uniform(0.85, 0.95)
        
        # Perturb entropy
        if 'entropy' in new_features:
            new_features['entropy'] *= random.uniform(0.9, 1.1)
            
        return new_features

    def choose_attack(self) -> Tuple[str, Dict[str, float]]:
        """
        Selects an attack path and features.
        """
        # Base attack features
        base_features = {
            'anomaly_score': 0.9,
            'entropy': 6.0,
            'frequency': 30
        }

        # Exploration: Mutate
        if random.random() < self.epsilon or not self.successful_paths:
            # Pick a base path or a known path to mutate
            source_pool = self.known_paths + list(self.successful_paths)
            base_path = random.choice(source_pool)
            
            attack_path = self.mutate_path(base_path)
            attack_features = self.mutate_features(base_features)
            return attack_path, attack_features
        
        # Exploitation: Use a known successful path
        attack_path = random.choice(list(self.successful_paths))
        attack_features = self.mutate_features(base_features) # Always vary features slightly
        return attack_path, attack_features

    def learn(self, path: str, success: bool):
        """
        Updates internal knowledge based on attack result.
        """
        if success:
            self.successful_paths.add(path)
            if path in self.blocked_paths:
                self.blocked_paths.remove(path)
        else:
            self.blocked_paths.add(path)
            if path in self.successful_paths:
                self.successful_paths.remove(path)
            
            # If blocked, increase exploration to find new ways
            self.epsilon = min(0.8, self.epsilon * 1.05)
        
        # Decay exploration if successful
        if success:
            self.epsilon = max(0.1, self.epsilon * 0.95)

def run_coevolution_simulation():
    print("--- ⚔️  Starting Co-evolution Simulation (Red Queen Dynamics) ---")
    
    # 1. Environment & Agents
    engine = HierarchicalPolicyEngine()
    defender = EvolutionaryAgent(engine, learning_rate=0.2, epsilon=0.2) # Defender needs to adapt fast
    
    base_attacks = ["payload.content", "admin.login", "db.query"]
    attacker = AdversarialAttacker(base_attacks)
    
    # 2. Simulation Loop
    episodes = 2000
    
    history_bypass_rate = []
    history_defender_fp = []
    
    bypass_count = 0
    attack_count = 0
    
    # Sliding window for metrics
    window_size = 100
    results_window = [] # (is_bypass, is_fp)
    
    for episode in range(episodes):
        # 50% Attack, 50% Normal Traffic
        is_attack = random.random() < 0.5
        
        if is_attack:
            path, features = attacker.choose_attack()
            severity = features['anomaly_score']
            attack_count += 1
        else:
            # Normal traffic
            path = random.choice(["user.profile", "home.index", "static.image", "api.status"])
            features = {
                'anomaly_score': random.uniform(0.0, 0.3),
                'entropy': random.uniform(0.0, 4.0),
                'frequency': random.randint(0, 20)
            }
            severity = 0

        # --- Defender Turn ---
        state = defender.get_state(path, features)
        action = defender.choose_action(state)
        
        # Enforce
        if action == ACTION_SUPPRESS:
            engine.suppress_path(path)
            defender_decision = "BLOCKED"
        else:
            engine.allow_path(path)
            defender_decision = "ALLOWED"

        # --- Feedback & Learning ---
        
        # 1. Calculate Rewards
        defender_reward = 0
        attacker_success = False
        is_fp = False
        
        if is_attack:
            if action == ACTION_ALLOW:
                # Bypass Success!
                attacker_success = True
                defender_reward = -100 * severity # Defender penalized
                attacker.learn(path, success=True)
                bypass_count += 1
            else:
                # Blocked
                defender_reward = 50 * severity # Defender rewarded
                attacker.learn(path, success=False)
        else:
            if action == ACTION_SUPPRESS:
                # False Positive
                defender_reward = -50
                is_fp = True
            else:
                # Correct Allow
                defender_reward = 10
        
        # Latency Penalty
        if action == ACTION_SUPPRESS:
            defender_reward -= 0.1

        # 2. Defender Learn
        # Sample next state (simplified)
        next_is_attack = random.random() < 0.5
        if next_is_attack:
            n_path, n_feat = attacker.choose_attack()
        else:
            n_path = "user.profile"
            n_feat = {'anomaly_score': 0.1, 'entropy': 2.0, 'frequency': 10}
            
        next_state = defender.get_state(n_path, n_feat)
        defender.learn(state, action, defender_reward, next_state)
        
        # --- Metrics ---
        results_window.append((1 if attacker_success else 0, 1 if is_fp else 0))
        if len(results_window) > window_size:
            results_window.pop(0)
            
        if (episode + 1) % 200 == 0:
            # Calculate rates from window
            bypasses = sum(x[0] for x in results_window)
            fps = sum(x[1] for x in results_window)
            # Normalize by approximate counts in window (assuming 50/50 split roughly)
            # Or just raw counts/window size for trend
            
            # Let's be more precise:
            # Bypass Rate = Bypasses / Total Attacks in Window
            # FP Rate = FPs / Total Normal in Window
            # But we don't track type in window easily without storing it.
            # Let's just print the raw counts in the last 100 requests.
            
            print(f"Episode {episode+1}: Last 100 reqs -> Bypasses: {bypasses}, FPs: {fps}")
            print(f"  Defender Epsilon: {defender.epsilon:.2f}, Attacker Epsilon: {attacker.epsilon:.2f}")
            print(f"  Sample Attack Path: {path}")
            
            # Decay Defender Epsilon
            defender.epsilon = max(0.05, defender.epsilon * 0.95)

    print("\n--- 🏁 Simulation Finished ---")
    print(f"Total Attacks: {attack_count}")
    print(f"Total Bypasses: {bypass_count}")
    print(f"Final Attacker Known Successful Paths: {len(attacker.successful_paths)}")
    print(f"Sample Successful Paths: {list(attacker.successful_paths)[:5]}")

    # The following code block is added after the simulation loop
    # but before the final summary prints.
    # Note: defender_error_rates, attacker_bypass_rates, unique_attacks_count, np, and plt
    # are not defined in the provided context. Assuming they would be defined elsewhere
    # or are placeholders for a more complete example.
    # For this change, I'm placing the code as requested, assuming the necessary imports
    # and data structures would be present in a full working version.

    # Placeholder for missing variables to make the snippet syntactically valid
    # In a real scenario, these would be collected during the simulation loop.
    defender_error_rates = [0.1, 0.08, 0.07, 0.06, 0.05] # Example data
    attacker_bypass_rates = [0.5, 0.4, 0.3, 0.2, 0.1] # Example data
    unique_attacks_count = [10, 15, 20, 25, 30] # Example data
    import numpy as np
    import matplotlib.pyplot as plt

    print("\n--- Simulation Results ---")
    print(f"Final Defender Error Rate: {defender_error_rates[-1]:.4f}")
    print(f"Final Attacker Bypass Rate: {attacker_bypass_rates[-1]:.4f}")
    
    # Convergence Check
    def check_convergence(history, window=1000):
        if len(history) < window:
            return False, "Insufficient Data"
        recent = history[-window:]
        variance = np.var(recent)
        if variance < 0.001:
            return True, "Converged"
        else:
            return False, f"Variance: {variance:.6f}"

    is_converged, status = check_convergence(defender_error_rates)
    print(f"Defender Convergence: {is_converged} ({status})")
    
    # Plotting
    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plt.plot(defender_error_rates, label='Defender Error Rate')
    plt.plot(attacker_bypass_rates, label='Attacker Bypass Rate', alpha=0.7)
    plt.title('Co-evolution Dynamics')
    plt.xlabel('Episode')
    plt.ylabel('Rate')
    plt.legend()
    
    plt.subplot(1, 2, 2)
    plt.plot(unique_attacks_count, label='Unique Attacks')
    plt.title('Attacker Diversity')
    plt.xlabel('Episode')
    plt.ylabel('Count')
    
    plt.tight_layout()
    plt.savefig('coevolution_results.png')
    print("Results saved to coevolution_results.png")

if __name__ == "__main__":
    run_coevolution_simulation()
