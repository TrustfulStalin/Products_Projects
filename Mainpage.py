from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy import Integer, String, DateTime, ForeignKey, Float, func
from sqlalchemy.orm import relationship
from marshmallow import ValidationError
import marshmallow_sqlalchemy as ma
from marshmallow import fields

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = 'mysql+mysqlconnector://root:1127@localhost/product_api'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # Disable modification tracking

# Initialize Flask-SQLAlchemy and Marshmallow
db = SQLAlchemy(app)
ma = Marshmallow(app)

# Define the User model
class User(db.Model):  # Use db.Model for SQLAlchemy models
    __tablename__ = 'user'

    id = db.Column(Integer, primary_key=True, autoincrement=True)
    name = db.Column(String(100), nullable=False)
    email = db.Column(String(100), unique=True)

    orders = relationship("Order", back_populates="user")

# Define the Order model
class Order(db.Model):  # Use db.Model for SQLAlchemy models
    __tablename__ = 'order'

    id = db.Column(Integer, primary_key=True, autoincrement=True)
    order_date = db.Column(DateTime, default=func.now())
    user_id = db.Column(Integer, ForeignKey('user.id'))

    user = relationship("User", back_populates="orders")
    order_products = relationship("Order_Product", back_populates="order")

# Define the Product model
class Product_Table(db.Model):  # Use db.Model for SQLAlchemy models
    __tablename__ = 'Product_Table'

    id = db.Column(Integer, primary_key=True, autoincrement=True)
    product_name = db.Column(String(100))
    price = db.Column(Float)

    order_products = relationship("Order_Product", back_populates="product")

# Define the Order_Product model
class Order_Product(db.Model):  # Use db.Model for SQLAlchemy models
    __tablename__ = 'Order_Product'

    order_id = db.Column(Integer, ForeignKey('order.id'), primary_key=True)
    product_id = db.Column(Integer, ForeignKey('Product_Table.id'), primary_key=True)

    order = relationship("Order", back_populates="order_products")
    product = relationship("Product_Table", back_populates="order_products")

# Marshmallow Schemas for validation and serialization
class UserSchema(ma.SQLAlchemySchema):
    class Meta:
        model = User

    name = fields.String(required=True)
    email = fields.Email(required=True)

class OrderSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Order

    
    order_date = fields.DateTime(required=True)
    user_id = fields.Integer(required=True)   



class Product_TableSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Product_Table

    
    product_name = fields.String(required=True)
    price = fields.Float(required=True)    

class Order_ProductSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Order_Product
    order_id = fields.Integer(ForeignKey = True, required=True)    
    product_id = fields.Integer(ForeignKey = True, required=True)


@app.route('/users', methods=['POST'])
def create_user():
    try:
        # Load and validate user data from the request
        user_data = UserSchema().load(request.json)

        # Check if the required fields are present
        if not user_data.get('name') or not user_data.get('email'):
            return jsonify({"error": "Both 'name' and 'email' are required."}), 400
        
    except ValidationError as e:
        # Return validation errors as response
        return jsonify(e.messages), 400

    # Create a new User object (No need to set the 'id', it will be auto-generated)
    new_user = User(name=user_data['name'], email=user_data['email'])

    # Add the user to the session and commit
    db.session.add(new_user)
    db.session.commit()

    # Serialize and return the created user as JSON response
    return jsonify(UserSchema().dump(new_user)), 201


# GET route to fetch all users
@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()  # Query all users from the database

    # Serialize and return users as JSON response
    return jsonify(UserSchema(many=True).dump(users)), 200


# GET route to fetch a single user by ID
@app.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    user = User.query.get(id)  # Use query.get for fetching by primary key

    if not user:
        return jsonify({"error": "User not found."}), 404

    # Serialize and return the user as JSON response
    return jsonify(UserSchema().dump(user)), 200



@app.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    # Fetch the user by the provided id
    user = db.session.get(User, id)
    
    # If user does not exist, return a 404 error
    if not user:
        return jsonify({"message": "Invalid user id"}), 400

    try:
        # Load and validate the updated data from the request
        user_data = UserSchema().load(request.json)

        # Check if 'name' and 'email' are part of the request data
        if 'name' in user_data:
            user.name = user_data['name']
        if 'email' in user_data:
            user.email = user_data['email']

        # Commit the changes to the database
        db.session.commit()

        # Serialize the updated user and return it as a response
        return jsonify(UserSchema().dump(user)), 200

    except ValidationError as e:
        # Handle validation errors and return them as a response
        return jsonify(e.messages), 400


@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    # Fetch the user by the provided id
    user = db.session.get(User, id)
    
    # If user does not exist, return a 404 error
    if not user:
        return jsonify({"message": "User not found"}), 404

    # Delete the user from the database
    db.session.delete(user)
    db.session.commit()

    # Return a success message
    return jsonify({"message": f"User with id {id} has been deleted."}), 200    

    # GET route to retrieve all products
@app.route('/products', methods=['GET'])
def get_products():
    products = Product_Table.query.all()  # Query all products from the database
    return jsonify(Product_TableSchema(many=True).dump(products)), 200


# GET route to retrieve a single product by ID
@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    product = Product_Table.query.get(id)
    if not product:
        return jsonify({"error": "Product not found."}), 404
    return jsonify(Product_TableSchema().dump(product)), 200


# POST route to create a new product
@app.route('/products', methods=['POST'])
def create_product():
    try:
        product_data = Product_TableSchema().load(request.json)

        # Create a new Product object
        new_product = Product_Table(
            product_name=product_data['product_name'],
            price=product_data['price']
        )

        db.session.add(new_product)
        db.session.commit()

        return jsonify(Product_TableSchema().dump(new_product)), 201

    except ValidationError as e:
        return jsonify(e.messages), 400


# PUT route to update a product by ID
@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = db.session.get(Product_Table, id)

    if not product:
        return jsonify({"error": "Product not found."}), 404

    try:
        product_data = Product_TableSchema().load(request.json)

        if 'product_name' in product_data:
            product.product_name = product_data['product_name']
        if 'price' in product_data:
            product.price = product_data['price']

        db.session.commit()

        return jsonify(Product_TableSchema().dump(product)), 200

    except ValidationError as e:
        return jsonify(e.messages), 400


# DELETE route to delete a product by ID
@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = db.session.get(Product_Table, id)

    if not product:
        return jsonify({"error": "Product not found."}), 404

    db.session.delete(product)
    db.session.commit()

    return jsonify({"message": f"Product with id {id} has been deleted."}), 200   

    # POST route to create a new order
@app.route('/orders', methods=['POST'])
def create_order():
    user_id = request.json.get('user_id')
    order_date = request.json.get('order_date', func.now())

    # Validate if the user exists
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found."}), 404

    new_order = Order(user_id=user_id, order_date=order_date)
    db.session.add(new_order)
    db.session.commit()

    return jsonify(OrderSchema().dump(new_order)), 201


# GET route to fetch all products in a given order
@app.route('/orders/<int:order_id>/products', methods=['GET'])
def get_order_products(order_id):
    order = db.session.get(Order, order_id)

    if not order:
        return jsonify({"error": "Order not found."}), 404

    # Fetch associated products for the order
    order_products = order.order_products
    return jsonify(Order_ProductSchema(many=True).dump(order_products)), 200


# POST route to add a product to an order (prevent duplicates)
@app.route('/orders/<int:order_id>/add_product/<int:product_id>', methods=['POST'])
def add_product_to_order(order_id, product_id):
    order = db.session.get(Order, order_id)
    product = db.session.get(Product_Table, product_id)

    if not order:
        return jsonify({"error": "Order not found."}), 404
    if not product:
        return jsonify({"error": "Product not found."}), 404

    # Check if the product is already added to the order
    existing_order_product = db.session.query(Order_Product).filter_by(order_id=order_id, product_id=product_id).first()
    if existing_order_product:
        return jsonify({"error": "Product is already in this order."}), 400

    # Add the product to the order
    new_order_product = Order_Product(order_id=order_id, product_id=product_id)
    db.session.add(new_order_product)
    db.session.commit()

    return jsonify(Order_ProductSchema().dump(new_order_product)), 201


# DELETE route to remove a product from an order
@app.route('/orders/<int:order_id>/remove_product', methods=['DELETE'])
def remove_product_from_order(order_id):
    product_id = request.json.get('product_id')
    order = db.session.get(Order, order_id)

    if not order:
        return jsonify({"error": "Order not found."}), 404

    # Find the product in the order
    order_product = db.session.query(Order_Product).filter_by(order_id=order_id, product_id=product_id).first()

    if not order_product:
        return jsonify({"error": "Product not found in this order."}), 404

    # Delete the product from the order
    db.session.delete(order_product)
    db.session.commit()

    return jsonify({"message": f"Product with id {product_id} has been removed from order {order_id}."}), 200


# GET route to fetch all orders for a specific user
@app.route('/orders/user/<int:user_id>', methods=['GET'])
def get_orders_by_user(user_id):
    user = db.session.get(User, user_id)

    if not user:
        return jsonify({"error": "User not found."}), 404

    # Fetch orders for the user
    orders = user.orders
    return jsonify(OrderSchema(many=True).dump(orders)), 200




if __name__ == '__main__':
    app.run(debug=True)
    
    # Create all tables before the first request
@app.before_first_request
def create_tables():
    db.create_all()  # Creates all tables if they do not exist
