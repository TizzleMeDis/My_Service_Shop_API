from app.extensions import ma
from app.models import Customer

class CustomerSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Customer
        include_relationships = True

customer_schema =CustomerSchema()
customers_schema = CustomerSchema(many=True) #variant that allows for the serialization of many Users,
login_schema = CustomerSchema(exclude=['name', 'phone'])