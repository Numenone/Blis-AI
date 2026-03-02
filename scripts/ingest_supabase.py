import os
import argparse
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import SupabaseVectorStore
from supabase.client import Client, create_client
from dotenv import load_dotenv

load_dotenv()

def ingest_pdf_supabase(pdf_path: str):
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
        exit(1)
        
    print(f"Loading {pdf_path}...")
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    
    print(f"Loaded {len(documents)} pages. Splitting text...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""]
    )
    docs = text_splitter.split_documents(documents)
    print(f"Split into {len(docs)} chunks.")

    print(f"Initializing OpenAI Embeddings...")
    embeddings = OpenAIEmbeddings()
    
    print("Connecting to Supabase...")
    supabase: Client = create_client(supabase_url, supabase_key)

    print("Saving to Supabase Vector Store...")
    vectorstore = SupabaseVectorStore.from_documents(
        docs,
        embeddings,
        client=supabase,
        table_name="documents",
        query_name="match_documents"
    )
    print("Ingestion complete! Data resides in Supabase Postgres.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest PDF into Supabase Vector DB")
    parser.add_argument("--pdf", type=str, default="data/manual-politicas-viagem-blis.pdf", help="Path to PDF file")
    args = parser.parse_args()
    
    if not os.path.exists(args.pdf):
        print(f"Error: File {args.pdf} not found.")
        exit(1)
        
    ingest_pdf_supabase(args.pdf)
