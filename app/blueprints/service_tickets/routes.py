from .schemas import ticket_information_schema, ticket_information_schemas
from app.blueprints.inventory.schemas import ticket_parts_schema
from flask import request, jsonify
from marshmallow import ValidationError
from sqlalchemy import select, insert, delete, and_
from app.models import TicketInformation, Mechanic, Car, Inventory, TicketPart, service_tickets, db
from . import service_tickets_bp
from app.extensions import limiter, cache
from app.utils.util import mechanic_token_required

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

    # Insert ticket into junction table with no mechanic or car yet
    stmt = service_tickets.insert().values(
        id=new_ticket.id,  # only setting ticket id
        mechanic_id=None,
        car_vin=None
    )

    db.session.execute(stmt)
    db.session.commit()

    return ticket_information_schema.jsonify(new_ticket)

#Create ticket with information (assigned)
@service_tickets_bp.route("/assign_car/<string:vin>", methods=['POST'])
@mechanic_token_required
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
    
@service_tickets_bp.route("/", methods=['GET'])
def get_all_tickets():
    try:
        page = int(request.args.get('page'))
        per_page = int(request.args.get('per_page'))
        query = select(TicketInformation)
        service_tickets = db.paginate(query, page=page, per_page=per_page)
    except:
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
@service_tickets_bp.route("/<int:ticket_id>/assign_mechanic", methods=['PUT'])
@mechanic_token_required
def assign_mechanic(ticket_id, mechanic_id):

    ticket = db.session.get(TicketInformation, ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found"}), 400

    query = select(Mechanic).join(service_tickets).where(service_tickets.c.id==ticket_id)
    mechanics = db.session.execute(query).scalars().all()
    print(mechanics)
    if len(mechanics) == 0:
        print("Assigning to empty ticket")
        stmt = (
            service_tickets.update().where(
                service_tickets.c.id == ticket_id,
                service_tickets.c.mechanic_id.is_(None)
            ).values(
                mechanic_id=mechanic_id
            )
        )
    else:
        print("Assigning to ticket")

        for mechanic in mechanics: #Checks if mechanic is in the list
            if int(mechanic.id) == int(mechanic_id):
                return jsonify({"message": "Mechanic Already Assigned"}), 200

        query = select(service_tickets.c.car_vin).where(service_tickets.c.id==ticket_id)
        car_vin = db.session.execute(query).fetchone()[0]

        print("Vin: ", car_vin)
        stmt = insert(service_tickets).values(
            id=ticket_id,
            car_vin=car_vin,
            mechanic_id=mechanic_id
        )

    db.session.execute(stmt)
    db.session.commit()
    return jsonify({"Completed": "Mechanic assigned to ticket"}), 201

#Removing mechanic from ticket.
@service_tickets_bp.route("/<int:ticket_id>/remove_mechanic", methods=['PUT'])
@mechanic_token_required
def remove_mechanic(ticket_id, mechanic_id):
    ticket = db.session.get(TicketInformation, ticket_id)
    mechanic = db.session.get(Mechanic, mechanic_id)

    if not ticket:
        return jsonify({"error": "Ticket not found"}), 400
    if not mechanic:
        return jsonify({"error": "Mechanic not found"}), 400

    # Check if the mechanic is assigned to this ticket
    query = select(service_tickets).where(
        and_(
            service_tickets.c.id == ticket_id,
            service_tickets.c.mechanic_id == mechanic_id
        )
    )
    existing_assignment = db.session.execute(query).fetchone()

    if not existing_assignment:
        return jsonify({"error": "Mechanic is not assigned to this ticket"}), 400

    #Delete the specific mechanic assignment from the junction table
    stmt = service_tickets.delete().where(
        and_(
            service_tickets.c.id == ticket_id,
            service_tickets.c.mechanic_id == mechanic_id
        )
    )
    db.session.execute(stmt)
    db.session.commit()

    return jsonify({"message": "Mechanic removed from ticket"}), 200

#Assigning car to ticket.
@service_tickets_bp.route("/<int:ticket_id>/assign_car/<string:vin>", methods=['PUT'])
def assign_car(ticket_id, vin):
    ticket = db.session.get(TicketInformation, ticket_id)
    car = db.session.get(Car, vin)

    if not ticket:
        return jsonify({"error": "Ticket not found"}), 400
    if not car:
        return jsonify({"error": "Car not found"}), 400

    # First, check if a service_tickets row exists for this ticket_id
    query = select(service_tickets).where(service_tickets.c.id == ticket_id)
    existing_entry = db.session.execute(query).fetchone()

    if existing_entry:
        # UPDATE the row, regardless of whether car_vin is null or not
        stmt = (
            service_tickets.update()
            .where(service_tickets.c.id == ticket_id)
            .values(car_vin=vin)
        )
    else:
        # INSERT only if no row exists yet
        stmt = insert(service_tickets).values(
            id=ticket.id,
            car_vin=vin
        )

    db.session.execute(stmt)
    db.session.commit()
    return jsonify({"Completed": "Car assigned to ticket"}), 200


# Assigning car parts to ticket.
@service_tickets_bp.route("/<int:ticket_id>/assign_parts/<int:part_id>", methods=['PUT'])
def assign_parts(ticket_id, part_id):
    ticket = db.session.get(TicketInformation, ticket_id)
    part = db.session.get(Inventory, part_id)

    if not ticket:
        return jsonify({"error": "Ticket not found"}), 400
    if not part:
        return jsonify({"error": "Part not found"}), 400

    data = request.get_json()
    quantity = data.get("quantity", 1)  # Default to 1 if not provided

    # Check if part is already assigned to the ticket
    ticket_part = next((tp for tp in ticket.ticket_parts if tp.inventory_id == part_id), None)

    if ticket_part:
        # Update existing quantity
        ticket_part.quantity += quantity
    else:
        # Create new TicketPart entry (store unit cost, not multiplied)
        ticket_part = TicketPart(
            ticket_id=ticket.id,
            inventory_id=part.id,
            quantity=quantity,
            part_cost=part.part_cost  # ✅ keep it as unit price
        )
        db.session.add(ticket_part)

    # ✅ Update total cost (labor + all parts)
    parts_total = sum(tp.quantity * tp.part_cost for tp in ticket.ticket_parts)
    print(parts_total)
    ticket.total_cost = (ticket.labor_cost or 0) + parts_total

    db.session.commit()

    return jsonify({
        "message": "Part assigned successfully",
        "ticket": {
            "id": ticket.id,
            "total_cost": ticket.total_cost,
            "parts": ticket_parts_schema.dump(ticket.ticket_parts)
        }
    }), 200
    
# Removing car parts from ticket.
@service_tickets_bp.route("/<int:ticket_id>/remove_parts/<int:part_id>", methods=['DELETE'])
def remove_parts(ticket_id, part_id):
    ticket = db.session.get(TicketInformation, ticket_id)
    part = db.session.get(Inventory, part_id)

    if not ticket:
        return jsonify({"error": "Ticket not found"}), 400
    if not part:
        return jsonify({"error": "Part not found"}), 400

    data = request.get_json()
    quantity = data.get("quantity", 1)  # Default to 1 if not provided

    # Check if part is already assigned to the ticket
    ticket_part = next((tp for tp in ticket.ticket_parts if tp.inventory_id == part_id), None)

    if ticket_part:
        # Update existing quantity
        if ticket_part.quantity >= quantity:
            ticket_part.quantity -= quantity
        else:
            ticket_part.quantity = 0
    else:
        # Let user know this part wasn't found
        return jsonify({"error": "part wasn't order already."}), 400

    # ✅ Update total cost (labor + all parts)
    parts_total = sum(tp.quantity * tp.part_cost for tp in ticket.ticket_parts)
    print(parts_total)
    ticket.total_cost = (ticket.labor_cost or 0) + parts_total

    db.session.commit()

    return jsonify({
        "message": "Part removed successfully",
        "ticket": {
            "id": ticket.id,
            "total_cost": ticket.total_cost,
            "parts": ticket_parts_schema.dump(ticket.ticket_parts)
        }
    }), 200

@service_tickets_bp.route("/<int:ticket_id>", methods=['DELETE'])
@limiter.limit("20 per day")
def delete_ticket(ticket_id):
    ticket = db.session.get(TicketInformation, ticket_id)

    if not ticket:
        return jsonify({"error": "Ticket not found"}), 400
    
    stmt = delete(service_tickets).where(service_tickets.c.id == ticket_id)
    db.session.execute(stmt)
    db.session.delete(ticket)
    db.session.commit()

    return jsonify({"message": f"Ticket {ticket_id} successfully deleted."}), 200