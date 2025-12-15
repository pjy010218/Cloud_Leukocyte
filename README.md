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

### 4. Adaptive Policy Engine
A mechanism for handling legitimate Schema Evolution (False Positive reduction).
- **Grace Period**: New fields are monitored for stability before whitelisting.
- **Result**: Reduced block rate for new fields from 100% to <5% while maintaining security.

### 5. High-Performance Optimizations
- **Cython/C++ Engine**: Rewrote the core Trie engine in C++ (wrapped in Cython) for ~2x speedup in intersection.
- **Compile-to-Flat**: Flattens the hierarchical policy into an **O(1) Hash Map** for the Data Plane, achieving **~14x speedup** (0.068 µs lookup).

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Cython (`apt install cython3` or `pip install cython`)
- C++ Compiler (GCC/Clang)

### Installation
```bash
git clone https://github.com/pjy010218/Cloud_Leukocyte.git
cd Cloud_Leukocyte
# Build Cython Extension
python3 setup.py build_ext --inplace
```

## 🧪 Experiments & Simulations

You can run the full suite of experiments using the master script:
```bash
./run_all_experiments.sh
```

### Individual Components:

**1. Evolutionary Agent Training**
```bash
python3 evolutionary_agent.py
```

**2. Co-evolution (Red Queen) Simulation**
```bash
python3 coevolution_simulation.py
```

**3. Enhanced Attack Simulation (Adaptive)**
Tests the system against obfuscation, synonym, and schema evolution attacks.
```bash
python3 attack_simulation_ENHANCED.py
```

**4. Performance Benchmarks**
Compare Python, Cython, and Flat Set performance.
```bash
python3 benchmark/policy_benchmark_FIXED.py
python3 benchmark/policy_benchmark_CYTHON.py
```

## 📂 Project Structure

- `hierarchical_policy_engine.py`: Pure Python Trie engine (Reference).
- `hierarchical_policy_engine_cython.pyx`: **Optimized Cython/C++ Engine**.
- `node.h`: C++ Node definition for the engine.
- `adaptive_policy_engine.py`: Handling Schema Evolution.
- `evolutionary_agent.py`: RL-based Defender.
- `coevolution_simulation.py`: Adversarial Dynamics.
- `policy_compiler.py`: Compiles Trie to O(1) Hash Map.
- `tests/`: Unit tests (includes flattening verification).

## 🔬 Research Findings
1.  **Self-Evolving**: The RL agent successfully converges to low error rates even against mutating attackers.
2.  **Adaptive**: The Grace Period mechanism solves the "Schema Evolution" False Positive problem.
3.  **Performant**: The "Compile-to-Flat" strategy allows us to have **Hierarchical Flexibility** in control and **O(1) Speed** in enforcement.

---
*Part of the Cloud Leukocyte Research Initiative.*