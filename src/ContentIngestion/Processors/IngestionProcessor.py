import base64
import logging
import json
from Models.Document import Document
from Utility import functions
from azure.search.documents import SearchClient
from Configuration.Settings import Settings
from Processors.IndexProcessor import IndexProcessor
from common.cache_utils import CacheFactory, CacheType
from Utilities.Helper import log_execution_time
from Utilities.Exceptions import *
from Models.RequestModel import RequestModel
from content_parser import ParserFactory
from common.openai_utils import OpenAIUtility as OpenAIUtilityCore
from common.azure_blob_storage_manager import AzureBlobStorageManager
from azure.identity import DefaultAzureCredential
from pydantic import BaseModel
from azure.core.credentials import AzureKeyCredential


class IngestionProcessor:
    
    def __init__(self, settings, fieldsPath):
        self.settings: Settings=settings
        self.cache = CacheFactory.get_cache(CacheType.REDIS,self.settings.redis_host,None)  
        with open(fieldsPath) as f:
            self.config = json.load(f)

    @log_execution_time
    def process(self, req_body: RequestModel):
        """
        Process the content by parsing the request body, chunking the content into smaller pieces,
        generating embeddings for the content chunks, and indexing the content in Azure Cognitive Search.

        Args:
            req_body (dict): The request body containing the content attributes.

        Returns:
            dict: The result of indexing the content in Azure Cognitive Search.

        {
            "Fields": 
            {
                "ChunkSize": 1024,
                "Data": ""
                "FileName": 
                "Identifier": 
                "Keywords": "",
                "LastModified": 
                "OriginalContentType":
                "Path": 
            }
            "DataSource": 
            "DocumentId": 
            "DocumentType":
            "Metadata": 
            "Operation": 
            "Properties":
        }
        """
        document_fields = self.config['document_types'].get('techconnect')
        if document_fields:
            model_class = self.create_model_class(document_fields['fields'])
            final_model = self.map_values(req_body, model_class)

        else:
            raise Exception(f"No model found for techconnect")

        response = 'Invalid Details. Please check the request'
        dataSource = str.lower(req_body.get('DataSource'))
        documentIdentifier = req_body.get('DocumentId')
        content = req_body.get('Fields')
        documentType = content.get('DocumentType')
        metadata = req_body.get('Properties')
        properties = req_body.get('Properties')
        fileURL = content.get('FileUrl')

        if(documentIdentifier is None or dataSource is None or documentType is None or content is None):
            raise QueryTypeInvalidOrNotSupported(response)
        
        index_name = self.settings.get_searchindexname('techconnect')

        self.search_client = self.get_searchClient(index_name)
        self.openaiutility = OpenAIUtilityCore(self.settings.openai_api_base, None, self.settings.openai_api_version)

        content_chunks, document_title = self.parse_document(documentType, content, documentIdentifier, metadata, properties, dataSource)

        if(content_chunks is None or len(content_chunks) == 0):
            raise QueryTypeInvalidOrNotSupported("Blank Page")
        
        else:
            titleVector = self.openaiutility.generate_embeddings(text=documentIdentifier)
            indexProcessor = IndexProcessor(self.settings)
            fileURL = fileURL
            response = indexProcessor.index_content(fileURL,content_chunks, documentIdentifier, document_title, titleVector, final_model, self.openaiutility, self.search_client)
            return response

    def create_model_class(self, fields):
        class DynamicModel(BaseModel):
            pass
        
        DynamicModel.field_names = set(fields.keys())

        for field, type_ in fields.items():
            print (field)
            setattr(DynamicModel, field, type_)
       
        return DynamicModel
    
    def map_values(self, source_instance: RequestModel, target_model: BaseModel) -> BaseModel:
        target_data = {}
        source_fields = source_instance["Fields"]
        for field in target_model.field_names:
            if field in source_instance:
                target_data[field] = source_instance[field]
            elif field in source_fields:
                target_data[field] = source_fields[field]
            elif "Vector" in str(field):
                target_data[field] = []
            else:
                target_data[field] = ""
        
        for key, value in target_data.items():
            setattr(target_model, key, value)

        return target_model
    
    def get_searchClient(self, indexName):
        if(indexName is None or len(indexName)==0):
            raise QueryTypeInvalidOrNotSupported("Search Index Name is not valid")
        
        search_client = SearchClient(
            endpoint=self.settings.azure_cognitive_search_service_url,
            index_name=indexName,
            credential=AzureKeyCredential(self.settings.azure_cognitive_admin_key))
        
        return search_client

    def parse_document(self, documentType, content, documentIdentifier, metadata, properties, dataSource):
        try:
            # Chunk the content into smaller pieces
            logging.info(f"Parsing Document: {documentIdentifier}")
            document = content.get('Data')
            content_bytes: bytes = base64.b64decode(document)
            contentType = content.get('ContentType')
            if(contentType is None):
                contentType = "application/pdf"
            
            document_content = []
            document_title = ''
            sequenceId = 0
            parserType = ''
            cache_key_content = None

            if(contentType == "application/text"):
                document_title=content.get('FileName')
                document_content, document_title = self.generate_index_document(pageContent, document_title, document_content, sequenceId, dataSource, documentType)
                return document_content, document_title
            
            match(contentType):
                case 'application/pdf':
                    parserType = "pdf"
                case "application/vnd.openxmlformats-officedocument.presentationml.presentation":
                    parserType = "pptx"
                case "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    parserType = "docx"

            openai_utility = OpenAIUtilityCore(self.settings.openai_api_base, None, self.settings.openai_api_version)
            # azure_blob_storage_manager =  AzureBlobStorageManager(self.settings.blob_storage_account_name,account_key= None,container_name= self.settings.blob_container_name_images, sas_url_expiry_window=self.settings.blob_sas_url_expiry_window)
            parser = ParserFactory.create_parser(content_bytes,parserType, azure_form_recognizer_endpoint=None, azure_form_recognizer_key=None, openai_utility=openai_utility, azure_blob_storage_manager=None)

            if parser:
                for page_number, page_content, is_image_present in parser.extract_text():
                    if len(page_content)>0 and page_content is not None:
                        logging.info(f"Parsing page - {page_number} for document {documentIdentifier}")
                        logging.info(f"page_content in content ingestion - {page_content} ")
                        
                        if(page_content is None or len(page_content) == 0):
                            raise PDFParsingException("Unable to parse the document")
                        else:
                            document_content, document_title = self.generate_index_document(
                                content=page_content,
                                            documentIdentifier=documentIdentifier,
                                            documentType= documentType,
                                            contentMetadata=metadata, 
                                            properties= properties,  
                                            pageNumber=page_number,
                                            document_content=document_content, 
                                            sequenceId=sequenceId, 
                                            dataSource=dataSource,
                                            is_image_present=is_image_present,
                                            chunk_size=1024)
                            sequenceId += 1
                            if(len(document_content) > 0):
                                cache_key_content = f"{documentType}_CONTENT_{documentIdentifier}"
                    else:
                        continue
        
                # Write the content to the cache so that it can be used later by other services
                if cache_key_content: 
                    self.cache.write_object_to_cache(cache_key_content, document_content)
                
                return document_content, document_title
            else:
                raise Exception(f"No content found for the given document number- {documentIdentifier}")
        
        except PDFParsingException as e:
            raise e
        except Exception as e:
            logging.error(f"Error while extracting content of document: {str(e)}")
            raise e

    @log_execution_time
    def generate_index_document(self, content, documentIdentifier, documentType, contentMetadata, properties, chunk_size, pageNumber, document_content : list, sequenceId, dataSource, is_image_present: bool):
        try:
            content_chunk = functions.split_text_by_token(content, chunk_size, chunk_overlap=80)

            for index, chunk in enumerate(content_chunk):
                if(len(chunk) > 0):
                    doccontent = ''
                    metadata = ''
                    indexProcessor = IndexProcessor(self.settings)
                    metadata, documentTitle = indexProcessor.get_content_metadata(documentIdentifier, contentMetadata, properties, documentType)
                    
                    if(len(metadata) > 0 and metadata is not None):
                        doccontent=f"----- Content block Start---- \n--continued text from Page {pageNumber} of DocumentType - '{documentType} - {documentIdentifier}'---- {chunk}   ----Page {pageNumber} of Document - '{documentIdentifier} \n ----{metadata}---\n '\n----Content block end \n---- "
                    else: 
                        doccontent=f"----- Content block Start---- \n--continued text from Page {pageNumber} of DocumentType - '{documentType} - {documentIdentifier}'---- {chunk}   ----Page {pageNumber} of Document - '{documentIdentifier} '\n----Content block end \n---- "
                        
                    doc = Document(page_content = doccontent, metadata={"source": f"Page {pageNumber} of {documentType} - {documentIdentifier}","pageNumber":pageNumber, "sequenceId": sequenceId, "isImagePresent": is_image_present})

                    document_content.append(doc)            
        except Exception as e:
            logging.error(f"Error while extracting content from page {pageNumber} of document: {str(e)}")
            raise e   
        return document_content, documentTitle
    
    @log_execution_time
    def generate_index_for_text_data(self, content, documentTitle,document_content : list, sequenceId, dataSource, documentType):
        content_chunk = functions.split_text_by_token(content, self.settings.chunk_size, chunk_overlap=80)

        try:
            for index, chunk in enumerate(content_chunk):
                if(len(chunk) > 0):
                    doccontent=f"----- Content block Start---- \n--continued text from  Document - '{documentTitle}'- {documentType} - {dataSource} ---- {chunk}   ---- of Document - '{documentTitle} '\n----Content block end \n---- "

                    doc = Document(page_content = doccontent, metadata={"source": f"{documentTitle} - {dataSource}", "sequenceId": sequenceId})
                    document_content.append(doc)
        except Exception as e:
            logging.error(f"Error while extracting content from document: {str(e)}")
            raise e   
        return document_content, documentTitle