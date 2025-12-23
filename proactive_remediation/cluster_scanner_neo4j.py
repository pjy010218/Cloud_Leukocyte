# -*- coding: utf-8 -*-
from neo4j import GraphDatabase
from typing import List, Dict, Any

class ClusterScannerNeo4j:
    """
    Immune Surveillance Component (Phase 24):
    Uses Neo4j Knowledge Graph to identify vulnerable services based on attack signatures.
    """
    def __init__(self, uri: str = "bolt://localhost:7687", auth: tuple = ("neo4j", "cve_password")):
        self.driver = GraphDatabase.driver(uri, auth=auth)

    def close(self):
        self.driver.close()

    def scan_via_graph(self, signature: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Scans the Neo4j graph for services vulnerable to the given attack signature.
        """
        # 1. Extract CWE ID from signature (assuming finding CWE is the key)
        # The signature might contain "CWE-xxx" in identifiers or we might need to look it up.
        # For this phase, we assume the signature *contains* a CWE or we derive it.
        # Let's assume static_indicators or a new field 'related_cwe' has it.
        cwe_id = signature.get('related_cwe')
        
        # Fallback: try to find CWE in static indicators
        if not cwe_id:
            for ind in signature.get('static_indicators', []):
                if ind.startswith('CWE-'):
                    cwe_id = ind.split(':')[0]
                    break
        
        vulnerable_services = []
        target_path = signature['vulnerable_path']

        # Query Logic:
        # Find Services that expose the target_path AND depend on a library that is affected by a CVE with the given CWE.
        # We assume a schema: (Service)-[:DEPENDS_ON]->(Product/Library)<-[:AFFECTS]-(CVE)-[:HAS_WEAKNESS]->(Weakness)
        # Note: In real world, version checking is needed. For this simulation, 
        # we simplify: if it depends on a product that has *a* CVE with this CWE, flag it (High Sensitivity).
        
        query = """
        MATCH (s:Service)
        WHERE $path IN s.exposed_paths
        MATCH (s)-[:DEPENDS_ON]->(p:Product)<-[:AFFECTS]-(cve:CVE)-[:HAS_WEAKNESS]->(w:Weakness)
        WHERE w.description STARTS WITH $cwe_id OR w.description CONTAINS $cwe_id
        RETURN DISTINCT s.id AS service_id, p.name AS vulnerable_lib, cve.id AS cve_id
        """
        
        # If no CWE is known, we might scan by CVE if available
        # But per prompt, "Cypher Query: ...CWE ID..."
        
        if not cwe_id:
            print("[SCANNER INFO] No CWE ID in signature. Skipping Graph Scan.")
            return []

        print(f"[SCANNER] Executing Graph Query for CWE: {cwe_id} on path: {target_path}")

        try:
            with self.driver.session() as session:
                result = session.run(query, path=target_path, cwe_id=cwe_id)
                for record in result:
                    vulnerable_services.append({
                        "service_id": record["service_id"],
                        "reason": "GRAPH_CORRELATION",
                        "path_match": target_path,
                        "vulnerable_lib": record["vulnerable_lib"],
                        "related_cve": record["cve_id"],
                        "hardening_needed": True
                    })
        except Exception as e:
            print(f"[SCANNER ERROR] Neo4j Query Failed: {e}")

        return vulnerable_services
