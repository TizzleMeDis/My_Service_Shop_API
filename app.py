from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import ValidationError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Table, String, Column, select, Date, Integer
from typing import List

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:****@localhost/library_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(app, model_class=Base)
ma = Marshmallow(app)


# Association table for service tickets  
class ServiceTickets(Base):
    __tablename__ = 'service_tickets'

    car_vin: Mapped[str] = mapped_column(ForeignKey("cars.vin"), primary_key=True)
    mechanic_id: Mapped[int] = mapped_column(ForeignKey("mechanics.id"), primary_key=True)

    service_date: Mapped[Date] = mapped_column(Date)
    issue: Mapped[str] = mapped_column(String(300))
    result: Mapped[str] = mapped_column(String(300))
    labor_cost: Mapped[int] = mapped_column(Integer)

    # Optional reverse relationships if needed
    car: Mapped["Car"] = relationship("Car", back_populates="service_tickets")
    mechanic: Mapped["Mechanic"] = relationship("Mechanic", back_populates="service_tickets")

# service_tickets = Table(
#     "service_tickets",
#     Base.metadata,
#     Column("car_vin", ForeignKey("cars.vin")),
#     Column("mechanic_id", ForeignKey("mechanics.id")),
#     Column("date", Date),
#     Column("issue", String(300)),
#     Column("result", String(300)),
#     Column("labor_cost", Integer),
# )

class Customer(Base):
    __tablename__ = 'customers'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(360), nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)

    cars: Mapped[List['Car']] = relationship("Car", back_populates="owner")

class Mechanic(Base):
    __tablename__ = 'mechanics'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(40), nullable=False)
    address: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(360), nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)
    salary: Mapped[int] = mapped_column(nullable=False)
    # Many-to-many relationship with cars through service_tickets
    service_tickets: Mapped[List["ServiceTickets"]] = relationship("ServiceTickets", back_populates="mechanic")

class Car(Base):
    __tablename__ = 'cars'

    vin: Mapped[str] = mapped_column(String(17), primary_key=True)
    make: Mapped[str] = mapped_column(String(30), nullable=False)
    model: Mapped[str] = mapped_column(String(30), nullable=False)
    year: Mapped[str] = mapped_column(String(4), nullable=False)
    license_plate: Mapped[str] = mapped_column(String(8), nullable=False, unique=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)

    # Direct relationship to the car's owner
    owner: Mapped["Customer"] = relationship("Customer", back_populates="cars")
    # Many-to-many relationship with mechanics through service_tickets
    service_tickets: Mapped[List["ServiceTickets"]] = relationship("ServiceTickets", back_populates="car")


# Marshmallow Schemas
class CustomerSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Customer
        include_relationships = True
    
class MechanicSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Mechanic
        include_relationships = True
    
class CarSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Car
        include_relationships = True

class ServiceTicketSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model: ServiceTickets
        include_relationships = True

customer_schema =CustomerSchema()
customers_schema = CustomerSchema(many=True) #variant that allows for the serialization of many Users,

mechanic_schema =MechanicSchema()
mechanics_schema = MechanicSchema(many=True)

car_schema =CarSchema()
cars_schema = CarSchema(many=True)

service_ticket_schema = ServiceTicketSchema()
service_tickets_schema = ServiceTicketSchema(many=True)

#================== Routes ======================
# ===========================================================================
#                               Customer Routes
# ===========================================================================
#Create customer
@app.route("/customer", methods=['POST'])
def create_customer():
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    query = select(Customer).where(Customer.email == customer_data['email'])
    existing_member = db.session.execute(query).scalars().all()

    if existing_member:
        return jsonify({"error": "Email already in use."}), 400
    
    new_customer = Customer(**customer_data)
    db.session.add(new_customer)
    db.session.commit()

    return customer_schema.jsonify(new_customer), 201

#Get all customers
@app.route("/customer", methods=['GET'])
def get_customers():
    query = select(Customer)
    customers = db.session.execute(query).scalars().all()

    return customers_schema.jsonify(customers), 200

#Get specific customer
@app.route("/customer/<int:customer_id>", methods=['GET'])
def get_customer(customer_id):
    customer = db.session.get(Customer, customer_id)

    if customer:
        return customer_schema.jsonify(customer), 200
    else:
        return jsonify({"error": "Customer not found"}), 404
    
#Update customer
@app.route("/customer/<int:customer_id>", methods=['PUT'])
def update_customer(customer_id):
    customer = db.session.get(Customer, customer_id)

    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    
    try:
        update_customer_data = customer_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    for key, value in update_customer_data.items():
        setattr(customer, key, value)
    print(customer)
    db.session.commit()
    return customer_schema.jsonify(customer), 200

#Delete Customer
@app.route("/customer/<int:customer_id>", methods=['DELETE'])
def delete_customer(customer_id):
    customer = db.session.get(Customer, customer_id)

    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": f"Customer id: {customer_id}, successfully deleted."}), 200
# ===========================================================================
#                               Car Routes
# ===========================================================================
#Create car
@app.route("/car", methods=['POST'])
def create_car():
    try:
        car_data = car_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages)
    
    customer = db.session.get(Customer, car_data['owner'])
    if not customer:
        return jsonify({"error": "Customer not found"}), 400
    
    query = select(Car).where(Car.license_plate == car_data['license_plate'])
    existing_car = db.session.execute(query).scalars().all()

    if existing_car:
        return jsonify({"error": "Car with same plate numbers"}), 400
    
    new_car = Car(**car_data)
    db.session.add(new_car)
    db.session.commit()

    return car_schema.jsonify(new_car), 201

#Get all cars
@app.route("/car", methods=['GET'])
def get_cars():
    query = select(Car)
    cars = db.session.execute(query).scalars().all()

    return cars_schema.jsonify(cars), 200

#Get specific car
@app.route("/car/plate/<string:license_plate>", methods=['GET'])
def get_car_plate(license_plate):
    query = select(Car).where(Car.license_plate == license_plate)
    car = db.session.scalar(query)

    if car:
        return car_schema.jsonify(car), 200
    else:
        return jsonify({"error": "Car not found"}), 404
    
#Get specific car
@app.route("/car/vin/<string:vin>", methods=['GET'])
def get_car_id(vin):
    car = db.session.get(Car, vin)

    if car:
        return car_schema.jsonify(car), 200
    else:
        return jsonify({"error": "Car not found"}), 404

#Update specific car
@app.route("/car/plate/<string:license_plate>", methods=['PUT'])
def Update_car_plate(license_plate):
    query = select(Car).where(Car.license_plate == license_plate)
    car = db.session.scalar(query)
    if not car:
        return jsonify({"error": "Car not found"}), 404
    
    try:
        update_car_data = car_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    for key, value in update_car_data.items():
        setattr(car, key, value)
    
    print(car)
    db.session.commit()
    return car_schema.jsonify(car), 200

#Update specific car
@app.route("/car/vin/<string:vin>", methods=['PUT'])
def Update_car_id(vin):
    car = db.session.get(Car, vin)
    if not car:
        return jsonify({"error": "Car not found"}), 404
    
    try:
        update_car_data = car_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    for key, value in update_car_data.items():
        setattr(car, key, value)
    
    print(car)
    db.session.commit()
    return car_schema.jsonify(car), 200

#Delete Car by vin
@app.route("/car/vin/<string:vin>", methods=['DELETE'])
def delete_car_vin(vin):
    car = db.session.get(Car, vin)

    if not car:
        return jsonify({"error": "Car not found"}), 404
    
    db.session.delete(car)
    db.session.commit()
    return jsonify({"message": f"Car: {vin}, successfully deleted."}), 200    

#Delete Car by license plate
@app.route("/car/plate/<string:license_plate>", methods=['DELETE'])
def delete_car_plate(license_plate):
    query = select(Car).where(Car.license_plate == license_plate)
    car = db.session.scalar(query)

    if not car:
        return jsonify({"error": "Car not found"}), 404
    
    db.session.delete(car)
    db.session.commit()
    return jsonify({"message": f"Car: {license_plate}, successfully deleted."}), 200  

# ===========================================================================
#                               Mechanic Routes
# ===========================================================================
#Create mechanic
@app.route("/mechanic", methods=['POST'])
def create_mechanic():
    try:
        mechanic_data = mechanic_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages)
    
    query = select(Mechanic).where(Mechanic.email == mechanic_data['email'])
    existing_mechanic = db.session.execute(query).scalars().all()

    if existing_mechanic:
        return jsonify({"error": "Car with same plate numbers"}), 400
    
    new_mechanic = Mechanic(**mechanic_data)
    db.session.add(new_mechanic)
    db.session.commit()

    return mechanic_schema.jsonify(new_mechanic), 201

#Get mechanics
@app.route("/mechanic", methods=['GET'])
def get_mechanics():
    query = select(Mechanic)
    mechanics = db.session.execute(query).scalars().all()

    return mechanics_schema.jsonify(mechanics), 200

#Get specific mechanics
@app.route("/mechanic/<int:mechanic_id>", methods=['GET'])
def get_mechanic(mechanic_id):
    mechanic = db.session.get(Mechanic, mechanic_id)

    if not mechanic:
        return jsonify({"error": "Mechanic not found"}), 400
    
    return mechanic_schema.jsonify(mechanic), 200

#Update specific mechanic
@app.route("/mechanic/<int:mechanic_id>", methods=['PUT'])
def update_mechanic(mechanic_id):
    mechanic = db.session.get(Mechanic, mechanic_id)

    if not mechanic:
        return jsonify({"error": "Mechanic not found"}), 400
    
    try:
        update_mechanic_data = mechanic_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    for key, value in update_mechanic_data.items():
        setattr(mechanic, key, value)

    db.session.commit()
    return mechanic_schema.jsonify(mechanic), 200

# ===========================================================================
#                               Ticket Routes
# ===========================================================================
@app.route("/create_ticket", methods=['POST'])
def create_ticket():
    try:
        ticket_data = mechanic_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages)

if __name__ == '__main__':
    with app.app_context():
        #db.drop_all()
        db.create_all()
    app.run(debug=True, port=5001)