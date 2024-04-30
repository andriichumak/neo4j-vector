import gradio as gr
import os
from embed import embed
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

neo4j_uri = os.getenv("NEO4J_HOST")
neo4j_auth = (os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))


def find(name):
    embedded = embed(name)

    with GraphDatabase.driver(neo4j_uri, auth=neo4j_auth) as driver:
        (records, summary, keys) = driver.execute_query(
            """CALL db.index.vector.queryNodes('dataset-embeddings', 10, $embedding) yield node, score
            RETURN node.title AS title, score, labels(node) as labels""",
            embedding=embedded
        )

        return [(
            record["title"],
            [i for i in record["labels"] if i != "Embedded"][0],
            record["score"]
        ) for record in records]


demo = gr.Interface(
    fn=find,
    inputs=["text"],
    outputs=["dataframe"],
)

demo.launch()
