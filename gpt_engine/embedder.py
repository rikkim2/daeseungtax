#(문서 → 벡터 DB)

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.embeddings.openai import OpenAIEmbedding
from django.conf import settings
import os


def build_index(doc_path="gpt_engine/docs", persist_path="gpt_engine/vector_db"):
    # 1. 문서 불러오기
    documents = SimpleDirectoryReader(doc_path).load_data()

    # 2. OpenAI 임베딩 모델
    embed_model = OpenAIEmbedding(api_key=settings.OPENAI_API_KEY)

    # 3. StorageContext 기본 사용 (SimpleVectorStore 내장)
    storage_context = StorageContext.from_defaults()

    # 4. 인덱스 생성
    index = VectorStoreIndex.from_documents(
        documents,
        embed_model=embed_model,
        storage_context=storage_context
    )

    # 5. 인덱스 저장
    os.makedirs(persist_path, exist_ok=True)
    index.storage_context.persist(persist_path)
    print("✅ 벡터 인덱스 저장 완료")