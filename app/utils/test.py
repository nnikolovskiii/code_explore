from pydantic import BaseModel


class Counter(BaseModel):
    lol1: str


dict = {"lol1": "lol", "lol2": "lol"}
print(Counter(**dict))