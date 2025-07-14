from .schemas import ticket_information_schema, ticket_information_schemas
from flask import request, jsonify
from marshmallow import ValidationError
from sqlalchemy import select, insert, delete
from app.models import TicketInformation, Mechanic, Car, service_tickets, db
from . import service_tickets_bp

#Create ticket with information (no assignments)
@service_tickets_bp.route("/", methods=['POST'])
def create_ticket():
    try:
        ticket_data = ticket_information_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    new_ticket = ticket_data
    db.session.add(new_ticket)
    db.session.commit()
    return ticket_information_schema.jsonify(new_ticket)

#Create ticket with information (assigned)
@service_tickets_bp.route("/mechanics/<int:mechanic_id>/assign_car/<string:vin>", methods=['POST'])
def create_ticket_mechanic_car(mechanic_id, vin):
    try:
        ticket_data = ticket_information_schema.load(request.json)
    except ValidationError as err:
        print("Validation Error:", err.messages)
        return jsonify(err.messages), 400
    
    mechanic = db.session.get(Mechanic, mechanic_id)
    car = db.session.get(Car, vin)

    if not car:
        return jsonify({"error": "Car not found"}), 400
    
    if not mechanic:
        return jsonify({"error": "Mechanic not found"}), 400
    
    new_ticket = ticket_data
    db.session.add(new_ticket)
    db.session.flush()

    stmt = insert(service_tickets).values(
        id=new_ticket.id,
        car_vin=vin,
        mechanic_id=mechanic_id
    )
    db.session.execute(stmt)
    db.session.commit()
    print("New ticket created")
    return ticket_information_schema.jsonify(new_ticket), 201
    
@service_tickets_bp.route("", methods=['GET'])
def get_all_tickets():
    query = select(TicketInformation)
    service_tickets = db.session.execute(query).scalars().all()

    return ticket_information_schemas.jsonify(service_tickets), 200 

@service_tickets_bp.route("/<int:ticket_id>", methods=['GET'])
def get_specific_ticket(ticket_id):
    ticket = db.session.get(TicketInformation, ticket_id)

    if not ticket:
        return jsonify({"error": "Ticket not found"}), 400
    return ticket_information_schema.jsonify(ticket), 200

#Update ticket information
@service_tickets_bp.route("/<int:ticket_id>", methods=['PUT'])
def update_ticket(ticket_id):
    ticket = db.session.get(TicketInformation, ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found"})
    
    try:
        update_ticket_data = ticket_information_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    for key, value in update_ticket_data.__dict__.items():
        if key != "_sa_instance_state":
            setattr(ticket, key, value)
    setattr(ticket, "id", ticket_id)
    db.session.commit()
    return ticket_information_schema.jsonify(update_ticket_data), 200

#Assigning mechanic to ticket.
@service_tickets_bp.route("/<int:ticket_id>/assign-mechanic/<int:mechanic_id>", methods=['PUT'])
def assign_mechanic(ticket_id, mechanic_id):
    ticket = db.session.get(TicketInformation, ticket_id)
    mechanic = db.session.get(Mechanic, mechanic_id)
    
    query = select(service_tickets).where(service_tickets.c.id == ticket_id)
    existing_ticket = db.session.execute(query).fetchone()

    if not ticket:
        return jsonify({"error": "Ticket not found"}), 400
    if not mechanic:
        return jsonify({"error": "Mechanic not found"}), 400
    if existing_ticket: #Make sure if ticket was made to update open ticket instead of inserting individual entry
        stmt = (
            service_tickets.update()
            .where(service_tickets.c.id == ticket_id)
            .values(mechanic_id = mechanic_id))
    else:
        stmt = insert(service_tickets).values(
            id=ticket.id,
            mechanic_id=mechanic_id
        )

    db.session.execute(stmt)
    db.session.commit()
    return jsonify({"Completed": "Mechanic assigned to ticket"}), 200

#Assigning car to ticket.
@service_tickets_bp.route("/<int:ticket_id>/assign_car/<string:vin>", methods=['PUT'])
def assign_car(ticket_id, vin):
    ticket = db.session.get(TicketInformation, ticket_id)
    car = db.session.get(Car, vin)
    query = select(service_tickets).where(service_tickets.c.id == ticket_id)
    existing_ticket = db.session.execute(query).fetchone()

    if not ticket:
        return jsonify({"error": "Ticket not found"}), 400
    if not car:
        return jsonify({"error": "Car not found"}), 400
    if existing_ticket: #Make sure if ticket was made to update open ticket instead of inserting individual entry
        stmt = (
            service_tickets.update()
            .where(service_tickets.c.id == ticket_id)
            .values(car_vin = vin))
    else:
        stmt = insert(service_tickets).values(
            id=ticket.id,
            car_vin=vin
        )

    db.session.execute(stmt)
    db.session.commit()
    return jsonify({"Completed": "Car assigned to ticket"}), 200

@service_tickets_bp.route("/<int:ticket_id>", methods=['DELETE'])
def delete_ticket(ticket_id):
    ticket = db.session.get(TicketInformation, ticket_id)

    if not ticket:
        return jsonify({"error": "Ticket not found"}), 400
    
    stmt = delete(service_tickets).where(service_tickets.c.id == ticket_id)
    db.session.execute(stmt)
    db.session.delete(ticket)
    db.session.commit()

    return jsonify({"message": f"Ticket {ticket_id} successfully deleted."}), 200