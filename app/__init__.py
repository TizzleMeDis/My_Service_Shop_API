from flask import Flask
from .extensions import ma, limiter, cache
from .models import db
from .blueprints.customers import customers_bp
from .blueprints.cars import cars_bp
from .blueprints.mechanics import mechanics_bp
from .blueprints.service_tickets import service_tickets_bp
from .blueprints.inventory import inventory_bp

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(f'config.{config_name}')

    #Initialize extensions
    ma.init_app(app)
    db.init_app(app)
    limiter.init_app(app)
    cache.init_app(app)
    
    #Register Blueprints
    app.register_blueprint(customers_bp, url_prefix='/customers')
    app.register_blueprint(cars_bp, url_prefix='/cars')
    app.register_blueprint(mechanics_bp, url_prefix='/mechanics')
    app.register_blueprint(service_tickets_bp, url_prefix='/service_tickets')
    app.register_blueprint(inventory_bp, url_prefix='/inventory')
    
    return app