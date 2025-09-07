from .schemas import mechanic_schema, mechanics_schema, login_schema
from app.blueprints.service_tickets.schemas import ticket_information_schemas
from flask import request, jsonify
from marshmallow import ValidationError
from sqlalchemy import select
from app.models import Mechanic, db
from . import mechanics_bp
from app.extensions import limiter
from app.utils.util import encode_token_mechanic, mechanic_token_required
from datetime import datetime
#mechanic login
@mechanics_bp.route("/login", methods=['POST'])
def mechanic_login():
    try:
        mechanic_credentials = login_schema.load(request.json)
        email = mechanic_credentials['email']
        password = mechanic_credentials['password']
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    query = select(Mechanic).where(Mechanic.email == email)
    mechanic = db.session.execute(query).scalar_one_or_none()

    if mechanic and mechanic.password == password:
        token = encode_token_mechanic(mechanic.id)

        response = {
            "status": "success",
            "message": "successfully logged in.",
            "token": token
        }

        return jsonify(response), 200
    else:
        return jsonify({"message": "Invalid email or password"}), 400


#Create mechanic
@mechanics_bp.route("/", methods=['POST'])
def create_mechanic():
    try:
        mechanic_data = mechanic_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages)
    
    query = select(Mechanic).where(Mechanic.email == mechanic_data['email'])
    existing_mechanic = db.session.execute(query).scalars().all()

    if existing_mechanic:
        return jsonify({"error": "Mechanic with same email"}), 400
    
    new_mechanic = Mechanic(**mechanic_data)
    db.session.add(new_mechanic)
    db.session.commit()

    return mechanic_schema.jsonify(new_mechanic), 201

#Get mechanics
@mechanics_bp.route("/", methods=['GET'])
def get_mechanics():
    try:
        page = int(request.args.get('page'))
        per_page = int(request.args.get('per_page'))
        query = select(Mechanic)
        mechanics = db.paginate(query, page=page, per_page=per_page)
    except:
        query = select(Mechanic)
        mechanics = db.session.execute(query).scalars().all()

    return mechanics_schema.jsonify(mechanics), 200

#Get specific mechanic
@mechanics_bp.route("/mechanic", methods=['GET'])
@mechanic_token_required
def get_mechanic(mechanic_id):
    mechanic = db.session.get(Mechanic, mechanic_id)

    if not mechanic:
        return jsonify({"error": "Mechanic not found"}), 400
    
    return mechanic_schema.jsonify(mechanic), 200

#Get mechanic's jobs
@mechanics_bp.route("/jobs", methods=['GET'])
@mechanic_token_required
def get_jobs_by_mechanic(mechanic_id):
    mechanic = db.session.get(Mechanic, mechanic_id)

    if not mechanic:
        return jsonify({"error": "Mechanic not found."}), 400
    
    return ticket_information_schemas.jsonify(mechanic.tickets), 200

#Get mechanic's jobs (by date)
@mechanics_bp.route("/job", methods=['GET'])
@mechanic_token_required
def get_jobs_by_date(mechanic_id):
    mechanic = db.session.get(Mechanic, mechanic_id)
    date = request.args.get("service_date")

    if not mechanic:
        return jsonify({"error": "Mechanic not found."}), 400

    if not date:
        return jsonify({"error": "Missing required parameter: service_date"}), 400

    try:
        parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    # filter tickets by date
    tickets = [ticket for ticket in mechanic.tickets if ticket.service_date == parsed_date]

    if not tickets:
        return jsonify({"message": "No data found."}), 200
    
    return ticket_information_schemas.jsonify(tickets), 200

#Order mechanics by amount of tickets
@mechanics_bp.route("/leaderboard", methods=['GET'])
def order_mechanics_by_job():
    mechanics = db.session.execute(select(Mechanic)).scalars().all()
    
    mechanics_with_counts = [
        {
            "id": mechanic.id,
            "name": mechanic.name,  # adjust if your field is named differently
            "ticket_count": len(mechanic.tickets),
            "profit": sum(ticket.total_cost for ticket in mechanic.tickets)
        }
        for mechanic in mechanics
    ]

    mechanics_with_counts.sort(key=lambda m: m["ticket_count"], reverse=True)

    return jsonify(mechanics_with_counts), 200

#Update specific mechanic
@mechanics_bp.route("/", methods=['PUT'])
@mechanic_token_required
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

#Delete mechanic
@mechanics_bp.route("/", methods=['DELETE'])
@mechanic_token_required
@limiter.limit("20 per day")
def delete_mechanic(mechanic_id):
    mechanic = db.session.get(Mechanic, mechanic_id)
    
    if not mechanic:
        return jsonify({"error": "Mechanic not found"}), 400

    db.session.delete(mechanic)
    db.session.commit()

    return jsonify({"message": f"Mechanic id: {mechanic_id}, successfully deleted."}), 200

