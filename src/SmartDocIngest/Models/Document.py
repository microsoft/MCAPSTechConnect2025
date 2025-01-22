class Document:
    # constructor
    def __init__(self, page_content: str, metadata: dict):
        self.page_content = page_content
        self.metadata = metadata
    
    page_content: str
    metadata: dict