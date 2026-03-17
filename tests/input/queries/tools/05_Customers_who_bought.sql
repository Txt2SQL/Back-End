-- Customers who bought the most popular product. Find customers who purchased the product that has been sold the most times

-- SQLAI
WITH product_sales AS (
  SELECT
    od.product_id,
    SUM(od.quantity) AS total_units_sold
  FROM order_details od
  GROUP BY od.product_id
),
top_products AS (
  SELECT product_id, total_units_sold
  FROM product_sales
  WHERE total_units_sold = (SELECT MAX(total_units_sold) FROM product_sales)
)
SELECT DISTINCT
  c.customer_id,
  c.first_name,
  c.last_name,
  c.email,
  tp.product_id,
  p.product_name,
  tp.total_units_sold
FROM top_products tp
JOIN products p ON p.product_id = tp.product_id
JOIN order_details od ON od.product_id = tp.product_id
JOIN orders o ON o.order_id = od.order_id
JOIN customers c ON c.customer_id = o.customer_id
ORDER BY c.customer_id;

-- Text2SQL
SELECT 
    DISTINCT c.customer_id,
    CONCAT(c.first_name, ' ', c.last_name) AS full_name,
    c.email
FROM 
    customers c
JOIN 
    orders o ON c.customer_id = o.customer_id
JOIN 
    order_details od ON o.order_id = od.order_id
WHERE 
    od.product_id = (
        SELECT product_id
        FROM order_details
        GROUP BY product_id
        ORDER BY SUM(quantity) DESC
        LIMIT 1
    )
ORDER BY 
    full_name;

-- Chat2DB
WITH product_sales AS (
    SELECT od.product_id, COUNT(od.order_detail_id) AS sales_count
    FROM order_details od
    GROUP BY od.product_id
),
most_popular_product AS (
    SELECT product_id
    FROM product_sales
    ORDER BY sales_count DESC
    LIMIT 1
)
SELECT c.customer_id, c.first_name, c.last_name
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_details od ON o.order_id = od.order_id
JOIN most_popular_product mpp ON od.product_id = mpp.product_id;

-- AI2sql
SELECT DISTINCT c.customer_id, c.customer_name
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
WHERE oi.product_id = (
    SELECT oi2.product_id
    FROM order_items oi2
    GROUP BY oi2.product_id
    ORDER BY COUNT(*) DESC
    LIMIT 1
);

-- Sequel
SELECT 
	c.`customer_id`, 
	CONCAT(c.`first_name`, ' ', c.`last_name`) AS `customer_name`, 
	c.`email`, SUM(od.`quantity`) AS `quantity_purchased` 
FROM supermarket.customers c 
INNER JOIN supermarket.orders o ON c.`customer_id` = o.`customer_id` 
INNER JOIN supermarket.order_details od ON o.`order_id` = od.`order_id` 
WHERE od.`product_id` = 18313 
GROUP BY c.`customer_id`, c.`first_name`, c.`last_name`, c.`email` 
ORDER BY `quantity_purchased` DESC;

-- Vanna
	WITH most_popular_product AS ( 
		SELECT product_id 
		FROM order_details 
		GROUP BY product_id 
		ORDER BY COUNT(*) DESC 
		LIMIT 1 
	) 
	SELECT 
		c.customer_id, 
		c.first_name, 
		c.last_name, 
		p.product_id, 
		p.product_name, 
		COUNT(*) as times_purchased 
	FROM customers c 
	INNER JOIN orders o ON c.customer_id = o.customer_id 
	INNER JOIN order_details od ON o.order_id = od.order_id 
	INNER JOIN products p ON od.product_id = p.product_id 
	WHERE od.product_id IN (
		SELECT product_id 
		FROM most_popular_product
	) 
	GROUP BY c.customer_id, c.first_name, c.last_name, p.product_id, p.product_name 
	ORDER BY times_purchased DESC, c.last_name;

-- AskYourDatabase
SELECT 
    c.customer_id,
    c.first_name,
    c.last_name,
    c.email,
    p.product_name,
    SUM(od.quantity) as total_quantity_purchased
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_details od ON o.order_id = od.order_id
JOIN products p ON od.product_id = p.product_id
WHERE od.product_id = (
    SELECT product_id
    FROM order_details
    GROUP BY product_id
    ORDER BY SUM(quantity) DESC
    LIMIT 1
)
GROUP BY c.customer_id, c.first_name, c.last_name, c.email, p.product_name
ORDER BY total_quantity_purchased DESC;