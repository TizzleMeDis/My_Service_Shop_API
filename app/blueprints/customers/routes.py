from .schemas import customer_schema, customers_schema, login_schema
from app.blueprints.service_tickets.schemas import ticket_information_schemas
from flask import request, jsonify
from marshmallow import ValidationError
from sqlalchemy import select
from app.models import Customer, TicketInformation, db
from . import customers_bp
from app.extensions import limiter, cache
from app.utils.util import encode_token_customer, customer_token_required

#Login token generation
@customers_bp.route("/login", methods=['POST'])
def customer_login():
    try:
        user_credentials = login_schema.load(request.json)
        email = user_credentials['email']
        password = user_credentials['password']
    except ValidationError as err:
        return jsonify(err.messages), 400

    query = select(Customer).where(Customer.email == email)
    customer = db.session.execute(query).scalar_one_or_none()

    if customer and customer.password == password:
        token = encode_token_customer(customer.id)

        response = {
            "status": "success",
            "message": "successfully logged in.",
            "token": token
        }

        return jsonify(response), 200
    else:
        return jsonify({"message": "Invalid email or password"}), 400


#Create customers
@customers_bp.route("/", methods=['POST'])
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
@customers_bp.route("/", methods=['GET'])
def get_customers():
    try:
        page = int(request.args.get('page'))
        per_page = int(request.args.get('per_page'))
        query = select(Customer)
        customers = db.paginate(query, page=page, per_page=per_page)
    except:
        query = select(Customer)
        customers = db.session.execute(query).scalars().all()

    return customers_schema.jsonify(customers), 200

#Get specific customer
@customers_bp.route("/customer", methods=['GET'])
@customer_token_required
def get_customer(customer_id):
    customer = db.session.get(Customer, customer_id)

    if customer:
        return customer_schema.jsonify(customer), 200
    else:
        return jsonify({"error": "Customer not found"}), 404

#Get specific customer tickets
@customers_bp.route("/customer_tickets", methods=['GET'])
@customer_token_required
def get_customer_tickets(customer_id):
    customer = db.session.get(Customer, customer_id)

    if not customer:
        return jsonify({"error": "Customer not found"}), 400

    all_tickets = []
    for car in customer.cars:
        all_tickets.extend(car.services)
    
    if len(all_tickets) == 0:
        return jsonify({"message": "No data found"}), 200
    
    return jsonify(ticket_information_schemas.dump(all_tickets)), 200

#Get customer total cost
@customers_bp.route("/customer_cost", methods=['GET'])
@customer_token_required
def get_customer_cost(customer_id):
    customer = db.session.get(Customer, customer_id)

    if not customer:
        return jsonify({"error": "Customer not found"}), 400

    all_tickets = []
    for car in customer.cars:
        all_tickets.extend(car.services)

    sum = 0
    for ticket in all_tickets:
        sum += ticket.labor_cost or 0

    return jsonify({"Total cost": f"{sum}"}), 200


#Update customer
@customers_bp.route("/", methods=['PUT'])
@customer_token_required
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
@customers_bp.route("/", methods=['DELETE'])
@customer_token_required
@limiter.limit("20 per day")
def delete_customer(customer_id):
    customer = db.session.get(Customer, customer_id)

    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    
    if customer.cars:
        return jsonify({"error": f"Delete owner {len(customer.cars)} car(s) first"}), 400
    
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": f"Customer id: {customer_id}, successfully deleted."}), 200