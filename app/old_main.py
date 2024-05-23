from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict
from fastapi.responses import JSONResponse

app = FastAPI()

# Dummy data to simulate menu and orders
MENU = {
    "1": {"name": "Burger", "price": 599, "image":""},
    "2": {"name": "Pizza", "price": 899, "image":""},
    "3": {"name": "Salad", "price": 499, "image": ""},
}

# In-memory storage for orders
orders: Dict[int, List[Dict]] = {}


class OrderItem(BaseModel):
    item_id: str
    quantity: int


class Order(BaseModel):
    table_no: int
    items: List[OrderItem]

@app.get("/")
async def homepage():
    return {"message":"Welcome to the demo version of this app"}

@app.get("/menu")
async def get_menu():
    return MENU


@app.post("/order", response_model=Dict)
async def place_order(order: Order):
    if order.table_no not in orders:
        orders[order.table_no] = []

    order_total = 0
    for item in order.items:
        if item.item_id not in MENU:
            raise HTTPException(status_code=404, detail=f"Item {item.item_id} not found in the menu.")
        menu_item = MENU[item.item_id]
        order_total += menu_item["price"] * item.quantity
        orders[order.table_no].append({"item_id": item.item_id, "quantity": item.quantity, "price": menu_item["price"]})

    return {"table_no": order.table_no, "total": order_total, "details": orders[order.table_no]}


@app.get("/order/{table_no}", response_model=Dict)
async def get_order(table_no: int):
    if table_no not in orders:
        raise HTTPException(status_code=404, detail=f"No orders found for table {table_no}.")
    return {"table_no": table_no, "orders": orders[table_no]}
