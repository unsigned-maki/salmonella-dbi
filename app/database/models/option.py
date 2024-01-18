import uuid
from errors import UserError

def valid_votes(votes):
    if votes < 0:
        raise UserError("Votes cannot be less than 0.")


class Option:

    def __init__(self, id: uuid.UUID, text: str, votes: int):
        if not isinstance(id, uuid.UUID):
            id = uuid.UUID(id)
        
        self.id = id
        self.text = text
        self.votes = votes
