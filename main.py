import gradio as gr
import os
from embed import embed
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

neo4j_uri = os.getenv("NEO4J_HOST")
neo4j_auth = (os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))


def find(search, k):
    embedded = embed(search)

    with GraphDatabase.driver(neo4j_uri, auth=neo4j_auth) as driver:
        (records, summary, keys) = driver.execute_query(
            """CALL db.index.vector.queryNodes('dataset-embeddings', $k, $embedding) yield node, score
            RETURN node.title AS title, score, labels(node) as labels""",
            embedding=embedded,
            k=k
        )

        return [(
            record["title"],
            [i for i in record["labels"] if i != "Embedded"][0],
            record["score"]
        ) for record in records]


def find_by_type(search, k, entity_type):
    embedded = embed(search)

    with GraphDatabase.driver(neo4j_uri, auth=neo4j_auth) as driver:
        # Unfortunately, we can't use the entity_type parameter directly in the query
        # So, have to increase the limit for the vector search and limit overall output at the end
        # See https://community.neo4j.com/t/vector-search-index-pre-filtered-query/64465
        (records, summary, keys) = driver.execute_query(
            """CALL db.index.vector.queryNodes('dataset-embeddings', 20, $embedding) yield node, score
            where $entity_type in labels(node)
            RETURN node.title AS title, score, labels(node) as labels
            limit $k""",
            embedding=embedded,
            k=k,
            entity_type=entity_type
        )

        return [(
            record["title"],
            [i for i in record["labels"] if i != "Embedded"][0],
            record["score"]
        ) for record in records]


def find_by_children(search, k):
    embedded = embed(search)

    with GraphDatabase.driver(neo4j_uri, auth=neo4j_auth) as driver:
        # TODO - probably we want to include self as well, not only children
        (records, summary, keys) = driver.execute_query(
            """CALL db.index.vector.queryNodes('dataset-embeddings', $k, $embedding) yield node, score
            MATCH (parent) -[:CONTAINS]-> (node)
            RETURN parent.title AS title, score, labels(parent) as labels, node.title AS child_title, labels(node) as child_labels""",
            embedding=embedded,
            k=k
        )

        return [(
            record["title"],
            f"{[i for i in record['child_labels'] if i != 'Embedded'][0]}: {record['child_title']}",
            record["score"]
        ) for record in records]


search_all = gr.Interface(
    fn=find,
    inputs=[
        gr.Textbox(label="Search query"),
        gr.Slider(minimum=1, maximum=30, value=5, step=1, label="Number of results"),
    ],
    outputs=[gr.Dataframe(headers=["Title", "Type", "Score"])],
)

search_by_type = gr.Interface(
    fn=find_by_type,
    inputs=[
        gr.Textbox(label="Search query"),
        gr.Slider(minimum=1, maximum=30, value=5, step=1, label="Number of results"),
        gr.Dropdown(["Dataset", "Fact", "Attribute"], value="Dataset", label="Entity type")
    ],
    outputs=[gr.Dataframe(headers=["Title", "Type", "Score"])],
)

search_by_children = gr.Interface(
    fn=find_by_children,
    inputs=[
        gr.Textbox(label="Search query"),
        gr.Slider(minimum=1, maximum=30, value=5, step=1, label="Number of results"),
    ],
    outputs=[gr.Dataframe(label="Datasets", headers=["Title", "Inclusion reason", "Score"])],

)

demo = gr.TabbedInterface(
    [search_all, search_by_type, search_by_children],
    ["Search All", "Search by Type", "Search by Children"]
)

demo.launch()
