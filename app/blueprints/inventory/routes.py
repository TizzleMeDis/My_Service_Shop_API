from .schemas import inventory_schema, inventory_schemas
from flask import request, jsonify
from marshmallow import ValidationError
from sqlalchemy import select
from app.models import Inventory, db
from . import inventory_bp
from app.extensions import limiter


#Create item
@inventory_bp.route("/", methods=['POST'])
def create_item():
    try:
        item_data = inventory_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    query = select(Inventory).where(Inventory.part_name == item_data["part_name"])
    existing_item = db.session.execute(query).scalar_one_or_none()

    if existing_item:
        return jsonify({"error": "Item already in inventory"}), 400
    
    new_item = Inventory(**item_data)
    db.session.add(new_item)
    db.session.commit()

    return inventory_schema.jsonify(new_item), 201

#Get all items
@inventory_bp.route("/", methods=['GET'])
def get_items():
    try:
        page = int(request.args.get('page'))
        per_page = int(request.args.get('per_page'))
        query = select(Inventory)
        items = db.paginate(query, page=page, per_page=per_page)
    except:
        query = select(Inventory)
        items = db.session.execute(query).scalars().all()

    return inventory_schemas.jsonify(items), 200

#Get specific customer
@inventory_bp.route("/<int:part_id>", methods=['GET'])
def get_item(part_id):
    item = db.session.get(Inventory, part_id)

    if item:
        return inventory_schema.jsonify(item), 200
    else:
        return jsonify({"error": "Customer not found"}), 404

#Update item
@inventory_bp.route("/<int:part_id>", methods=['PUT'])
def update_item(part_id):
    item = db.session.get(Inventory, part_id)

    if not item:
        return jsonify({"error": "item not found"}), 404
    
    try:
        update_item_data = inventory_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    for key, value in update_item_data.items():
        setattr(item, key, value)
    print(item)
    db.session.commit()
    return inventory_schema.jsonify(item), 200

#Delete iteam
@inventory_bp.route("/<int:part_id>", methods=['DELETE'])
@limiter.limit("20 per day")
def delete_item(part_id):
    item = db.session.get(Inventory, part_id)

    if not item:
        return jsonify({"error": "item not found"}), 404
    
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": f"Inventory item: {item.part_name}, successfully deleted."}), 200