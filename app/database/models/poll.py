import uuid
from .option import Option


class Poll:


    def __init__(self, id: uuid.UUID, title: str, description: str, author: uuid.UUID, options: [Option]):
        if not isinstance(id, uuid.UUID):
            id = uuid.UUID(id)

        if not isinstance(author, uuid.UUID):
            author = uuid.UUID(author)
    
        self.id = id
        self.title = title
        self.description = description
        self.author = author
        self.options = options
