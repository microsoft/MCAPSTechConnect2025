import logging
from time import sleep
import json
from Configuration.Settings import Settings
from Models.DataSources import DataSources
from common.cache_utils import CacheFactory, CacheType
from Utilities.Exceptions import *
from Utilities.Helper import log_execution_time
from azure.search.documents import SearchClient
from common.openai_utils import OpenAIUtility 

class IndexProcessor:
    def __init__(self, settings: Settings):  
        self.settings = settings
        self.clm_access_token=None
        
    @log_execution_time
    def index_content(self,fileURL, content, documentIdentifier, document_title, titleVector, index_model, openaiutility: OpenAIUtility, search_client: SearchClient):
        """
        Uploads the document content to the search index.

        Args:
        sources (list): A list of the document contents.
        document_number (str): The document number.

        Returns:
        bool: True if the upload is successful, otherwise False.
        """
        # Remove leading slash and split the path into parts
        parts = fileURL.lstrip('/').split('/')
    
        # The folder name is usually the first part of the path
        folder_name = parts[4] if parts else ''
        model_name = folder_name
        counter = 1
        contents=[]
        for document in content:
            document_ChunkID=f'{documentIdentifier}_{counter}'
            counter+=1
            pageNumber = str(document.metadata["pageNumber"])
            sequenceId: int = document.metadata["sequenceId"]
            isImagePresent: int = document.metadata["isImagePresent"]
            
            contentVector = openaiutility.generate_embeddings(document.page_content)
            
            if (counter%10==0):
                sleep(5)

            setattr(index_model, "DocumentChunkId", document_ChunkID)
            setattr(index_model, "PageNumber", pageNumber)
            setattr(index_model, "SequenceId", sequenceId)
            setattr(index_model, "Content", document.page_content)
            setattr(index_model, "ContentVector", contentVector)
            setattr(index_model, "IsImagePresent", isImagePresent)
            setattr(index_model, "FileUrl", fileURL)
            setattr(index_model, "ModelName", model_name)
            
            if document_title is not None and len(titleVector)>0:
                setattr(index_model, "Title", document_title)
                setattr(index_model, "TitleVector", titleVector)

            contentItem =  {attr: getattr(index_model, attr) for attr in index_model.field_names}
            
            logging.info(f"Indexing page - {pageNumber} for document {documentIdentifier}")
            contents.append(contentItem)
        
        filter_query = f"FileUrl eq '{fileURL}'"
        results = search_client.search(
            search_text="*",  # or use a more specific search term if needed
            filter=filter_query,
            top=1000  # adjust as needed to handle pagination
        )
        deleteBatchSize = 10
        results_list = list(results)

        if len(results_list) > 0: 
            for index in range(0, len(results_list), deleteBatchSize):
                currentBatchToDelete = results_list[index : index + deleteBatchSize]
                search_client.delete_documents(documents = currentBatchToDelete)
            
        batchSize = 10
        for index in range(0, len(contents), batchSize):
            currentBatch = contents[index : index + batchSize]
            search_client.upload_documents(documents = currentBatch)

        return 'Succeeded'
    
    def get_content_metadata(self, documentId, metadata, properties, documentType):
        """
        Retrieves metadata information using an API call.

        Args:
            documentId (str): The document Id for which the metadata is to be retrieved.

        Returns:
            document_metadata (str): A string containing the metadata information about the document.
                                    Returns None if the API call fails.

        Raises:
            None.
        """
        try:
            self.cache = CacheFactory.get_cache(CacheType.REDIS,self.settings.redis_host,None)  
            cache_key_metadata=f'{documentType}_METADATA_{documentId}'
            cache_key_title=f'{documentType}_TITLE_{documentId}'
            cache_response_metadata = self.cache.readstr_from_cache(cache_key_metadata)
            cache_response_title = self.cache.readstr_from_cache(cache_key_title)
            
            if cache_response_metadata is not None and cache_response_title is not None:
                return cache_response_metadata,cache_response_title
            
            if len(metadata)>0 and metadata is not None:
                document_metadata = metadata

            if len(properties)>0 and properties is not None:
                if "Title" in properties:
                    title = properties["Title"]
                else:
                    title = properties["{Name}"]
                document_metadata=f'---Title - "{title}", documentId -"{documentId}", created - "{properties["Created"]}", modified - "{properties["Modified"]}", fullPath - "{properties["FullPath"]}" ---'
            else:
                title = documentId

            
            self.cache.write_to_cache(cache_key_metadata, document_metadata)
            self.cache.write_to_cache(cache_key_title, title)
                
            return document_metadata, title
            
        except Exception as e:
            raise DocumentNotFoundException(f"Error while retrieving  metadata: {str(e)}")