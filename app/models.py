from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Table, String, Column, Date, Integer, Float, event
from typing import List

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Association table for service tickets  
service_tickets = Table(
    "service_tickets",
    Base.metadata,
    Column("id", ForeignKey("ticket_information.id"), nullable=False),
    Column("car_vin", ForeignKey("cars.vin")),
    Column("mechanic_id", ForeignKey("mechanics.id")),
)

#Association table for inventory and service tickets
class TicketPart(Base):
    __tablename__ = "ticket_parts"

    ticket_id: Mapped[int] = mapped_column(ForeignKey("ticket_information.id"), primary_key=True)
    inventory_id: Mapped[int] = mapped_column(ForeignKey("inventory.id"), primary_key=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    part_cost: Mapped[float] = mapped_column(Float, nullable=False)

    ticket: Mapped["TicketInformation"] = relationship(back_populates="ticket_parts")
    inventory: Mapped["Inventory"] = relationship(back_populates="ticket_parts")

class Inventory(Base):
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(primary_key=True)
    part_name: Mapped[str] = mapped_column(String(30), nullable=False)
    part_cost: Mapped[float] = mapped_column(Float, nullable = False)
    
    ticket_parts: Mapped[List["TicketPart"]] = relationship(back_populates="inventory")

class TicketInformation(Base):
    __tablename__ = 'ticket_information'

    #one-one relationship to junction table
    id: Mapped[int] = mapped_column(primary_key=True)

    service_date: Mapped[Date] = mapped_column(Date)
    issue: Mapped[str] = mapped_column(String(300))
    result: Mapped[str] = mapped_column(String(300))
    labor_cost: Mapped[float] = mapped_column(Float)
    
    # Many-to-many with Inventory
    ticket_parts: Mapped[List["TicketPart"]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan"
    )

    total_cost: Mapped[float] = mapped_column(Float)
    
    #relationships

    cars: Mapped[List["Car"]] = relationship(
        "Car",
        secondary=service_tickets,
        primaryjoin="TicketInformation.id == service_tickets.c.id",
        secondaryjoin="Car.vin == service_tickets.c.car_vin",
        back_populates="services",
        overlaps="mechanics,tickets")

    mechanics: Mapped[List["Mechanic"]] = relationship(
        "Mechanic",
        secondary=service_tickets,
        primaryjoin="TicketInformation.id == service_tickets.c.id",
        secondaryjoin="Mechanic.id == service_tickets.c.mechanic_id",
        back_populates="tickets",
        overlaps="cars,services")

class Customer(Base):
    __tablename__ = 'customers'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(360), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(40), nullable=False)
    phone: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)

    cars: Mapped[List['Car']] = relationship("Car", back_populates="customer")

class Mechanic(Base):
    __tablename__ = 'mechanics'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(40), nullable=False)
    address: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(360), nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(40), nullable=False)
    salary: Mapped[int] = mapped_column(nullable=False)
    # Many-to-many relationship with cars through service_tickets
    tickets: Mapped[List["TicketInformation"]] = relationship(
        secondary=service_tickets,
        primaryjoin="Mechanic.id == service_tickets.c.mechanic_id",
        secondaryjoin="TicketInformation.id == service_tickets.c.id",
        back_populates="mechanics",  # ✅ must match TicketInformation
        overlaps="cars,services")

class Car(Base):
    __tablename__ = 'cars'

    vin: Mapped[str] = mapped_column(String(17), primary_key=True)
    make: Mapped[str] = mapped_column(String(30), nullable=False)
    model: Mapped[str] = mapped_column(String(30), nullable=False)
    year: Mapped[str] = mapped_column(String(4), nullable=False)
    license_plate: Mapped[str] = mapped_column(String(8), nullable=False, unique=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)

    # Direct relationship to the car's owner
    customer: Mapped["Customer"] = relationship("Customer", back_populates="cars")
    # Many-to-many relationship with mechanics through service_tickets
    services: Mapped[List["TicketInformation"]] = relationship(
        secondary=service_tickets,
        primaryjoin="Car.vin == service_tickets.c.car_vin",
        secondaryjoin="TicketInformation.id == service_tickets.c.id",
        back_populates="cars",
        overlaps="mechanics,tickets")


# # 1. When parts are added/removed via relationship
# @event.listens_for(TicketInformation.ticket_parts, "append")
# @event.listens_for(TicketInformation.ticket_parts, "remove")
# def update_total_on_collection_change(target, value, initiator):
#     db.session.flush()
#     recalc_total_cost(target)

# 2. When TicketPart is inserted or deleted in DB
@event.listens_for(TicketPart, "before_insert")
@event.listens_for(TicketPart, "before_delete")
def update_total_on_part_row(mapper, connection, target):
    ticket = target.ticket
    if ticket:
        recalc_total_cost(ticket)

# # 3. When quantity or part_cost changes
# @event.listens_for(TicketPart.quantity, "set")
# @event.listens_for(TicketPart.part_cost, "set")
# def update_total_on_part_attribute(target, value, oldvalue, initiator):
#     ticket = target.ticket
#     if ticket:
#         db.session.flush()
#         recalc_total_cost(ticket)

# # 4. When ticket itself updates (labor cost changes)
# @event.listens_for(TicketInformation, "before_insert")
# @event.listens_for(TicketInformation, "before_update")
# def update_total_on_ticket(mapper, connection, target):
#     recalc_total_cost(target)

# Helper function
def recalc_total_cost(ticket):
    parts_total = sum(tp.quantity * tp.part_cost for tp in ticket.ticket_parts)
    for tp in ticket.ticket_parts:
        print(tp)
    print(f'parts total cost = {parts_total}')
    ticket.total_cost = (ticket.labor_cost or 0) + parts_total