import uuid

class User:

    def __init__(self, id: uuid.UUID, name: str, password: str):
        if not isinstance(id, uuid.UUID):
            id = uuid.UUID(id)
        
        self.id = id
        self.name = name
        self.password = password
