import os
import argparse
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv

load_dotenv()

def ingest_pdf(pdf_path: str, persist_directory: str = "data/chroma"):
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

    print(f"Saving to Chroma DB at {persist_directory}...")
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    print("Ingestion complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest PDF into Chroma DB")
    parser.add_argument("--pdf", type=str, default="data/manual-politicas-viagem-blis.pdf", help="Path to PDF file")
    args = parser.parse_args()
    
    if not os.path.exists(args.pdf):
        print(f"Error: File {args.pdf} not found.")
        exit(1)
        
    ingest_pdf(args.pdf)
