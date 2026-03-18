-- mployees who processed more orders than average. Find employees who have processed more orders than the average number of orders per employee

-- SQLAI
WITH emp_orders AS (
  SELECT
    e.employee_id,
    e.first_name,
    e.last_name,
    COUNT(o.order_id) AS order_count
  FROM employees e
  LEFT JOIN orders o ON o.employee_id = e.employee_id
  GROUP BY e.employee_id, e.first_name, e.last_name
)
SELECT employee_id, first_name, last_name, order_count
FROM emp_orders
WHERE order_count > (SELECT AVG(order_count) FROM emp_orders)
ORDER BY order_count DESC;

-- Text2SQL
SELECT 
    e.employee_id,
    CONCAT(e.first_name, ' ', e.last_name) AS full_name,
    e.position,
    COUNT(o.order_id) AS orders_processed
FROM 
    employees e
JOIN 
    orders o ON e.employee_id = o.employee_id
GROUP BY 
    e.employee_id, e.first_name, e.last_name, e.position
HAVING 
    COUNT(o.order_id) > (
        SELECT AVG(order_count)
        FROM (
            SELECT COUNT(order_id) AS order_count
            FROM orders
            GROUP BY employee_id
        ) AS employee_orders
    )
ORDER BY 
    orders_processed DESC;

-- Chat2DB
SELECT e.employee_id, e.first_name, e.last_name, COUNT(o.order_id) AS num_orders
FROM employees e
LEFT JOIN orders o ON e.employee_id = o.employee_id
GROUP BY e.employee_id, e.first_name, e.last_name
HAVING num_orders > (
    SELECT AVG(num_orders) 
    FROM (
        SELECT COUNT(order_id) AS num_orders 
        FROM orders GROUP BY employee_id
    ) AS avg_orders
);

-- AI2sql
SELECT e.employee_id, e.first_name, e.last_name, COUNT(o.order_id) AS orders_processed
FROM employees e
JOIN orders o ON e.employee_id = o.employee_id
GROUP BY e.employee_id, e.first_name, e.last_name
HAVING COUNT(o.order_id) > (
    SELECT AVG(order_count) 
    FROM (
        SELECT COUNT(*) AS order_count
        FROM orders
        GROUP BY employee_id
    ) AS order_counts
);

-- Sequel
SELECT 
	e.`employee_id`, 
	e.`first_name`, 
	e.`last_name`, 
	e.`position`, 
	e.`email`, 
	COUNT(o.`order_id`) AS `orders_processed`, 
	(
		SELECT AVG(order_count) 
		FROM (
			SELECT COUNT(o2.`order_id`) AS order_count 
			FROM supermarket.orders o2 
			GROUP BY o2.`employee_id`
		) AS avg_calc
	) AS `average_orders` 
FROM supermarket.employees e 
LEFT JOIN supermarket.orders o ON e.`employee_id` = o.`employee_id` 
GROUP BY e.`employee_id`, e.`first_name`, e.`last_name`, e.`position`, e.`email` 
HAVING COUNT(o.`order_id`) > (
	SELECT AVG(order_count) 
	FROM (
		SELECT COUNT(o2.`order_id`) AS order_count 
		FROM supermarket.orders o2 
		GROUP BY o2.`employee_id`
	) AS avg_calc
) ORDER BY `orders_processed` DESC;

-- Vanna
SELECT 
    e.employee_id, 
    e.first_name, 
    e.last_name, 
    COUNT(o.order_id) as orders_processed 
FROM employees e 
INNER JOIN orders o ON e.employee_id = o.employee_id 
GROUP BY e.employee_id, e.first_name, e.last_name 
HAVING COUNT(o.order_id) > (
    SELECT AVG(order_count) 
    FROM (
        SELECT COUNT(order_id) as order_count 
        FROM orders 
        GROUP BY employee_id 
    ) subquery 
) ORDER BY orders_processed DESC;

-- AskYourDatabase
SELECT 
    e.employee_id,
    e.first_name,
    e.last_name,
    e.email,
    e.position,
    COUNT(o.order_id) as orders_processed
FROM employees e
JOIN orders o ON e.employee_id = o.employee_id
GROUP BY e.employee_id, e.first_name, e.last_name, e.email, e.position
HAVING COUNT(o.order_id) > (
    SELECT AVG(order_count)
    FROM (
        SELECT COUNT(order_id) as order_count
        FROM orders
        GROUP BY employee_id
    ) as employee_order_counts
)
ORDER BY orders_processed DESC

-- MyQuery

SELECT E.EMPLOYEE_ID, E.FIRST_NAME, E.LAST_NAME
FROM EMPLOYEES E
JOIN ORDERS O ON E.EMPLOYEE_ID = O.EMPLOYEE_ID
GROUP BY E.EMPLOYEE_ID
HAVING COUNT(O.ORDER_ID) > (
    SELECT AVG(TOTAL_ORDERS)
    FROM (
        SELECT COUNT(ORDER_ID) AS TOTAL_ORDERS
        FROM ORDERS
        GROUP BY EMPLOYEE_ID
    ) AS OE
);