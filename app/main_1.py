from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

DATABASE_URL = "postgresql://postgres:1234@localhost/restaurant_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

MENU = {
    "1": {"name": "Burger", "price": 599, "image":""},
    "2": {"name": "Pizza", "price": 899, "image":""},
    "3": {"name": "Salad", "price": 499, "image": ""},
}

app = FastAPI()

class MenuItemCreate(BaseModel):
    name: str
    price: float
    image: str

class MenuItemUpdate(BaseModel):
    name: str
    price: float
    image: str


# ----------------------------



class MenuItem(Base):
    __tablename__ = "menu_items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    price = Column(Float)
    image = Column(String)


class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    item_id = Column(Integer, ForeignKey('menu_items.id'))
    quantity = Column(Integer)
    price = Column(Float)
    menu_item = relationship("MenuItem")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    table_no = Column(Integer, index=True)
    status = Column(String, default="ongoing")
    served = Column(Boolean, default=False)
    order_items = relationship("OrderItem", back_populates="order")

OrderItem.order = relationship("Order", back_populates="order_items")

Base.metadata.create_all(bind=engine)

class OrderItemCreate(BaseModel):
    item_id: int
    quantity: int

class OrderCreate(BaseModel):
    table_no: int
    items: List[OrderItemCreate]

class OrderUpdate(BaseModel):
    status: str
    served: bool


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def homepage():
    return {"message":"Welcome to the demo version of this app"}

@app.get("/menu", response_model=Dict[int, Dict[str, float]])
async def get_menu(db: Session = Depends(get_db)):
    menu_items = db.query(MenuItem).all()
    return {item.id: {"name": item.name, "price": item.price} for item in menu_items}

@app.post("/order", response_model=Dict)
async def place_order(order: OrderCreate, db: Session = Depends(get_db)):
    db_order = db.query(Order).filter(Order.table_no == order.table_no, Order.status == "ongoing").first()
    if not db_order:
        db_order = Order(table_no=order.table_no)
        db.add(db_order)
        db.commit()
        db.refresh(db_order)

    order_total = 0
    for item in order.items:
        menu_item = db.query(MenuItem).filter(MenuItem.id == item.item_id).first()
        if not menu_item:
            raise HTTPException(status_code=404, detail=f"Item {item.item_id} not found in the menu.")
        order_item = OrderItem(order_id=db_order.id, item_id=item.item_id, quantity=item.quantity, price=menu_item.price)
        db.add(order_item)
        order_total += menu_item.price * item.quantity

    db.commit()
    db.refresh(db_order)
    order_details = db.query(OrderItem).filter(OrderItem.order_id == db_order.id).all()
    return {
        "table_no": db_order.table_no,
        "total": order_total,
        "details": [{"item_id": item.item_id, "quantity": item.quantity, "price": item.price} for item in order_details]
    }

@app.get("/order/{table_no}", response_model=Dict)
async def get_order(table_no: int, db: Session = Depends(get_db)):
    db_order = db.query(Order).filter(Order.table_no == table_no, Order.status == "ongoing").first()
    if not db_order:
        raise HTTPException(status_code=404, detail=f"No ongoing orders found for table {table_no}.")
    order_details = db.query(OrderItem).filter(OrderItem.order_id == db_order.id).all()
    return {
        "table_no": db_order.table_no,
        "status": db_order.status,
        "served": db_order.served,
        "orders": [{"item_id": item.item_id, "quantity": item.quantity, "price": item.price} for item in order_details]
    }

@app.patch("/order/{table_no}", response_model=Dict)
async def update_order_status(table_no: int, order_update: OrderUpdate, db: Session = Depends(get_db)):
    db_order = db.query(Order).filter(Order.table_no == table_no, Order.status == "ongoing").first()
    if not db_order:
        raise HTTPException(status_code=404, detail=f"No ongoing orders found for table {table_no}.")
    db_order.status = order_update.status
    db_order.served = order_update.served
    db.commit()
    db.refresh(db_order)
    return {
        "table_no": db_order.table_no,
        "status": db_order.status,
        "served": db_order.served
    }
