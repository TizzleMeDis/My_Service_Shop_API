from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Table, String, Column, Date, Integer
from typing import List

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Association table for service tickets  
service_tickets = Table(
    "service_tickets",
    Base.metadata,
    Column("id", ForeignKey("ticket_information.id")),
    Column("car_vin", ForeignKey("cars.vin")),
    Column("mechanic_id", ForeignKey("mechanics.id")),
)

class TicketInformation(Base):
    __tablename__ = 'ticket_information'

    #one-one relationship to junction table
    id: Mapped[int] = mapped_column(primary_key=True)

    service_date: Mapped[Date] = mapped_column(Date)
    issue: Mapped[str] = mapped_column(String(300))
    result: Mapped[str] = mapped_column(String(300))
    labor_cost: Mapped[int] = mapped_column(Integer)

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
    phone: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)

    cars: Mapped[List['Car']] = relationship("Car", back_populates="customer")

class Mechanic(Base):
    __tablename__ = 'mechanics'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(40), nullable=False)
    address: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(360), nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)
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