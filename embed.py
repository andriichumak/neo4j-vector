from typing import List

from transformers import AutoModel

# trust_remote_code is needed to use the encode method
model = AutoModel.from_pretrained('jinaai/jina-embeddings-v2-base-en', trust_remote_code=True)


def embed(text) -> List[float]:
    return list(model.encode(text))


def embed_entity(entity) -> List[float]:
    text = entity.title

    if entity.title != entity.description:
        text += "\n" + entity.description

    return embed(text)


if __name__ == '__main__':
    print(len(embed('hello world')))  # 768
