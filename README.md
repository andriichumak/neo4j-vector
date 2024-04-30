# Testing Graph database

Requirements:
1. Running neo4j server (I used Docker locally, but can be a cloud as well).
2. Install dependencies with Poetry.
3. Copy `.env.template` to `.env` and fill it with your data.
4. Run `python ./build.py` to generate, embed and index the graph database.
5. Run `python ./kill_all.py` in case you want to drop all items in DB.
6. Run `python ./main.py` to start Gradio server with the demo.
