from pydantic import BaseModel


class Counter(BaseModel):
    counter: int = 0

counter = Counter()