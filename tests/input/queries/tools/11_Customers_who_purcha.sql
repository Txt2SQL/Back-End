-- Customers who purchased from all product categories. Find customers who have bought at least one product from EVERY category available in the supermarket. Use correlated subqueries and count distinct categories

-- SQLAI
SELECT c.customer_id, c.first_name, c.last_name, c.email
FROM customers c
WHERE (
    SELECT COUNT(DISTINCT p.category_id)
    FROM orders o
    JOIN order_details od ON o.order_id = od.order_id
    JOIN products p ON od.product_id = p.product_id
    WHERE o.customer_id = c.customer_id
) = (SELECT COUNT(*) FROM categories);

-- Text2SQL
SELECT
    c.customer_id,
    CONCAT(c.first_name, ' ', c.last_name) AS customer_name
FROM
    customers c
WHERE
    (
        SELECT COUNT(DISTINCT p.category_id)
        FROM
            orders o
            JOIN order_details od ON o.order_id = od.order_id
            JOIN products p ON od.product_id = p.product_id
        WHERE
            o.customer_id = c.customer_id
    ) = (
        SELECT COUNT(*) FROM categories
    );

-- Chat2DB
SELECT 
    c.customer_id,
    c.first_name,
    c.last_name
FROM 
    customers c
WHERE 
    NOT EXISTS (
        SELECT 
            cat.category_id
        FROM 
            categories cat
        WHERE 
            NOT EXISTS (
                SELECT 
                    1
                FROM 
                    orders o
                JOIN 
                    order_details od ON o.order_id = od.order_id
                JOIN 
                    products p ON od.product_id = p.product_id
                WHERE 
                    o.customer_id = c.customer_id
                    AND p.category_id = cat.category_id
            )
    );

-- AI2sql
SELECT c.customer_id, c.customer_name
FROM customers c
WHERE (
    SELECT COUNT(DISTINCT pc.category_id)
    FROM products p
    JOIN product_categories pc ON p.product_id = pc.product_id
    JOIN orders o ON o.product_id = p.product_id
    WHERE o.customer_id = c.customer_id
) = (
    SELECT COUNT(DISTINCT category_id)
    FROM product_categories
);

-- Sequel
SELECT 
	c.`customer_id`, 
	c.`first_name`, 
	c.`last_name`, 
	c.`email`, 
	COUNT(DISTINCT p.`category_id`) as `categories_purchased`, 
	(
		SELECT COUNT(DISTINCT `category_id`) 
		FROM supermarket.categories
	) as `total_categories` 
FROM supermarket.customers c 
INNER JOIN supermarket.orders o ON c.`customer_id` = o.`customer_id` 
INNER JOIN supermarket.order_details od ON o.`order_id` = od.`order_id` 
INNER JOIN supermarket.products p ON od.`product_id` = p.`product_id` 
WHERE NOT EXISTS (
	SELECT 1 
	FROM supermarket.categories cat 
	WHERE NOT EXISTS (
		SELECT 1 
		FROM supermarket.orders o2 
		INNER JOIN supermarket.order_details od2 ON o2.`order_id` = od2.`order_id` 
		INNER JOIN supermarket.products p2 ON od2.`product_id` = p2.`product_id` 
		WHERE o2.`customer_id` = c.`customer_id` AND p2.`category_id` = cat.`category_id`
	)
) 
GROUP BY c.`customer_id`, c.`first_name`, c.`last_name`, c.`email` 
HAVING COUNT(DISTINCT p.`category_id`) = (
	SELECT COUNT(DISTINCT `category_id`) 
	FROM supermarket.categories
) 
ORDER BY c.`customer_id`;

-- Vanna
SELECT 
	c.customer_id, 
	c.first_name, 
	c.last_name, 
	( 
		SELECT COUNT(DISTINCT p.category_id) 
		FROM orders o 
		INNER JOIN order_details od ON o.order_id = od.order_id 
		INNER JOIN products p ON od.product_id = p.product_id 
		WHERE o.customer_id = c.customer_id 
	) as distinct_categories_purchased, 
	( 
		SELECT COUNT(DISTINCT category_id) 
		FROM categories 
	) as total_categories_available, 
	ROUND( ( 
			SELECT COUNT(DISTINCT p.category_id) 
			FROM orders o 
			INNER JOIN order_details od ON o.order_id = od.order_id 
			INNER JOIN products p ON od.product_id = p.product_id 
			WHERE o.customer_id = c.customer_id 
		) * 100.0 / ( 
			SELECT COUNT(DISTINCT category_id) 
			FROM categories 
		), 2 
	) as percentage_of_all_categories 
FROM customers c 
INNER JOIN orders o ON c.customer_id = o.customer_id 
GROUP BY c.customer_id, c.first_name, c.last_name 
ORDER BY distinct_categories_purchased DESC;

-- AskYourDatabase
SELECT 
    c.customer_id,
    c.first_name,
    c.last_name,
    c.email,
    (
        SELECT COUNT(DISTINCT p2.category_id)
        FROM orders o2
        JOIN order_details od2 ON o2.order_id = od2.order_id
        JOIN products p2 ON od2.product_id = p2.product_id
        WHERE o2.customer_id = c.customer_id
    ) as categories_purchased,
    (
        SELECT COUNT(DISTINCT category_id)
        FROM categories
    ) as total_categories
FROM customers c
WHERE (
    SELECT COUNT(DISTINCT p2.category_id)
    FROM orders o2
    JOIN order_details od2 ON o2.order_id = od2.order_id
    JOIN products p2 ON od2.product_id = p2.product_id
    WHERE o2.customer_id = c.customer_id
) = (
    SELECT COUNT(DISTINCT category_id)
    FROM categories
)
ORDER BY c.customer_id;

-- MyQuery
SELECT DISTINCT 
    C.CUSTOMER_ID, 
    CONCAT(C.FIRST_NAME,' ',C.LAST_NAME) AS customer_name
FROM CUSTOMERS C
WHERE (
    SELECT COUNT(DISTINCT P.CATEGORY_ID)
    FROM ORDERS O
    JOIN ORDER_DETAILS OD ON O.ORDER_ID=OD.ORDER_ID
    JOIN PRODUCTS P ON OD.PRODUCT_ID=P.PRODUCT_ID
    WHERE O.CUSTOMER_ID=C.CUSTOMER_ID
) = (SELECT COUNT(*) FROM CATEGORIES);