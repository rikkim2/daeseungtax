from llama_index.llms.openai import OpenAI

# OpenAI 설정
llm = OpenAI(model="gpt-3.5-turbo")

# 벡터 DB 저장 위치
VECTOR_DB_PATH = "gpt_engine/vector_db/"
DOCS_PATH = "docs/"