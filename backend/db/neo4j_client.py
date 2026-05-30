import os
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables from backend/.env
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Neo4jClient:
    def __init__(self, uri=None, user=None, password=None):
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        # Aura free-tier on some networks has self-signed intermediate certs;
        # neo4j+ssc:// skips full chain verification while still encrypting.
        if self.uri.startswith("neo4j+s://"):
            self.uri = self.uri.replace("neo4j+s://", "neo4j+ssc://")
        self.user = user or os.getenv("NEO4J_USERNAME", os.getenv("NEO4J_USER", "neo4j"))
        self.password = password or os.getenv("NEO4J_PASSWORD", "password")
        self.database = os.getenv("NEO4J_DATABASE", "neo4j")
        self.driver = None

        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # Verify connectivity by running a trivial query on the target database
            with self.driver.session(database=self.database) as session:
                session.run("RETURN 1").consume()
            print(f"[Neo4j] Successfully connected to {self.uri} (db={self.database})")
        except Exception as e:
            print(f"[Neo4j] Failed to connect to Neo4j at {self.uri}: {e}")
            self.driver = None

    def close(self):
        if self.driver is not None:
            self.driver.close()

    def execute_write(self, query, parameters=None):
        """Execute a write transaction."""
        if not self.driver:
            raise Exception("Neo4j driver not initialized.")
        with self.driver.session(database=self.database) as session:
            return session.execute_write(self._execute_tx, query, parameters)

    def execute_read(self, query, parameters=None):
        """Execute a read transaction."""
        if not self.driver:
            raise Exception("Neo4j driver not initialized.")
        with self.driver.session(database=self.database) as session:
            return session.execute_read(self._execute_tx, query, parameters)

    @staticmethod
    def _execute_tx(tx, query, parameters):
        result = tx.run(query, parameters or {})
        return [record for record in result]
