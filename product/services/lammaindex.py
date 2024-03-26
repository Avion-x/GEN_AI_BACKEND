from llama_index.core import Document, VectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.core.node_parser import SentenceSplitter, SemanticSplitterNodeParser
from llama_index.vector_stores.pinecone import PineconeVectorStore
from pinecone import Pinecone
from llama_index.embeddings.cohere import CohereEmbedding
from IPython.display import Markdown, display
from dotenv import load_dotenv,find_dotenv
import os

from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.core.ingestion import IngestionPipeline
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding


load_dotenv(find_dotenv())
PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
PINECONE_API_ENV = os.environ.get('PINECONE_API_ENV')
cohere_api_key = os.environ["COHERE_API_KEY"]

class VectorStoreService():

    # Configure OpenAI API

    def __init__(self, *args, **kwargs):
        self.api_type = self.kwargs.get("api_type", "azure")
        self.api_version = self.kwargs.get("api_version", "2023-07-01-preview")
        self.api_base = os.getenv('AZURE_OPENAI_ENDPOINT')
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.pinecone_namespace = self.kwargs.get("pinecone_namespace", "alice_new_3")
        self.chunk_size = self.kwargs.get("chunk_size", 120)
        self.chunk_overlap = self.kwargs.get("chunk_overlap", 0)

        self.embed_model = AzureOpenAIEmbedding(
            model="text-embedding-ada-002",
            deployment_name="OpenAIEmbeddings",
            api_key=self.api_key,
            azure_endpoint=self.api_base,
            api_version=self.api_version,
        )

    def get_data_dir(self,):
        data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data_2')
        print(data_dir)
        return data_dir

    def execute(self, *args):
        data_dir = self.get_data_dir()
        documents = SimpleDirectoryReader(data_dir).load_data()
        parser = SentenceSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap) #(chunk_size=80, chunk_overlap=20, embed_model=embed_model)
        nodes = parser.get_nodes_from_documents(documents, show_progress=True)

        pinecone_vector_store = PineconeVectorStore(api_key=PINECONE_API_KEY, index_name=pinecone_index, environment=PINECONE_API_ENV, namespace=self.pinecone_namespace)

        pipeline = IngestionPipeline(
            transformations=[
                embed_model,
                ],
                vector_store=pinecone_vector_store 
            )


        pipeline.run(nodes=nodes)