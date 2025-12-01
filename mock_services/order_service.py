import requests
import time
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TARGET_URL = "http://inventory-service:8080/api/v1/inventory/reserve"

def generate_traffic():
    while True:
        # Scenario 1: Legitimate Traffic
        payload_legit = {
            "order_amount": random.randint(10, 100),
            "sku": f"ITEM-{random.randint(1000, 9999)}"
        }
        try:
            resp = requests.post(TARGET_URL, json=payload_legit)
            logger.info(f"Sent Legit: {resp.status_code}")
        except Exception as e:
            logger.error(f"Failed to send: {e}")

        # Scenario 2: PII Leakage (Should be blocked by Symbiosis later)
        if random.random() < 0.3: # 30% chance
            payload_pii = {
                "order_amount": random.randint(10, 100),
                "sku": f"ITEM-{random.randint(1000, 9999)}",
                "customer_pii": "sensitive-data"
            }
            try:
                resp = requests.post(TARGET_URL, json=payload_pii)
                logger.info(f"Sent PII: {resp.status_code}")
            except Exception as e:
                logger.error(f"Failed to send PII: {e}")
        
        time.sleep(2)

if __name__ == "__main__":
    logger.info("Starting Order Service (Traffic Generator)...")
    # Wait for target to be ready
    time.sleep(5) 
    generate_traffic()
