# Symbiosis: Adaptive Security Framework

**Symbiosis** is a next-generation adaptive security framework inspired by biological immune systems and epigenetic mechanisms. It is designed to evolve in real-time, defending against sophisticated, mutating adversaries through "Epigenetic Symbiosis" and "Red Queen Dynamics".

## 🧬 Core Concepts

### 1. Epigenetic Policy Engine
A hierarchical Trie-based enforcement engine that manages security policies like gene expression.
- **Gene Expression (Allow)**: Whitelisting known good paths.
- **Methylation (Suppress)**: Suppressing specific paths (vulnerabilities) without altering the underlying code.
- **Transduction**: Sharing immunity (suppression rules) between distinct service engines.

### 2. Evolutionary Agent (The Defender)
A Reinforcement Learning (RL) agent that interacts with traffic to learn optimal security policies.
- **Algorithm**: Q-Learning with Epsilon-Greedy exploration.
- **State**: Abstracted traffic features (Path Structure, Anomaly Score, Entropy, Frequency).
- **Goal**: Minimize False Positives and False Negatives by dynamically adjusting the policy.

### 3. Red Queen Dynamics (Co-evolution)
A simulation of the arms race between the Defender and an **Adversarial Attacker**.
- **Attacker**: Mutates attack vectors using Obfuscation, Structural changes, and Semantic variations to bypass defenses.
- **Defender**: Adapts to new mutations, forcing the attacker to evolve further.

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- No external heavy dependencies (Standard Library + `random`, `math`)

### Installation
```bash
git clone https://github.com/pjy010218/Cloud_Leukocyte.git
cd Cloud_Leukocyte
```

## 🧪 Simulations

### 1. Evolutionary Agent Training
Train the Defender agent against a stream of traffic.
```bash
python3 evolutionary_agent.py
```
*Output: Convergence metrics showing reduced error rates over 1000 episodes.*

### 2. Co-evolution (Red Queen) Simulation
Run the full adversarial simulation where Attacker and Defender evolve together.
```bash
python3 coevolution_simulation.py
```
*Output: Real-time logs of bypass attempts, successful mutations, and defender adaptation.*

## 📂 Project Structure

- `hierarchical_policy_engine.py`: Core Trie-based policy engine.
- `evolutionary_agent.py`: RL-based Defender agent.
- `coevolution_simulation.py`: Adversarial Attacker and Co-evolution loop.
- `policy_compiler.py`: Utilities for compiling policies.

## 🔬 Research Goals
This project aims to prove that **Self-Evolving Security Systems** can outperform static rule-based systems by:
1. Reducing the window of vulnerability (Zero-Day defense).
2. Adapting to novel attack patterns without human intervention.
3. Maintaining high availability (low False Positives) during active attacks.

---
*Part of the Cloud Leukocyte Research Initiative.*