-- Customers who spent more than average. Find customers whose total spending is above the average customer spending

-- SQLAI
SELECT customer_id, first_name, last_name, total_spent, avg_spent
FROM (
  SELECT
    t.customer_id,
    t.first_name,
    t.last_name,
    t.total_spent,
    AVG(t.total_spent) OVER () AS avg_spent
  FROM (
    SELECT
      c.customer_id,
      c.first_name,
      c.last_name,
      COALESCE(SUM(o.total_amount), 0) AS total_spent
    FROM customers c
    LEFT JOIN orders o ON c.customer_id = o.customer_id
    GROUP BY c.customer_id, c.first_name, c.last_name
  ) AS t
) AS final
WHERE total_spent > avg_spent
ORDER BY total_spent DESC;

-- Text2SQL
SELECT 
    c.customer_id,
    CONCAT(c.first_name, ' ', c.last_name) AS full_name,
    c.email,
    SUM(o.total_amount) AS total_spent
FROM 
    customers c
JOIN 
    orders o ON c.customer_id = o.customer_id
GROUP BY 
    c.customer_id, c.first_name, c.last_name, c.email
HAVING 
    SUM(o.total_amount) > (
        SELECT AVG(customer_total)
        FROM (
            SELECT SUM(total_amount) AS customer_total
            FROM orders
            GROUP BY customer_id
        ) AS customer_totals
    )
ORDER BY 
    total_spent DESC;

-- AI2sql
SELECT
    c.customer_id,
    c.name,
    SUM(o.total_amount) AS total_spent
FROM
    customers c
JOIN
    orders o ON c.customer_id = o.customer_id
GROUP BY
    c.customer_id,
    c.name
HAVING
    SUM(o.total_amount) > (
        SELECT AVG(customer_total)
        FROM (
            SELECT SUM(total_amount) AS customer_total
            FROM orders
            GROUP BY customer_id
        ) AS sub
    );

-- Sequel
SELECT 
	c.`customer_id`, 
	c.`first_name`, 
	c.`last_name`, 
	c.`email`, 
	COALESCE(SUM(o.`total_amount`), 0) AS `total_spending`, 
	(
		SELECT AVG(customer_total) 
		FROM (
			SELECT SUM(o2.`total_amount`) AS customer_total 
			FROM supermarket.orders o2 
			GROUP BY o2.`customer_id`
		) AS avg_calc
	) AS `average_spending` 
FROM supermarket.customers c 
LEFT JOIN supermarket.orders o ON c.`customer_id` = o.`customer_id` 
GROUP BY c.`customer_id`, c.`first_name`, c.`last_name`, c.`email` 
HAVING COALESCE(SUM(o.`total_amount`), 0) > (
	SELECT AVG(customer_total) 
	FROM (
		SELECT SUM(o2.`total_amount`) AS customer_total 
		FROM supermarket.orders o2 
		GROUP BY o2.`customer_id`
	) AS avg_calc
) 
ORDER BY `total_spending` DESC;

-- Vanna
SELECT c.customer_id, c.first_name, c.last_name, SUM(o.total_amount) as total_spending 
FROM customers c 
INNER JOIN orders o ON c.customer_id = o.customer_id 
GROUP BY c.customer_id, c.first_name, c.last_name 
HAVING SUM(o.total_amount) > (
  SELECT AVG(customer_total) 
  FROM ( 
    SELECT SUM(total_amount) as customer_total 
    FROM orders GROUP BY customer_id 
  ) subquery 
) 
ORDER BY total_spending DESC;

-- AskYourDatabase
SELECT 
    c.customer_id,
    c.first_name,
    c.last_name,
    c.email,
    SUM(o.total_amount) as total_spending
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.first_name, c.last_name, c.email
HAVING SUM(o.total_amount) > (
    SELECT AVG(customer_total)
    FROM (
        SELECT SUM(total_amount) as customer_total
        FROM orders
        GROUP BY customer_id
    ) as customer_totals
)
ORDER BY total_spending DESC;

-- MyQuery
SELECT C.CUSTOMER_ID, C.FIRST_NAME, C.LAST_NAME, SUM(O.TOTAL_AMOUNT) AS TOTAL_SPENDING
FROM CUSTOMERS C
JOIN ORDERS O ON C.CUSTOMER_ID = O.CUSTOMER_ID
GROUP BY C.CUSTOMER_ID
HAVING SUM(O.TOTAL_AMOUNT) > (
    SELECT AVG(TOTAL_SPENDING)
        FROM (
            SELECT SUM(TOTAL_AMOUNT) TOTAL_SPENDING
            FROM ORDERS
            GROUP BY CUSTOMER_ID
        ) AS CS
);