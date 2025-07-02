import pandas as pd
import os
from app.main import app
from app.database import db
from app.models import (
    Product, ProductCategory, ProductSubCategory, SalesOrderHeader, 
    SalesOrderDetail, SalesTerritory, Customer, IndividualCustomer, StoreCustomers
)
from sqlalchemy.exc import IntegrityError

def setup_database():
    """
    This function drops all existing tables, creates new ones based on the models,
    and then populates them from the Excel file.
    """
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        print("Creating all tables from models...")
        db.create_all()

        excel_path = os.path.join(os.path.dirname(__file__), 'data', 'Business Analytics - Case Study Data.xlsx')
        
        try:
            xls = pd.ExcelFile(excel_path)
            print("Excel file loaded successfully.")
        except FileNotFoundError:
            print(f"Error: The file at {excel_path} was not found.")
            return

        # Define the mapping from sheet name to model and sanitize function
        sheet_to_model = {
            'Product': Product,
            'ProductCategory': ProductCategory,
            'ProductSubCategory': ProductSubCategory,
            'SalesOrderHeader': SalesOrderHeader,
            'SalesOrderDetail': SalesOrderDetail,
            'SalesTerritory': SalesTerritory,
            'Customers': Customer,
            'IndividualCustomers': IndividualCustomer,
            'StoreCustomers': StoreCustomers
        }

        for sheet_name, model in sheet_to_model.items():
            print(f"Processing sheet: {sheet_name}")
            try:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                # Sanitize column names to match model attributes
                df.columns = df.columns.str.replace(' ', '').str.replace('[^A-Za-z0-9_]', '', regex=True)
                
                # Convert DataFrame to a list of dictionaries and insert row by row
                for record in df.to_dict(orient='records'):
                    # The keys in `record` must match the attribute names in the model `model`
                    obj = model(**record)
                    db.session.add(obj)
                
                db.session.commit()
                print(f"Successfully populated {model.__tablename__} table.")
                
            except IntegrityError as e:
                db.session.rollback()
                print(f"An integrity error occurred while processing {sheet_name}. This might be due to duplicate primary keys or other constraints. Error: {e}")
            except Exception as e:
                db.session.rollback()
                print(f"Could not process sheet {sheet_name}. Error: {e}")

    print("Database setup complete.")

if __name__ == '__main__':
    setup_database() 