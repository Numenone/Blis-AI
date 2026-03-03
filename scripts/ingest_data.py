import os
import argparse
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

load_dotenv()

def ingest_file(file_path: str, persist_directory: str = "data/chroma"):
    print(f"Loading {file_path}...")
    if file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    else:
        loader = TextLoader(file_path, encoding="utf-8")
        
    documents = loader.load()
    
    print(f"Loaded {len(documents)} docs. Splitting text...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n### ", "\n## ", "\n# ", "\n\n", "\n", " ", ""]
    )
    docs = text_splitter.split_documents(documents)
    print(f"Split into {len(docs)} chunks.")

    print(f"Initializing OpenAI Embeddings via OpenRouter...")
    embeddings = OpenAIEmbeddings(
        model="openai/text-embedding-3-small",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1"
    )

    print(f"Saving to Chroma DB at {persist_directory}...")
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    print("Ingestion complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest PDF or Markdown into Chroma DB")
    parser.add_argument("--file", type=str, default="data/manual_blis_v2.md", help="Path to file")
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"Error: File {args.file} not found.")
        exit(1)
        
    ingest_file(args.file)
