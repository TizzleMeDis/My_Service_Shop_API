from app.extensions import ma
from app.models import Inventory, TicketPart

class InventorySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Inventory
        include_relationships = True

    ticket_parts = ma.Nested('TicketPartsSchema', many=True, dump_only=True)


class TicketPartsSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = TicketPart
        include_fk = True

    quantity = ma.auto_field()
    part_cost = ma.auto_field()
    part_name = ma.Method("get_part_name")

    def get_part_name(self, obj):
        return obj.inventory.part_name if obj.inventory else None
    

inventory_schema = InventorySchema()
inventory_schemas = InventorySchema(many=True)

ticket_part_schema = TicketPartsSchema()
ticket_parts_schema = TicketPartsSchema(many=True)