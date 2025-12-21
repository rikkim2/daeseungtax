# from django.shortcuts import render 
# from django.http import JsonResponse 

# import os
# import time
# import openai
# from django.db import connection

# from django.conf import settings
# from concurrent.futures import ThreadPoolExecutor
# # from llama_index.readers.database import DatabaseReader

# # from llama_index.core import Document,GPTListIndex,Settings,VectorStoreIndex
# # from llama_index.llms.openai import OpenAI
# # from llama_index.embeddings.openai import OpenAIEmbedding
# # from llama_index.core.node_parser import SentenceSplitter
# from app.models import MemUser

# from django.contrib.auth.decorators import login_required
# # openai.api_key = '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'
# # load_dotenv()
# openai.api_key = settings.OPENAI_API_KEY

# # Settings.llm = OpenAI(model="gpt-3.5-turbo", temperature=0)
# # embed_model = OpenAIEmbedding(model="text-embedding-ada-002")
# # Settings.embed_model = embed_model
# # Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)
# # Settings.num_output = 512
# # Settings.context_window = 3900



# def fetch_data():
#     transactions = MemUser.objects.only("biz_name", "reg_date", "ceo_name")
#     content_count = 0 
#     documents = []

#     def process_transaction(transaction):
#         content = (
#             f"Customer: {transaction.biz_name}\n"
#             f"Date: {transaction.reg_date}\n"
#             f"Ceo: {transaction.ceo_name}"
#         )

#         return Document(text=content)

#     with ThreadPoolExecutor() as executor:
#         for document in executor.map(process_transaction, transactions):
#             documents.append(document)
#             content_count += 1  # content 개수 증가
        
#     print(f"Total Content Count: {content_count}")
#     return documents

# def embed_data(documents):
#     embed_model = OpenAIEmbedding(model="text-embedding-ada-002")

#     # 비동기 병렬 임베딩 처리
#     with ThreadPoolExecutor() as executor:
#         embeddings = list(executor.map(lambda doc: embed_model.get_text_embedding(doc.text), documents))

#     return embeddings

# def embed_data_in_batches(documents, batch_size=10):
#     embed_model = OpenAIEmbedding(model="text-embedding-ada-002")
#     embeddings = []

#     for i in range(0, len(documents), batch_size):
#         batch = documents[i : i + batch_size]
#         batch_texts = [doc.text for doc in batch]
        
#         # 배치 단위로 임베딩 생성
#         batch_embeddings = [embed_model.get_text_embedding(text) for text in batch_texts]
#         embeddings.extend(batch_embeddings)

#     return embeddings

# # @login_required(login_url="/login/")
# def query_view(request):
#     response_text = None
#     if request.method == "POST":
#         query = request.POST.get("query")
#         if query:
#             # 테스트용 문서 생성
#           documents = [
#               Document(text="This is a test document containing financial data.")
#           ]
#           start_time = time.time()
#           documents = fetch_data()
#           embeddings = embed_data(documents)
#           # embeddings = embed_data_in_batches(documents, batch_size=10)  # 배치 크기 설정
#           for document, embedding in zip(documents, embeddings):
#               document.embedding = embedding  # 문서에 임베딩 추가
#           print(f"Data Fetching Time: {time.time() - start_time:.2f} seconds")

#           start_time = time.time()
#           # index = GPTListIndex.from_documents(documents)
#           index = VectorStoreIndex.from_documents(documents)
#           print(f"Index Creation Time: {time.time() - start_time:.2f} seconds")

#           start_time = time.time()
          
#           query_engine = index.as_query_engine(similarity_top_k=10)
#           response = query_engine.query(query)
#           print(f"Query Execution Time: {time.time() - start_time:.2f} seconds")
#           # 쿼리를 실행하여 결과 가져오기
#           # response = index.query(query)
#           response_text = str(response)  # 결과를 문자열로 변환
    
#     return render(request, 'accountGpt/index.html', {"response": response_text})



