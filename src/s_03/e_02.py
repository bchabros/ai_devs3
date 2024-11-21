from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from pinecone import Pinecone
import os
from dotenv import load_dotenv

from src.prompt.s02e03 import QA_PROMPT_TEMPLATE


class DocumentRAG:
    def __init__(self, documents_path, index_name, refresh=False, chunk_size=1000,
                 chunk_overlap=200, model_name="gpt-4o-mini", temperature=0,
                 embedding_model="text-embedding-3-small"):
        """
        Initialize the Document QA System

        Args:
            documents_path (str): Path to documents directory
            index_name (str): Name of the Pinecone index
            refresh (bool): Whether to refresh the vector store
            chunk_size (int): Size of document chunks
            chunk_overlap (int): Overlap between chunks
            model_name (str): Name of the LLM model
            temperature (float): Temperature for LLM responses
            embedding_model (str): Name of the embedding model
        """
        load_dotenv()

        self.documents_path = documents_path
        self.index_name = index_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.model_name = model_name
        self.temperature = temperature
        self.embedding_model = embedding_model

        # Initialize components
        self.embeddings = self._initialize_embeddings()
        self.vector_store = self._get_vector_store(refresh)
        self.qa_chain = self._setup_qa_chain_with_filter()

    def _initialize_embeddings(self):
        """Initialize OpenAI embeddings"""
        return OpenAIEmbeddings(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            model=self.embedding_model
        )

    def _load_documents(self, file_pattern="*.txt"):
        """Load documents from specified directory"""
        loader = DirectoryLoader(self.documents_path, glob=file_pattern)
        return loader.load()

    def _split_documents(self, docs):
        """Split documents into smaller chunks"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        return text_splitter.split_documents(docs)

    def _get_vector_store(self, refresh):
        """Get or create vector store based on refresh parameter"""
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

        try:
            index = pc.Index(self.index_name)

            if refresh:
                try:
                    index.delete(delete_all=True)
                    print(f"All vectors deleted from index '{self.index_name}'")
                except Exception:
                    print(f"No existing vectors to delete in index '{self.index_name}'")

                docs = self._load_documents()
                split_docs = self._split_documents(docs)
                return PineconeVectorStore.from_documents(
                    split_docs,
                    self.embeddings,
                    index_name=self.index_name
                )
            else:
                stats = index.describe_index_stats()
                if stats.total_vector_count == 0:
                    raise ValueError(f"Index '{self.index_name}' is empty. Please use refresh=True to populate it.")

                return PineconeVectorStore(
                    index_name=self.index_name,
                    embedding=self.embeddings
                )

        except Exception as e:
            if "Index not found" in str(e) and refresh:
                docs = self._load_documents()
                split_docs = self._split_documents(docs)
                return PineconeVectorStore.from_documents(
                    split_docs,
                    self.embeddings,
                    index_name=self.index_name
                )
            else:
                raise ValueError(f"Index '{self.index_name}' does not exist. Please use refresh=True to create it.")

    def _setup_qa_chain_with_filter(self):
        """Set up the QA chain with document filtering"""
        llm = ChatOpenAI(
            model_name=self.model_name,
            temperature=self.temperature
        )

        compressor = LLMChainExtractor.from_llm(llm=llm)

        compression_retriever = ContextualCompressionRetriever(
            base_retriever=self.vector_store.as_retriever(search_kwargs={"k": 4}),
            base_compressor=compressor
        )

        qa_prompt_template = QA_PROMPT_TEMPLATE

        qa_prompt = PromptTemplate(
            template=qa_prompt_template,
            input_variables=["context", "question"]
        )

        return RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=compression_retriever,
            return_source_documents=True,
            chain_type_kwargs={
                "prompt": qa_prompt,
            }
        )

    def _setup_qa_chain(self):
        """Set up the QA chain with specified LLM and vector store"""
        llm = ChatOpenAI(
            model_name=self.model_name,
            temperature=self.temperature
        )

        # Create a custom prompt template that includes metadata
        prompt_template = QA_PROMPT_TEMPLATE

        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )

        return RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever(),
            return_source_documents=True,  # This will return source documents along with the answer
            chain_type_kwargs={
                "prompt": prompt,
            }
        )

    def query(self, query_text):
        """Execute a query and return results with source documents"""
        result = self.qa_chain.invoke(query_text)

        answer = result['result']
        source_docs = result['source_documents']

        print("\nAnswer:", answer)

        unique_sources = set()
        print("\nSources used:")
        for doc in source_docs:
            source_file = os.path.basename(doc.metadata['source'])
            if source_file not in unique_sources:
                print(f"- {source_file}")
                unique_sources.add(source_file)

        return result

