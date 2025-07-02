from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, String
)
from sqlalchemy.orm import relationship
from .database import db

class SalesOrderHeader(db.Model):
    __tablename__ = 'SalesOrderHeader'
    SalesOrderID = Column(Integer, primary_key=True)
    RevisionNumber = Column(Integer)
    OrderDate = Column(DateTime, nullable=False)
    DueDate = Column(DateTime, nullable=False)
    ShipDate = Column(DateTime, nullable=True)
    Status = Column(Integer)
    OnlineOrderFlag = Column(Boolean)
    SalesOrderNumber = Column(String, unique=True, nullable=False)
    PurchaseOrderNumber = Column(String, nullable=True)
    AccountNumber = Column(String, nullable=True)
    CustomerID = Column(Integer, ForeignKey('Customers.CustomerID'), nullable=False)
    SalesPersonID = Column(Float, nullable=True)
    TerritoryID = Column(Integer, ForeignKey('SalesTerritory.TerritoryID'), nullable=True)
    BillToAddressID = Column(Integer, nullable=True)
    ShipToAddressID = Column(Integer, nullable=True)
    ShipMethodID = Column(Integer, nullable=True)
    CreditCardID = Column(Float, nullable=True)
    CreditCardApprovalCode = Column(String, nullable=True)
    CurrencyRateID = Column(Float, nullable=True)
    SubTotal = Column(Float, nullable=False)
    TaxAmt = Column(Float, nullable=False)
    Freight = Column(Float, nullable=False)
    TotalDue = Column(Float, nullable=False)
    details = relationship("SalesOrderDetail", backref="header")

class SalesOrderDetail(db.Model):
    __tablename__ = 'SalesOrderDetail'
    SalesOrderDetailID = Column(Integer, primary_key=True)
    SalesOrderID = Column(Integer, ForeignKey('SalesOrderHeader.SalesOrderID'), nullable=False)
    CarrierTrackingNumber = Column(String, nullable=True)
    OrderQty = Column(Integer, nullable=False)
    ProductID = Column(Integer, ForeignKey('Product.ProductID'), nullable=False)
    SpecialOfferID = Column(Integer, nullable=True)
    UnitPrice = Column(Float, nullable=False)
    UnitPriceDiscount = Column(Float, default=0.0)
    LineTotal = Column(Float, nullable=False)

class Product(db.Model):
    __tablename__ = 'Product'
    ProductID = Column(Integer, primary_key=True)
    Name = Column(String, nullable=True)
    ProductNumber = Column(String, unique=True, nullable=False)
    MakeFlag = Column(Boolean, nullable=True)
    FinishedGoodsFlag = Column(Boolean, nullable=True)
    Color = Column(String, nullable=True)
    StandardCost = Column(Float, nullable=True)
    ListPrice = Column(Float, nullable=True)
    Size = Column(String, nullable=True)
    ProductLine = Column(String, nullable=True)
    Class = Column(String, nullable=True)
    Style = Column(String, nullable=True)
    ProductSubcategoryID = Column(Integer, ForeignKey('ProductSubCategory.ProductSubcategoryID'), nullable=True)
    ProductModelID = Column(Float, nullable=True)

class Customer(db.Model):
    __tablename__ = 'Customers'
    CustomerID = Column(Integer, primary_key=True)
    PersonID = Column(Integer, unique=True, nullable=True)
    StoreID = Column(Float, nullable=True)
    TerritoryID = Column(Integer, ForeignKey('SalesTerritory.TerritoryID'), nullable=True)
    AccountNumber = Column(String, nullable=True)
    orders = relationship("SalesOrderHeader", backref="customer")

class IndividualCustomer(db.Model):
    __tablename__ = 'IndividualCustomers'
    IndividualCustomerID = Column(Integer, primary_key=True, autoincrement=True)
    BusinessEntityID = Column(Integer, nullable=False)
    FirstName = Column(String)
    MiddleName = Column(String, nullable=True)
    LastName = Column(String)
    AddressType = Column(String, nullable=True)
    AddressLine1 = Column(String, nullable=True)
    AddressLine2 = Column(String, nullable=True)
    City = Column(String, nullable=True)
    StateProvinceName = Column(String, nullable=True)
    PostalCode = Column(String, nullable=True)
    CountryRegionName = Column(String, nullable=True)

class ProductCategory(db.Model):
    __tablename__ = 'ProductCategory'
    ProductCategoryID = Column(Integer, primary_key=True)
    Name = Column(String)
    subcategories = relationship("ProductSubCategory", backref="category")

class ProductSubCategory(db.Model):
    __tablename__ = 'ProductSubCategory'
    ProductSubcategoryID = Column(Integer, primary_key=True)
    ProductCategoryID = Column(Integer, ForeignKey('ProductCategory.ProductCategoryID'))
    Name = Column(String)
    products = relationship("Product", backref="subcategory")

class SalesTerritory(db.Model):
    __tablename__ = 'SalesTerritory'
    TerritoryID = Column(Integer, primary_key=True)
    Name = Column(String)
    CountryRegionCode = Column(String)
    Group = Column(String)

class StoreCustomers(db.Model):
    __tablename__ = 'StoreCustomers'
    StoreCustomerID = Column(Integer, primary_key=True, autoincrement=True)
    BusinessEntityID = Column(Integer, nullable=False)
    Name = Column(String)
    AddressType = Column(String, nullable=True)
    AddressLine1 = Column(String, nullable=True)
    AddressLine2 = Column(String, nullable=True)
    City = Column(String, nullable=True)
    StateProvinceName = Column(String, nullable=True)
    PostalCode = Column(String, nullable=True)
    CountryRegionName = Column(String, nullable=True)