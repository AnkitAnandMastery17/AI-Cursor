from dotenv import load_dotenv
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_qdrant import QdrantVectorStore

from langchain_openai import OpenAIEmbeddings
pdf_path = Path(__file__).parent / "nodejs.pdf"
load_dotenv()

loader = PyPDFLoader(file_path=pdf_path)
dosc = loader.load() #Read Pdf file

#Chunking
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 1000,
    chunk_overlap=400
)
split_dosc = text_splitter.split_documents(documents=dosc)

#vector embeddings
embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-large",
)


vector_store = QdrantVectorStore.from_documents(
    documents=split_dosc,
    url="http://localhost:6333",
    collection_name="learning_vectors",
    embedding=embedding_model
)
