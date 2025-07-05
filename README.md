# Mechanic Service Shop API

Build Custom with Python and Tech listed below
- SQLAlchemy
- Flask
- Marshmallow

## Code is usible with Postman
Prerouted structures to interact with back-end using URL request
Examples of use:

Route:
### Create Customer

Post: https://ServerName/customers
Payload:
{
     "email": "tisdalea@email.com",
     "name": "Anthony",
     "phone": "2098089454"
}

### See Customers

Get: https://ServerName/customers
Result:
[
    {
        "cars": [
            "1HGCM82633A123456"
        ],
        "email": "tisdalea@email.com",
        "id": 1,
        "name": "Anthony",
        "phone": "2098089454"
    }
]
### Create Car

Post: https://ServerName/cars
Payload:
{
    "license_plate": "7ABC123",
    "make": "Honda",
    "mechanics": [],
    "model": "Accord",
    "owner": 1,
    "vin": "1HGCM82633A123456",
    "year": "2021"
}


Code is not made for commercial use.
Here to showcase building skills with SQL and Pyhton
