import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

neo4j_uri = os.getenv("NEO4J_HOST")
neo4j_auth = (os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))


def kill_all():
    with GraphDatabase.driver(neo4j_uri, auth=neo4j_auth) as driver:
        driver.execute_query("match (a) -[r] -> () delete a, r")
        driver.execute_query("match (a) delete a")
        driver.execute_query("DROP INDEX `dataset-embeddings` IF EXISTS")


if __name__ == "__main__":
    kill_all()
