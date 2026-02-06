-- Create Customers table
CREATE TABLE Customers (
    customer_id INT AUTO_INCREMENT,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20),
    address VARCHAR(200),
    registration_date DATE,
    PRIMARY KEY(customer_id)
);

ALTER TABLE Customers ADD UNIQUE idx_customers_email (email);
ALTER TABLE Customers ADD INDEX idx_customers_name (last_name, first_name);

CREATE TABLE Categories (
    category_id INT AUTO_INCREMENT,
    category_name VARCHAR(100) NOT NULL,
    description TEXT,
    PRIMARY KEY(category_id)
);

ALTER TABLE Categories ADD UNIQUE idx_categories_name (category_name);

CREATE TABLE Suppliers (
    supplier_id INT AUTO_INCREMENT,
    supplier_name VARCHAR(100) NOT NULL,
    contact_person VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100),
    address VARCHAR(200),
    PRIMARY KEY(supplier_id)
);

ALTER TABLE Suppliers ADD UNIQUE idx_suppliers_email (email);
ALTER TABLE Suppliers ADD INDEX idx_suppliers_name (supplier_name);

CREATE TABLE Products (
    product_id INT AUTO_INCREMENT,
    product_name VARCHAR(100) NOT NULL,
    category_id INT,
    supplier_id INT,
    price DECIMAL(10,2) NOT NULL,
    stock_quantity INT NOT NULL,
    description TEXT,
    PRIMARY KEY(product_id)
);

ALTER TABLE Products ADD INDEX idx_products_name (product_name);
ALTER TABLE Products ADD INDEX idx_products_price (price);

CREATE TABLE Employees (
    employee_id INT AUTO_INCREMENT,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    position VARCHAR(50),
    email VARCHAR(100),
    phone VARCHAR(20),
    hire_date DATE,
    salary DECIMAL(10,2),
    PRIMARY KEY(employee_id)
);

ALTER TABLE Employees ADD UNIQUE idx_employees_email (email);
ALTER TABLE Employees ADD INDEX idx_employees_name (last_name, first_name);
ALTER TABLE Employees ADD INDEX idx_employees_position (position);

CREATE TABLE Orders (
    order_id INT AUTO_INCREMENT,
    customer_id INT,
    employee_id INT,
    order_date DATE NOT NULL,
    total_amount DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'Pending',
    PRIMARY KEY(order_id)
);

ALTER TABLE Orders ADD INDEX idx_orders_date (order_date);
ALTER TABLE Orders ADD INDEX idx_orders_status (status);
ALTER TABLE Orders ADD INDEX idx_orders_customer (customer_id);

CREATE TABLE Order_Details (
    order_detail_id INT AUTO_INCREMENT,
    order_id INT,
    product_id INT,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    PRIMARY KEY(order_detail_id)
);

ALTER TABLE Order_Details ADD INDEX idx_order_details_order (order_id);
ALTER TABLE Order_Details ADD INDEX idx_order_details_product (product_id);

CREATE TABLE Inventory (
    inventory_id INT AUTO_INCREMENT,
    product_id INT,
    quantity_change INT NOT NULL,
    change_date DATE NOT NULL,
    change_type VARCHAR(20),
    PRIMARY KEY(inventory_id)
);

ALTER TABLE Inventory ADD INDEX idx_inventory_product (product_id);
ALTER TABLE Inventory ADD INDEX idx_inventory_date (change_date);

CREATE TABLE Shipments (
    shipment_id INT AUTO_INCREMENT,
    order_id INT,
    shipment_date DATE NOT NULL,
    carrier VARCHAR(100),
    tracking_number VARCHAR(100),
    status VARCHAR(50) DEFAULT 'Processing',
    estimated_delivery DATE,
    actual_delivery DATE,
    shipping_cost DECIMAL(10,2),
    PRIMARY KEY(shipment_id)
);

ALTER TABLE Shipments ADD UNIQUE idx_shipments_tracking (tracking_number);
ALTER TABLE Shipments ADD INDEX idx_shipments_order (order_id);
ALTER TABLE Shipments ADD INDEX idx_shipments_status (status);
ALTER TABLE Shipments ADD INDEX idx_shipments_dates (shipment_date, estimated_delivery);

CREATE TABLE Reviews (
    review_id INT AUTO_INCREMENT,
    customer_id INT,
    product_id INT,
    order_id INT,
    rating INT CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    review_date DATE NOT NULL,
    helpful_count INT DEFAULT 0,
    PRIMARY KEY(review_id)
);

ALTER TABLE Reviews ADD UNIQUE idx_reviews_unique (customer_id, product_id, order_id);
ALTER TABLE Reviews ADD INDEX idx_reviews_product (product_id);
ALTER TABLE Reviews ADD INDEX idx_reviews_rating (rating);
ALTER TABLE Reviews ADD INDEX idx_reviews_date (review_date);

ALTER TABLE Products ADD CONSTRAINT fk_products_category FOREIGN KEY (category_id) REFERENCES Categories(category_id);
ALTER TABLE Products ADD CONSTRAINT fk_products_supplier FOREIGN KEY (supplier_id) REFERENCES Suppliers(supplier_id);
ALTER TABLE Orders ADD CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id) REFERENCES Customers(customer_id);
ALTER TABLE Orders ADD CONSTRAINT fk_orders_employee FOREIGN KEY (employee_id) REFERENCES Employees(employee_id);
ALTER TABLE Order_Details ADD CONSTRAINT fk_order_details_order FOREIGN KEY (order_id) REFERENCES Orders(order_id);
ALTER TABLE Order_Details ADD CONSTRAINT fk_order_details_product FOREIGN KEY (product_id) REFERENCES Products(product_id);
ALTER TABLE Inventory ADD CONSTRAINT fk_inventory_product FOREIGN KEY (product_id) REFERENCES Products(product_id);
ALTER TABLE Shipments ADD CONSTRAINT fk_shipments_order FOREIGN KEY (order_id) REFERENCES Orders(order_id);
ALTER TABLE Reviews ADD CONSTRAINT fk_reviews_customer FOREIGN KEY (customer_id) REFERENCES Customers(customer_id);
ALTER TABLE Reviews ADD CONSTRAINT fk_reviews_product FOREIGN KEY (product_id) REFERENCES Products(product_id);
ALTER TABLE Reviews ADD CONSTRAINT fk_reviews_order FOREIGN KEY (order_id) REFERENCES Orders(order_id);