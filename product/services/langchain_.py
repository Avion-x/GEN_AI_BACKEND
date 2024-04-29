

import os

from dotenv import load_dotenv, find_dotenv
# from langchain.llms import AzureOpenAI
from langchain_community.llms import AzureOpenAI
from langchain_community.embeddings import BedrockEmbeddings
from langchain_community.llms.bedrock import LLM
from langchain_openai.llms.azure import AzureOpenAI
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.chat_models import ChatCohere
from langchain_core.messages import AIMessage, HumanMessage

from llama_index.core import VectorStoreIndex, Settings
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core.retrievers import VectorIndexRetriever


from product.models import KnowledgeBaseResults



# Load environment variables from a `.env` file (if present)
load_dotenv(find_dotenv())

# Retrieve environment variables
PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
PINECONE_API_ENV = os.environ.get('PINECONE_API_ENV')
pinecone_index = os.environ.get("PINECONE_API_INDEX")
AZURE_OPENAI_ENDPOINT = os.environ.get('AZURE_OPENAI_ENDPOINT')
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


# Create Pinecone vector store
pinecone_vector_store = PineconeVectorStore(
    api_key=PINECONE_API_KEY,
    index_name=pinecone_index,
    environment=PINECONE_API_ENV,
    namespace="alice_new_61"
)

# Create Azure OpenAI embedding model
embed_model = AzureOpenAIEmbeddings(
    model="text-embedding-ada-002",
    deployment="OpenAIEmbeddings",
    api_key=OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_version="2023-07-01-preview"
)

# Create VectorStoreIndex and retriever
vector_index = VectorStoreIndex.from_vector_store(vector_store=pinecone_vector_store, embed_model=embed_model)
# retriever = VectorIndexRetriever(vector_index, similarity_top_k=3)  # Retrieve top 3 results

registry = {
    "GRE Tunnel Connecectivity" : "Tunnel Interface, Tunnel Endpoint, Tunnel Source, Tunnel Destination, Tunnel Mode, Tunneling Protocol, Tunnel Encapsulation, GRE tunnel connectivity: Tunnel Interface, Tunnel Endpoint, Tunnel Source, Tunnel Destination, Tunnel Mode, Tunneling Protocol, Tunnel Encapsulation,",
    "NAT Configuration" : 'Source NAT (SNAT), Destination NAT (DNAT), Static NAT, Dynamic NAT.',
    "ACL Configuration" : "ACL (Access Control List), Permit, Deny, Source Address, Destination Address.",
    "Routing Protocols" : ""
}

# get vector namespace based on the product
# store the query data from knowledge base in db



class Langchain_():
    def __init__(self, prompt_data, request, *args, **kwargs):
        try:
            self.request = request
            self.top_k=kwargs.get('top_k', 3)
            self.vector_index = kwargs.get('vector_namespace',None)
            # self.kb_query = kwargs.get("kb_query", None)
            # self.prompt = kwargs.get("query", None)
            self.retriever = VectorIndexRetriever(vector_index, similarity_top_k=self.top_k)
            self.prompt_data = prompt_data
            self.cohere_chat_model = ChatCohere(cohere_api_key=os.environ["COHERE_API_KEY"], temaperature=kwargs.get('embedding_temaperature', 0.1))
            if not self.vector_index:
                raise Exception("No Pinecone namespace is sent to check in knowledge base")
        except Exception as e:
            raise e

    # def execute(self):
    #     response = {}
    #     for test_type, test_categories in self.prompt_data.items():
    #         response[test_type] = {}
    #         for test_category_name, details in test_categories.items():
    #             test_category_id = details.get('test_category_id')
    #             for test in details.get('Tests', []):
    #                 kb_data = self.execute_kb_queries(test.get('kb_query',[]))
    #                 print(kb_data)

                    
                    
    def execute_kb_queries(self, kb_details):
        overall_summary = ""
        for query in kb_details:
            overall_summary += ". " +self.get_data_from_knowledge_base(query)
            self.store_knowledge_base_data(query)
        return overall_summary

    def get_data_from_knowledge_base(self, query_details, *args, **kwargs):
        retriever = None
        if self.top_k != query_details.get('top_k',""):
            retriever = VectorIndexRetriever(vector_index, similarity_top_k=query_details.get('top_k',self.top_k))
        
        retriever = retriever or self.retriever
        answer = retriever.retrieve(query_details.get('query')) or []
        
        self.docs = []
        for retrieved_doc in answer:
            res = retrieved_doc.get_content() + "\n" 
            self.docs.append(res)
        self.summary = self.get_knowledge_base_summary(query_details, self.docs)
        return self.summary

    def get_knowledge_base_summary(self, query_details, docs):
        query = query_details.get('query')
        current_message_with_prompt = [
            HumanMessage(content=f"you are only allowed to search answer to my question within following tripple backticks, find {query} : ```{docs}```. result should as short as possible without information loss, If you don't find answer of my question in the given text simply say 'NOT FOUND' also when the given text is null or empty list say 'Not Found'")
        ]
        a = self.cohere_chat_model.invoke(current_message_with_prompt)
        knowledge_base_summary = f"{query_details.get('default_query_data', '')}" if ('Not Found'.lower() in a.content.lower()) else a.content
        return knowledge_base_summary

    def store_knowledge_base_data(self, query_details):
        kb_result = KnowledgeBaseResults.objects.create(
            customer = self.request.user.customer,
            kb_prompt_id = query_details.get('kb_prompt_id'),
            created_by = self.request.user,
            request_id = self.request.request_id,
            query = query_details.get('query'),
            top_k_docs = self.docs,
            summary_of_docs = self.summary
        )
        return kb_result

        


