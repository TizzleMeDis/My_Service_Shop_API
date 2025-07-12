from .schemas import car_schema, cars_schema
from app.models import Customer
from flask import request, jsonify
from marshmallow import ValidationError
from sqlalchemy import select
from app.models import Car, db
from . import cars_bp

#Create car
@cars_bp.route("/", methods=['POST'])
def create_car():
    try:
        car_data = car_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    customer = db.session.get(Customer, car_data['customer_id'])
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
@cars_bp.route("/", methods=['GET'])
def get_cars():
    query = select(Car)
    cars = db.session.execute(query).scalars().all()

    return cars_schema.jsonify(cars), 200

#Get specific car
@cars_bp.route("/plate/<string:license_plate>", methods=['GET'])
def get_car_plate(license_plate):
    query = select(Car).where(Car.license_plate == license_plate)
    car = db.session.scalar(query)

    if car:
        return car_schema.jsonify(car), 200
    else:
        return jsonify({"error": "Car not found"}), 404
    
#Get specific car
@cars_bp.route("/vin/<string:vin>", methods=['GET'])
def get_car_id(vin):
    car = db.session.get(Car, vin)

    if car:
        return car_schema.jsonify(car), 200
    else:
        return jsonify({"error": "Car not found"}), 404

#Update specific car
@cars_bp.route("/plate/<string:license_plate>", methods=['PUT'])
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
@cars_bp.route("/vin/<string:vin>", methods=['PUT'])
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
@cars_bp.route("/vin/<string:vin>", methods=['DELETE'])
def delete_car_vin(vin):
    car = db.session.get(Car, vin)

    if not car:
        return jsonify({"error": "Car not found"}), 404
    
    db.session.delete(car)
    db.session.commit()
    return jsonify({"message": f"Car: {vin}, successfully deleted."}), 200    

#Delete Car by license plate
@cars_bp.route("/plate/<string:license_plate>", methods=['DELETE'])
def delete_car_plate(license_plate):
    query = select(Car).where(Car.license_plate == license_plate)
    car = db.session.scalar(query)

    if not car:
        return jsonify({"error": "Car not found"}), 404
    
    db.session.delete(car)
    db.session.commit()
    return jsonify({"message": f"Car: {license_plate}, successfully deleted."}), 200  