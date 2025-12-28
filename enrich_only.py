from neo4j import GraphDatabase

NEO4J_URI = "bolt://localhost:7688"
NEO4J_AUTH = ("neo4j", "cve_password")

def enrich_with_boutique_data(driver):
    """
    Manually injects Online Boutique service topology and dependency mappings
    to simulate a real environment where 'BillingService' uses 'log4j'.
    """
    print("   🎨 Enriching Graph with Online Boutique Topology...")
    query = """
    // 1. Define Services and their Exposed Paths (e.g., User-Agent header)
    MERGE (s1:Service {id: "AdService"})
    SET s1.exposed_paths = ["User-Agent", "payload.content"]
    
    MERGE (s2:Service {id: "BillingService"})
    SET s2.exposed_paths = ["User-Agent", "checkout.header"]
    
    MERGE (s3:Service {id: "LogService"})
    SET s3.exposed_paths = ["User-Agent", "payload.content"]
    
    // 2. Define the Vulnerable Library (log4j)
    MERGE (p:Product {name: "log4j"})
    
    // 3. Link Services to the Library
    MERGE (s1)-[:DEPENDS_ON]->(p)
    MERGE (s2)-[:DEPENDS_ON]->(p)
    MERGE (s3)-[:DEPENDS_ON]->(p)
    
    // 4. Ensure Log4j is linked to the critical CVE (CVE-2021-44228) and CWE-502
    MERGE (cve:CVE {id: "CVE-2021-44228"})
    SET cve.description = "Apache Log4j2 JNDI features..."
    
    MERGE (cve)-[:AFFECTS]->(p)
    
    MERGE (wk:Weakness {description: "CWE-502: Deserialization of Untrusted Data"})
    MERGE (cve)-[:HAS_WEAKNESS]->(wk)

    // 5. Spring4Shell Data (CartService)
    // Keywords: class.module, classLoader
    MERGE (p2:Product {name: "Spring Framework"})
    MERGE (cve2:CVE {id: "CVE-2022-22965"})
    SET cve2.description = "Spring4Shell RCE", cve2.keywords = ["class.module", "classLoader"], cve2.severity = 9.8
    MERGE (wk2:Weakness {description: "CWE-94: Improper Control of Generation of Code"})
    MERGE (p2)-[:AFFECTED_BY]->(cve2)
    MERGE (cve2)-[:AFFECTS]->(p2)
    MERGE (cve2)-[:HAS_WEAKNESS]->(wk2)

    MERGE (s4:Service {id: "CartService"})
    SET s4.exposed_paths = ["payload.data", "POST_BODY"]
    MERGE (s4)-[:DEPENDS_ON]->(p2)

    // 6. libcurl Heap Overflow (Frontend)
    // Keywords: socks5h, hostname_overflow
    MERGE (p3:Product {name: "libcurl"})
    MERGE (cve3:CVE {id: "CVE-2023-38545"})
    SET cve3.description = "libcurl SOCKS5 Heap Buffer Overflow", cve3.keywords = ["socks5h", "hostname_overflow"], cve3.severity = 9.8
    MERGE (wk3:Weakness {description: "CWE-122: Heap-based Buffer Overflow"})
    MERGE (p3)-[:AFFECTED_BY]->(cve3)
    MERGE (cve3)-[:AFFECTS]->(p3)
    MERGE (cve3)-[:HAS_WEAKNESS]->(wk3)

    MERGE (s5:Service {id: "Frontend"})
    SET s5.exposed_paths = ["proxy_url", "target_host"]
    MERGE (s5)-[:DEPENDS_ON]->(p3)
    """
    try:
        with driver.session() as session:
            session.run(query)
        print("   ✅ Boutique Data Enriched with Multi-Vector CVEs (Log4Shell, Spring4Shell, libcurl)")
    except Exception as e:
        print(f"   [!] Enrichment Failed: {e}")

if __name__ == "__main__":
    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
    try:
        enrich_with_boutique_data(driver)
    finally:
        driver.close()
