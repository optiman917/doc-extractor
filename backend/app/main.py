import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv
from .database import db
from . import models
from datetime import datetime

# This will be populated with the content of models.py
MODELS_SCHEMA = ""
try:
    with open(os.path.join(os.path.dirname(__file__), 'models.py'), 'r') as f:
        MODELS_SCHEMA = f.read()
except Exception as e:
    print(f"Could not read models.py: {e}")


load_dotenv()

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['UPLOAD_FOLDER'] = os.path.join(basedir, '..', 'uploads')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    return app

app = create_app()

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def extract_json_from_response(text):
    """Extracts JSON object from a string."""
    try:
        # Find the start and end of the JSON block
        json_start = text.find('```json')
        if json_start == -1:
            # Fallback for plain JSON without backticks
            return json.loads(text)

        json_start += len('```json')
        json_end = text.find('```', json_start)
        
        # Extract and parse the JSON string
        json_str = text[json_start:json_end].strip()
        return json.loads(json_str)
    except (json.JSONDecodeError, AttributeError, ValueError) as e:
        print(f"Error decoding JSON: {e}")
        return None

@app.route("/")
def hello_world():
    return "Hello, from Flask backend!"

@app.route("/test_db")
def test_db():
    try:
        # Try to execute a simple query
        result = db.session.execute(db.text('SELECT 1')).scalar()
        if result == 1:
            return "Database connection successful!"
        else:
            return "Database connection test failed."
    except Exception as e:
        return f"Database connection failed: {e}"

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            img = Image.open(filepath)
            model = genai.GenerativeModel('gemini-2.5-pro')
            
            prompt = f"""
            You are an expert invoice data extractor. Your goal is to extract all possible information from the invoice image to provide a detailed, structured response.

            First, extract the following information from the invoice:
            - Customer's Full Name
            - Billing Address (if different from shipping, otherwise use shipping)
            - Shipping Address
            - Invoice Number (map to SalesOrderNumber)
            - Order Date
            - Due Date
            - Ship Date
            - Account Number
            - Subtotal
            - Tax Amount (map to TaxAmt)
            - Shipping & Handling cost (map to Freight)
            - Total Due
            - A list of all products, including their Product Code/Number, Quantity, and Unit Price.

            Based on this, construct a single JSON object with keys: "SalesOrderHeader", "SalesOrderDetail", "CustomerName", "BillingAddress", "ShippingAddress".

            - For "SalesOrderHeader" and "SalesOrderDetail", use the field names from the models below.
            - Calculate `LineTotal` for each item in "SalesOrderDetail".
            - For product details in "SalesOrderDetail", only include `ProductNumber`, `OrderQty`, `UnitPrice`, and `LineTotal`. The system will look up the rest.

            Here are the database models for context:
            {MODELS_SCHEMA}

            Return ONLY the JSON object.
            """
            
            response = model.generate_content([prompt, img])
            img.close()
            os.remove(filepath)

            extracted_data = extract_json_from_response(response.text)
            
            if not extracted_data:
                return jsonify({'error': 'Failed to extract data from document.'}), 500

            # --- Process and Save to Database ---
            header_data = extracted_data.get('SalesOrderHeader')
            details_data = extracted_data.get('SalesOrderDetail')
            customer_name_str = extracted_data.get('CustomerName')

            if not header_data or not details_data:
                return jsonify({'error': 'Extracted data is missing required sections.'}), 500
            # -- I have put this here because I cannot create multiple invoices just to test so random assignment
            if os.getenv('TESTING', 'false').lower() == 'true':
                # Find the highest existing sales order number to generate a new one.
                last_order_num_str = db.session.query(db.func.max(db.func.substr(models.SalesOrderHeader.SalesOrderNumber, 3))).filter(models.SalesOrderHeader.SalesOrderNumber.like('SO%')).scalar()
                
                last_known_max = 75123
                last_order_num = 0
                if last_order_num_str:
                    try:
                        last_order_num = int(last_order_num_str)
                    except (ValueError, TypeError):
                        pass # Keep it at 0 if conversion fails

                # Use the greater of the DB max or the known last number from previous data
                new_number = max(last_known_max, last_order_num) + 1
                new_sales_order_number = f"SO{new_number}"
                
                print(f"TESTING MODE: Overriding SalesOrderNumber with {new_sales_order_number}")
                header_data['SalesOrderNumber'] = new_sales_order_number

            # Explicitly remove any SalesOrderID from LLM to ensure DB generates a new one.
            header_data.pop('SalesOrderID', None)

            # Check if an order with this SalesOrderNumber already exists
            sales_order_number = header_data.get('SalesOrderNumber')
            if sales_order_number:
                existing_order = db.session.query(models.SalesOrderHeader).filter_by(SalesOrderNumber=sales_order_number).first()
                if existing_order:
                    return jsonify({'error': f"An order with SalesOrderNumber '{sales_order_number}' already exists."}), 409 # HTTP 409 Conflict

            # Find customer
            if customer_name_str:
                parts = customer_name_str.split()
                first_name, last_name = (parts[0], parts[-1]) if len(parts) > 1 else (parts[0], "")
                customer_info = db.session.query(models.IndividualCustomer).filter_by(FirstName=first_name, LastName=last_name).first()
                if customer_info:
                    customer_record = db.session.query(models.Customer).filter_by(PersonID=customer_info.BusinessEntityID).first()
                    if customer_record:
                        header_data['CustomerID'] = customer_record.CustomerID

            # Convert date strings
            for field in ['OrderDate', 'DueDate', 'ShipDate']:
                if header_data.get(field) and isinstance(header_data[field], str):
                    try:
                        header_data[field] = datetime.strptime(header_data[field], '%Y-%m-%d')
                    except ValueError:
                        header_data[field] = None
            
            new_header = models.SalesOrderHeader(**header_data)
            db.session.add(new_header)
            db.session.flush() # This is sufficient to get the ID on new_header

            # Update the original header dict with the new ID for the response
            header_data['SalesOrderID'] = new_header.SalesOrderID

            hydrated_details = []
            for detail_data in details_data:
                product = db.session.query(models.Product).filter_by(ProductNumber=detail_data.get('ProductNumber')).first()
                if product:
                    model_init_data = detail_data.copy()
                    model_init_data.pop('ProductNumber', None)
                    model_init_data['ProductID'] = product.ProductID
                    model_init_data['SalesOrderID'] = new_header.SalesOrderID
                    
                    new_detail = models.SalesOrderDetail(**model_init_data)
                    db.session.add(new_detail)
                    db.session.flush()

                    detail_data['SalesOrderDetailID'] = new_detail.SalesOrderDetailID
                    detail_data['SalesOrderID'] = new_header.SalesOrderID
                    detail_data['Name'] = product.Name
                    detail_data['Color'] = product.Color
                    detail_data['Size'] = product.Size
                    detail_data['ListPrice'] = product.ListPrice
                    hydrated_details.append(detail_data)

            db.session.commit()
            
            # --- Construct Detailed Response for Frontend ---
            final_response = {
                "SalesOrderHeader": header_data,
                "CustomerInfo": extracted_data.get('CustomerName'),
                "BillingAddress": extracted_data.get('BillingAddress'),
                "ShippingAddress": extracted_data.get('ShippingAddress'),
                "SalesOrderDetail": hydrated_details,
            }

            return jsonify({
                "status": "success", 
                "message": "Data saved to database.", 
                "data": final_response
            })

        except Exception as e:
            db.session.rollback()
            if 'img' in locals() and img:
                img.close()
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': f'An error occurred: {str(e)}'}), 500
        finally:
            db.session.remove()

    return jsonify({'error': 'File processing failed'}), 500

@app.route('/api/sales_order/<int:order_id>', methods=['PUT'])
def update_sales_order(order_id):
    from . import models
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid data'}), 400

    header_data = data.get('SalesOrderHeader')
    details_data = data.get('SalesOrderDetail')

    try:
        header = db.session.get(models.SalesOrderHeader, order_id)
        if not header:
            return jsonify({'error': f'SalesOrder with ID {order_id} not found.'}), 404

        # Update Header
        for key, value in header_data.items():
            if hasattr(header, key):
                if key in ['OrderDate', 'DueDate', 'ShipDate']:
                    if isinstance(value, str):
                        try:
                            parsed_date = datetime.strptime(value, '%a, %d %b %Y %H:%M:%S %Z')
                            setattr(header, key, parsed_date)
                        except (ValueError, TypeError):
                            # If that fails, try a standard ISO format (YYYY-MM-DD)
                            try:
                                parsed_date = datetime.strptime(value.split('T')[0], '%Y-%m-%d')
                                setattr(header, key, parsed_date)
                            except (ValueError, TypeError):
                                if key == 'OrderDate': # OrderDate is not nullable
                                    return jsonify({'error': f"Invalid date format for '{key}'. Please use YYYY-MM-DD."}), 400
                                setattr(header, key, None)
                    else:
                        setattr(header, key, value)
                else:
                    setattr(header, key, value)

        # Replace Details
        db.session.query(models.SalesOrderDetail).filter_by(SalesOrderID=order_id).delete()
        for detail in details_data:
            product_number = detail.get('ProductNumber')

            detail.pop('Name', None)
            detail.pop('Color', None)
            detail.pop('Size', None)
            detail.pop('ListPrice', None)
            detail.pop('ProductNumber', None)

            # Re-fetch the ProductID using the ProductNumber, as it's not submitted directly
            if product_number:
                product = db.session.query(models.Product).filter_by(ProductNumber=product_number).first()
                if product:
                    detail['ProductID'] = product.ProductID
                else:
                    # If we can't find the product, we can't create the detail record.
                    continue
            else:
                continue

            new_detail = models.SalesOrderDetail(**detail)
            db.session.add(new_detail)

        db.session.commit()
        return jsonify({"status": "success", "message": f"Order {order_id} updated."})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
    finally:
        db.session.close()


@app.route('/api/sales_order/<int:order_id>', methods=['DELETE'])
def delete_sales_order(order_id):
    from . import models
    try:
        # First delete the details, then the header
        db.session.query(models.SalesOrderDetail).filter_by(SalesOrderID=order_id).delete()
        db.session.query(models.SalesOrderHeader).filter_by(SalesOrderID=order_id).delete()
        db.session.commit()
        return jsonify({"status": "success", "message": f"Order {order_id} deleted."})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
    finally:
        db.session.close()

if __name__ == '__main__':
    app.run(debug=True)
