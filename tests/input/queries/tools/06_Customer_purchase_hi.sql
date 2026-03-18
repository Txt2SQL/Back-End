-- Customer purchase history with details. Show complete purchase history for each customer including: Customer name, order date, number of product, quantities, and total spent per order

-- SQLAI
SELECT
  c.customer_id,
  CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
  o.order_id,
  o.order_date,
  COUNT(DISTINCT od.product_id) AS num_distinct_products,
  COALESCE(SUM(od.quantity), 0) AS total_quantity,
  COALESCE(MAX(o.total_amount), SUM(od.quantity * od.unit_price)) AS total_spent
FROM customers c
JOIN orders o ON o.customer_id = c.customer_id
LEFT JOIN order_details od ON od.order_id = o.order_id
GROUP BY
  c.customer_id, c.first_name, c.last_name, o.order_id, o.order_date;

-- Text2SQL
SELECT
    c.customer_id,
    CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
    o.order_id,
    o.order_date,
    COUNT(od.product_id) AS number_of_products,
    SUM(od.quantity) AS total_quantity,
    o.total_amount AS total_spent
FROM
    customers c
JOIN
    orders o ON c.customer_id = o.customer_id
JOIN
    order_details od ON o.order_id = od.order_id
GROUP BY
    c.customer_id,
    c.first_name,
    c.last_name,
    o.order_id,
    o.order_date,
    o.total_amount
ORDER BY
    c.customer_id,
    o.order_date DESC;

-- Chat2DB
SELECT 
    c.customer_id,
    CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
    o.order_date,
    COUNT(od.product_id) AS number_of_products,
    SUM(od.quantity) AS total_quantity,
    SUM(od.quantity * od.unit_price) AS total_spent_per_order
FROM 
    customers c
JOIN 
    orders o ON c.customer_id = o.customer_id
JOIN 
    order_details od ON o.order_id = od.order_id
GROUP BY 
    c.customer_id, c.first_name, c.last_name, o.order_date, o.order_id
ORDER BY 
    c.customer_id, o.order_date;

-- AI2sql
SELECT 
    c.customer_id,
    c.customer_name,
    o.order_id,
    o.order_date,
    COUNT(oi.product_id) AS number_of_products,
    SUM(oi.quantity) AS total_quantity,
    SUM(oi.quantity * oi.unit_price) AS total_spent_per_order
FROM 
    customers c
JOIN 
    orders o ON c.customer_id = o.customer_id
JOIN 
    order_items oi ON o.order_id = oi.order_id
GROUP BY 
    c.customer_id, c.customer_name, o.order_id, o.order_date
ORDER BY 
    c.customer_name, o.order_date;

-- Sequel
SELECT 
	CONCAT(c.`first_name`, ' ', c.`last_name`) AS `customer_name`, 
	o.`order_date`, 
	COUNT(DISTINCT od.`product_id`) AS `number_of_products`, 
	SUM(od.`quantity`) AS `total_quantity`, 
	ROUND(o.`total_amount`, 2) AS `total_spent` 
FROM supermarket.`customers` c 
JOIN supermarket.`orders` o ON c.`customer_id` = o.`customer_id` 
JOIN supermarket.`order_details` od ON o.`order_id` = od.`order_id` 
GROUP BY c.`customer_id`, c.`first_name`, c.`last_name`, o.`order_id`, o.`order_date`, o.`total_amount` 
ORDER BY c.`last_name`, c.`first_name`, o.`order_date` DESC;

-- Vanna
SELECT 
	c.customer_id, 
	c.first_name, 
	c.last_name, 
	o.order_id, 
	o.order_date, 
	COUNT(od.order_detail_id) as number_of_products, 
	SUM(od.quantity) as total_quantity, 
	ROUND(SUM(od.quantity * od.unit_price), 2) as total_spent_per_order 
FROM customers c 
INNER JOIN orders o ON c.customer_id = o.customer_id 
INNER JOIN order_details od ON o.order_id = od.order_id 
GROUP BY c.customer_id, c.first_name, c.last_name, o.order_id, o.order_date 
ORDER BY c.customer_id, o.order_date DESC;

-- AskYourDatabase
SELECT 
    c.customer_id,
    c.first_name,
    c.last_name,
    o.order_id,
    o.order_date,
    COUNT(od.product_id) as number_of_products,
    SUM(od.quantity) as total_quantities,
    o.total_amount
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_details od ON o.order_id = od.order_id
GROUP BY c.customer_id, c.first_name, c.last_name, o.order_id, o.order_date, o.total_amount
ORDER BY c.customer_id, o.order_date DESC;

-- MyQuery
SELECT 
    CONCAT(C.FIRST_NAME, ' ', C.LAST_NAME) AS customer_name,
    C.EMAIL,
    O.ORDER_ID,
    DATE_FORMAT(O.ORDER_DATE, '%Y-%m-%d') AS order_date,
    O.STATUS AS order_status,
    COUNT(DISTINCT OD.PRODUCT_ID) AS number_of_products,
    SUM(OD.QUANTITY) AS total_items,
    FORMAT(SUM(OD.QUANTITY * OD.UNIT_PRICE), 2) AS calculated_order_total,
    FORMAT(O.TOTAL_AMOUNT, 2) AS recorded_order_total
FROM CUSTOMERS C
JOIN ORDERS O ON C.CUSTOMER_ID = O.CUSTOMER_ID
JOIN ORDER_DETAILS OD ON O.ORDER_ID = OD.ORDER_ID
GROUP BY 
    C.CUSTOMER_ID,
    C.FIRST_NAME,
    C.LAST_NAME,
    C.EMAIL,
    O.ORDER_ID,
    O.ORDER_DATE,
    O.STATUS,
    O.TOTAL_AMOUNT
HAVING ABS(SUM(OD.QUANTITY * OD.UNIT_PRICE) - O.TOTAL_AMOUNT) < 0.01
ORDER BY 
    C.LAST_NAME, 
    C.FIRST_NAME, 
    O.ORDER_DATE DESC;