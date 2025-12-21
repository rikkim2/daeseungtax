# (GPT 응답 생성)

from django.conf import settings
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.core.settings import Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
import openai


def test_api_key():
    """Test if OpenAI API key is valid by making a test request."""
    try:
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            return "❌ API key is empty"
        if not api_key.startswith('sk-'):
            return "❌ API key format is invalid"

        # OpenAI API로 키 검증
        openai.api_key = api_key
        try:
            # 간단한 모델 목록 요청으로 키 검증
            openai.models.list()
            print(f"✅ API key is valid and working:{openai.models.list()}") 
        except openai.RateLimitError:
            print( "❌ Rate limit exceeded")
        except openai.APIConnectionError:
            print( "❌ Connection error")
        except openai.AuthenticationError:
            print( "❌ API key is invalid")
        except openai.APIError as e:
            print( f"❌ API error: {str(e)}")
    except AttributeError:
        print( "❌ OPENAI_API_KEY not found in settings")


def ask_gpt(question: str, persist_path: str = "gpt_engine/vector_db/") -> str:
    """Query GPT with a question and return the response.
    
    Args:
        question (str): The question to ask GPT
        persist_path (str): Path to the vector database
        
    Returns:
        str: GPT's response to the question
    """
    print(question)
    # test_api_key()
    # 1. LLM 설정
    llm = OpenAI(
        model="gpt-3.5-turbo",
        api_key=settings.OPENAI_API_KEY,
        timeout=20,  # Increased timeout to 120 seconds
        default_headers={},
        max_retries=1  # Add retries for reliability
    )

    # 2. Embedding 모델 설정
    embed_model = OpenAIEmbedding(
        api_key=settings.OPENAI_API_KEY,
        model="text-embedding-ada-002"
    )
    embedding = embed_model.get_text_embedding(question)
    print("임베딩 벡터 길이:", len(embedding))
    print(f"✅ 저장된 인덱스를 '{persist_path}'에서 로딩 중...")

    # 3. 서비스 컨텍스트 구성 (embedding 포함)
    Settings.llm = llm
    Settings.embed_model = embed_model
    
    # 4. 인덱스 로딩
    storage_context = StorageContext.from_defaults(persist_dir=persist_path)
    index = load_index_from_storage(storage_context)
    query_engine = index.as_query_engine()
    response = query_engine.query(question)
    print("✅ 인덱스 로드 성공!")
    return str(response)
