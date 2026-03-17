-- Products that have never been sold: List all products that have never been included in any order

-- SQLAI
SELECT
  p.product_id,
  p.product_name,
  p.description,
  p.price,
  p.stock_quantity,
  p.category_id,
  p.supplier_id
FROM products p
WHERE NOT EXISTS (
  SELECT 1
  FROM order_details od
  WHERE od.product_id = p.product_id
);

-- Text2SQL
SELECT 
    p.product_id,
    p.product_name,
    p.price,
    p.stock_quantity,
    p.description
FROM 
    products p
LEFT JOIN 
    order_details od ON p.product_id = od.product_id
WHERE 
    od.product_id IS NULL
ORDER BY 
    p.product_name;

-- Chat2DB
SELECT p.product_id, p.product_name, p.category_id, p.supplier_id, p.price, p.stock_quantity, p.description
FROM products p
LEFT JOIN order_details od ON p.product_id = od.product_id
WHERE od.order_detail_id IS NULL;

-- AI2sql
SELECT p.*
FROM products p
LEFT JOIN order_details od ON p.product_id = od.product_id
WHERE od.product_id IS NULL;

-- Sequel
SELECT c.`customer_id`, c.`first_name`, c.`last_name`, c.`email`, COALESCE(SUM(o.`total_amount`), 0) AS `total_spending`, (SELECT AVG(customer_total) 
FROM (
	SELECT SUM(o2.`total_amount`) AS customer_total 
	FROM supermarket.orders o2 
	GROUP BY o2.`customer_id`) AS avg_calc
) AS `average_spending` 
FROM supermarket.customers c 
LEFT JOIN supermarket.orders o ON c.`customer_id` = o.`customer_id` 
GROUP BY c.`customer_id`, c.`first_name`, c.`last_name`, c.`email` 
HAVING COALESCE(SUM(o.`total_amount`), 0) > (SELECT AVG(customer_total) 
FROM (
	SELECT SUM(o2.`total_amount`) AS customer_total 
	FROM supermarket.orders o2 
	GROUP BY o2.`customer_id`) AS avg_calc
	) 
ORDER BY `total_spending` DESC;

-- Vanna
NULL;

-- AskYourDatabase
SELECT 
    p.product_id,
    p.product_name,
    p.price,
    p.stock_quantity,
    p.description,
    c.category_name,
    s.supplier_name
FROM products p
LEFT JOIN categories c ON p.category_id = c.category_id
LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
WHERE p.product_id NOT IN (
    SELECT DISTINCT product_id 
    FROM order_details
)
ORDER BY p.product_id;