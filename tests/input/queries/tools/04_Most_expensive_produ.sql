-- Most expensive product in each category. For each category, show the most expensive product and its price

-- SQLAI
SELECT
  c.category_id,
  c.category_name,
  p.product_id,
  p.product_name,
  p.price
FROM categories c
JOIN (
  SELECT category_id, MAX(price) AS max_price
  FROM products
  GROUP BY category_id
) m ON m.category_id = c.category_id
JOIN products p ON p.category_id = m.category_id AND p.price = m.max_price
ORDER BY c.category_name, p.product_name;

-- Text2SQL
SELECT 
    c.category_id,
    c.category_name,
    p.product_id,
    p.product_name,
    p.price
FROM 
    categories c
JOIN 
    products p ON c.category_id = p.category_id
WHERE 
    p.price = (
        SELECT MAX(p2.price)
        FROM products p2
        WHERE p2.category_id = c.category_id
    )
ORDER BY 
    c.category_name, p.product_name;

-- Chat2DB
SELECT p.product_id, p.product_name, p.category_id, p.price, c.category_name
FROM products p
JOIN categories c ON p.category_id = c.category_id
JOIN (
    SELECT category_id, MAX(price) AS max_price
    FROM products
    GROUP BY category_id
) max_prices ON p.category_id = max_prices.category_id AND p.price = max_prices.max_price;


-- AI2sql
SELECT 
    c.category_name,
    p.product_name,
    p.price
FROM
    products p
INNER JOIN
    categories c ON p.category_id = c.category_id
WHERE
    (p.category_id, p.price) IN (
        SELECT 
            category_id, MAX(price)
        FROM 
            products
        GROUP BY 
            category_id
    );

-- Sequel
SELECT 
	c.`category_name` AS Category, 
	p.`product_name` AS Product Name, 
	CONCAT('$', FORMAT(p.`price`, 2)) AS `Price` 
FROM supermarket.products p 
INNER JOIN supermarket.categories c ON p.`category_id` = c.`category_id` 
WHERE p.`price` = (
	SELECT MAX(p2.`price`) 
	FROM supermarket.products p2 
	WHERE p2.`category_id` = p.`category_id`
) 
ORDER BY p.`price` DESC;

-- Vanna
SELECT c.category_id, c.category_name, p.product_id, p.product_name, p.price 
FROM ( 
	SELECT 
		p.product_id, 
		p.product_name, 
		p.price, 
		p.category_id, 
		ROW_NUMBER() OVER (PARTITION BY p.category_id ORDER BY p.price DESC) as rn 
	FROM products p 
) p 
INNER JOIN categories c ON p.category_id = c.category_id 
WHERE p.rn = 1 
ORDER BY c.category_name;

-- AskYourDatabase
SELECT 
    c.category_name,
    p.product_name,
    p.price,
    p.product_id
FROM products p
JOIN categories c ON p.category_id = c.category_id
WHERE (p.category_id, p.price) IN (
    SELECT category_id, MAX(price)
    FROM products
    GROUP BY category_id
)
ORDER BY p.price DESC;