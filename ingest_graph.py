import os
import pandas as pd
from neo4j import GraphDatabase
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Load credentials from .env file
load_dotenv()
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# In ingest_graph.py

def run_ingestion():
    """Reads the ENRICHED stock list and populates the Neo4j graph."""
    try:
        # --- FIX APPLIED HERE: Use the new, enriched file ---
        df = pd.read_csv("nse_stocks_enriched.csv")
        # ---------------------------------------------------
        df = df.rename(columns={"SYMBOL": "ticker", "NAME OF COMPANY": "name"})
        df = df.dropna(subset=['ticker', 'name', 'sector'])
    except FileNotFoundError:
        logging.error("nse_stocks_enriched.csv not found. Please run enrich_data.py first.")
        return

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    with driver.session() as session:
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Company) REQUIRE c.ticker IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (s:Sector) REQUIRE s.name IS UNIQUE")

        query = """
        UNWIND $rows AS row
        MERGE (c:Company {ticker: row.ticker})
        ON CREATE SET c.name = row.name, c.sector = row.sector
        MERGE (s:Sector {name: row.sector})
        MERGE (c)-[:IN_SECTOR]->(s)
        """
        
        batch_size = 500
        records = df.to_dict('records')
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            session.run(query, rows=batch)
            logging.info(f"Ingested batch {i // batch_size + 1}...")

    driver.close()
    logging.info("Graph ingestion complete.")

    
if __name__ == "__main__":
    run_ingestion()