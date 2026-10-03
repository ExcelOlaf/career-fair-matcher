from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Holding(BaseModel):
    symbol: str
    quantity: int
    price: float

holdings = {}

@app.get("/holdings")
def list_holdings():
    return holdings

@app.post("/holdings", status_code=201)
def add_holding(h: Holding):
    holdings[h.symbol] = h
    return h

@app.get("/holdings/{symbol}")
def get_holding(symbol: str):
    if symbol not in holdings:
        raise HTTPException(status_code=404, detail="Not found")
    return holdings[symbol]