from jose import jwt, ExpiredSignatureError, JWTError
from datetime import datetime, timezone, timedelta
from functools import wraps
from flask import request, jsonify

SECRET_KEY = "Token Signature"
ALGORITHM = 'HS256'

def encode_token_customer(customer_id):
    payload = {
        'exp': datetime.now(timezone.utc) + timedelta(days=0, hours=1, minutes=0),
        'iat': datetime.now(timezone.utc),
        'sub': str(customer_id)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def customer_token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split()[1]

            if not token:
                return jsonify({"message": "missing token."}), 400
            
            try:
                data = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
                customer_id = data['sub']
            except ExpiredSignatureError:
                return jsonify({"message": "token expired."}), 400
            except JWTError:
                return jsonify({"message": "invalid token."}), 400
            
            return f(customer_id=customer_id, *args, **kwargs)
        else:
            return jsonify({"message": "Need to login to access this."}), 400
    
    return decorated

def encode_token_mechanic(mechanic_id):
    payload = {
        'exp': datetime.now(timezone.utc) + timedelta(days=0, hours=3, minutes=0),
        'iat': datetime.now(timezone.utc),
        'sub': str(mechanic_id)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def mechanic_token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split()[1]

            if not token:
                return jsonify({"message": "missing token."}), 400
            
            try:
                data = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
                mechanic_id = data['sub']
            except ExpiredSignatureError:
                return jsonify({"message": "token expired."}), 400
            except JWTError:
                return jsonify({"message": "invalid token."}), 400
            
            return f(mechanic_id=mechanic_id, *args, **kwargs)
        else:
            return jsonify({"message": "Need to login to access this."}), 400
    
    return decorated