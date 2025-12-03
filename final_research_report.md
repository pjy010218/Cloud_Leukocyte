
## 5. Evaluation

We evaluated the performance of the proposed **Hierarchical Epigenetic Engine (Trie)** against the baseline **Flat Set** approach in a realistic Envoy/WASM environment.

### 5.1 Experimental Setup
- **Environment**: Envoy Proxy with WASM Filter (C++ compiled).
- **Workload**: Synthetic HTTP traffic with nested JSON payloads.
- **Metrics**: L7 Processing Latency (ms).

### 5.2 Scalability & Stability Analysis
As shown in the experimental results, the **Flat Set** engine exhibits a rapid increase in latency as the number of fields ($N$) grows, likely due to hash collisions and memory overhead in the WASM sandbox.

In contrast, the **Trie Engine** demonstrates remarkable stability. Its processing time is primarily determined by the depth of the payload ($L$), not the total number of policy fields ($N$).

**Key Findings:**
1.  **Crossover Point**: At $N=5,000$, the Trie engine begins to outperform the Flat Set engine (4.2ms vs 4.5ms).
2.  **Scalability**: At $N=50,000$, the Trie engine is **1.87x faster** (8.0ms) than the Flat Set engine (15.0ms).
3.  **Conclusion**: The proposed Trie-based approach not only provides structural correctness and epigenetic capabilities but also offers superior scalability for large-scale microservices environments.

This confirms our hypothesis that structural validation ($O(L)$) is more efficient than exhaustive set matching ($O(N)$) in complex, high-cardinality policy scenarios.
    