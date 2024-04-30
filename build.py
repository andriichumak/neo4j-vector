import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
from gooddata_sdk import GoodDataSdk
from embed import embed_entity

load_dotenv()

gd_host = os.getenv("GD_HOST")
gd_token = os.getenv("GD_TOKEN")
gd_workspace = os.getenv("GD_WORKSPACE")

neo4j_uri = os.getenv("NEO4J_HOST")
neo4j_auth = (os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))


def main():
    with GraphDatabase.driver(neo4j_uri, auth=neo4j_auth) as driver:
        print("Verifying NEO4J connectivity...")
        driver.verify_connectivity()

        # Fetch all datasets
        sdk = GoodDataSdk.create(gd_host, gd_token)
        print("Loading declarative LDM...")
        declarative_ldm = sdk.catalog_workspace_content.get_declarative_ldm(workspace_id=gd_workspace)

        for dataset in declarative_ldm.ldm.datasets:
            store_dataset(dataset, driver)

        for dataset in declarative_ldm.ldm.datasets:
            apply_references(dataset, driver)

        driver.execute_query(
            """CREATE VECTOR INDEX `dataset-embeddings`
            FOR (n: Embedded) ON (n.embedding)
            OPTIONS {indexConfig: {
                `vector.dimensions`: 768,
                `vector.similarity_function`: 'cosine'
            }}"""
        )


def store_dataset(dataset, driver):
    print(f"Adding dataset: {dataset.title}")
    driver.execute_query(
        """CREATE (d:Dataset:Embedded {
           id: $id,
           title: $title,
           description: $description
        })""",
        id=dataset.id,
        title=dataset.title,
        description=dataset.description
    )

    driver.execute_query(
        """MATCH (d:Dataset {id: $id})
        CALL db.create.setNodeVectorProperty(d, 'embedding', $embedding)
        RETURN d""",
        id=dataset.id,
        embedding=embed_entity(dataset)
    )

    for fact in dataset.facts:
        store_fact(dataset.id, fact, driver)

    for attr in dataset.attributes:
        store_attribute(dataset.id, attr, driver)


def store_fact(ds_id, fact, driver):
    print(f"\tAdding fact: {fact.title}")
    driver.execute_query(
        """MATCH (d:Dataset {id: $ds_id})
        CREATE (f:Fact:Embedded {
           id: $id,
           title: $title,
           description: $description
        })
        MERGE (d)-[:CONTAINS]->(f)""",
        ds_id=ds_id,
        id=fact.id,
        title=fact.title,
        description=fact.description,
        tags=fact.tags
    )

    driver.execute_query(
        """MATCH (f:Fact {id: $id})
        CALL db.create.setNodeVectorProperty(f, 'embedding', $embedding)
        RETURN f""",
        id=fact.id,
        embedding=embed_entity(fact)
    )


def store_attribute(ds_id, attr, driver):
    print(f"\tAdding attribute: {attr.title}")
    driver.execute_query(
        """MATCH (d:Dataset {id: $ds_id})
        CREATE (f:Attribute:Embedded {
           id: $id,
           title: $title,
           description: $description
        })
        MERGE (d)-[:CONTAINS]->(f)""",
        ds_id=ds_id,
        id=attr.id,
        title=attr.title,
        description=attr.description,
        tags=attr.tags
    )

    driver.execute_query(
        """MATCH (a:Attribute {id: $id})
        CALL db.create.setNodeVectorProperty(a, 'embedding', $embedding)
        RETURN a""",
        id=attr.id,
        embedding=embed_entity(attr)
    )


def apply_references(dataset, driver):
    for reference in dataset.references:
        referenced_id = reference.identifier.id
        print(f"Applying reference: {dataset.id} => {referenced_id}")
        driver.execute_query(
            """MATCH (d1:Dataset {id: $from_id})
            MATCH (d2:Dataset {id: $to_id})
            CREATE (d1)-[:REFERENCES]->(d2)""",
            from_id=dataset.id,
            to_id=referenced_id
        )


if __name__ == "__main__":
    main()
