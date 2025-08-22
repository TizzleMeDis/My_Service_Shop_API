from app.extensions import ma
from app.models import TicketInformation
from app.blueprints.inventory.schemas import TicketPartsSchema
class TicketInformationSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = TicketInformation
        load_instance = True
        include_relationships = True

    ticket_parts = ma.Nested(TicketPartsSchema, many=True)

ticket_information_schema = TicketInformationSchema()
ticket_information_schemas = TicketInformationSchema(many=True)