-- Employee sales performance with customer details. Show each employee's sales performance including: Employee name, number of orders processed, total revenue, and their top customer

-- SQLAI
WITH per_emp_cust AS (
  SELECT
    o.employee_id,
    o.customer_id,
    SUM(o.total_amount) AS customer_revenue,
    COUNT(*) AS customer_orders
  FROM orders o
  GROUP BY o.employee_id, o.customer_id
),
ranked_top AS (
  SELECT
    pec.employee_id,
    pec.customer_id,
    pec.customer_revenue,
    ROW_NUMBER() OVER (
      PARTITION BY pec.employee_id
      ORDER BY pec.customer_revenue DESC, pec.customer_orders DESC, pec.customer_id ASC
    ) AS rn
  FROM per_emp_cust pec
)
SELECT
  CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
  COALESCE(emp_stats.orders_processed, 0) AS orders_processed,
  COALESCE(emp_stats.total_revenue, 0) AS total_revenue,
  CONCAT(c.first_name, ' ', c.last_name) AS top_customer
FROM employees e
LEFT JOIN (
  SELECT employee_id, COUNT(*) AS orders_processed, SUM(total_amount) AS total_revenue
  FROM orders
  GROUP BY employee_id
) emp_stats ON emp_stats.employee_id = e.employee_id
LEFT JOIN ranked_top rt ON rt.employee_id = e.employee_id AND rt.rn = 1
LEFT JOIN customers c ON c.customer_id = rt.customer_id
ORDER BY total_revenue DESC;

-- Text2SQL
WITH employee_customer_sales AS (
    SELECT
        e.employee_id,
        CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
        c.customer_id,
        CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
        COUNT(o.order_id) AS orders_processed,
        SUM(o.total_amount) AS total_revenue,
        ROW_NUMBER() OVER (
            PARTITION BY e.employee_id
            ORDER BY SUM(o.total_amount) DESC
        ) AS rn
    FROM
        employees e
    LEFT JOIN
        orders o ON e.employee_id = o.employee_id
    LEFT JOIN
        customers c ON o.customer_id = c.customer_id
    GROUP BY
        e.employee_id, c.customer_id
)
SELECT
    ecs.employee_id,
    ecs.employee_name,
    IFNULL(SUM(ecs.orders_processed), 0) AS number_of_orders_processed,
    IFNULL(SUM(ecs.total_revenue), 0) AS total_revenue,
    ecs.customer_name AS top_customer
FROM
    employee_customer_sales ecs
WHERE
    ecs.rn = 1 OR ecs.customer_id IS NULL
GROUP BY
    ecs.employee_id, ecs.employee_name, ecs.customer_name
ORDER BY
    ecs.employee_id

-- Chat2DB
WITH EmployeeSales AS (
    SELECT 
        e.employee_id,
        e.first_name,
        e.last_name,
        COUNT(o.order_id) AS number_of_orders,
        SUM(od.quantity * od.unit_price) AS total_revenue,
        o.customer_id
    FROM 
        employees e
    JOIN 
        orders o ON e.employee_id = o.employee_id
    JOIN 
        order_details od ON o.order_id = od.order_id
    GROUP BY 
        e.employee_id, e.first_name, e.last_name, o.customer_id
),
TopCustomers AS (
    SELECT 
        es.employee_id,
        es.first_name,
        es.last_name,
        es.number_of_orders,
        es.total_revenue,
        es.customer_id,
        ROW_NUMBER() OVER (PARTITION BY es.employee_id ORDER BY es.total_revenue DESC) AS rn
    FROM 
        EmployeeSales es
)
SELECT 
    tc.employee_id,
    CONCAT(tc.first_name, ' ', tc.last_name) AS employee_name,
    tc.number_of_orders,
    tc.total_revenue,
    c.first_name AS top_customer_first_name,
    c.last_name AS top_customer_last_name
FROM 
    TopCustomers tc
JOIN 
    customers c ON tc.customer_id = c.customer_id
WHERE 
    tc.rn = 1
ORDER BY 
    tc.employee_id;

-- AI2sql
SELECT
    e.employee_id,
    CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
    COUNT(o.order_id) AS number_of_orders,
    SUM(o.total_amount) AS total_revenue,
    (
        SELECT CONCAT(c2.first_name, ' ', c2.last_name)
        FROM orders o2
        JOIN customers c2 ON o2.customer_id = c2.customer_id
        WHERE o2.employee_id = e.employee_id
        GROUP BY o2.customer_id
        ORDER BY COUNT(*) DESC, SUM(o2.total_amount) DESC
        LIMIT 1
    ) AS top_customer_name
FROM employees e
LEFT JOIN orders o ON e.employee_id = o.employee_id
GROUP BY e.employee_id, employee_name
ORDER BY total_revenue DESC;

-- Sequel
WITH employee_sales AS (
	SELECT 
		e.`employee_id`, 
		CONCAT(e.`first_name`, ' ', e.`last_name`) AS `employee_name`, 
		COUNT(DISTINCT o.`order_id`) AS `orders_processed`, 
		ROUND(SUM(o.`total_amount`), 2) AS `total_revenue` 
	FROM `employees` e 
	LEFT JOIN `orders` o ON e.`employee_id` = o.`employee_id` 
	GROUP BY e.`employee_id`
), 
top_customers AS (
	SELECT 
		o.`employee_id`, 
		CONCAT(c.`first_name`, ' ', c.`last_name`) AS `top_customer`, 
		ROUND(SUM(o.`total_amount`), 2) AS `customer_revenue`, 
		ROW_NUMBER() OVER (PARTITION BY o.`employee_id` ORDER BY SUM(o.`total_amount`) DESC) AS `rnk` 
	FROM `orders` o 
	JOIN `customers` c ON o.`customer_id` = c.`customer_id` 
	GROUP BY o.`employee_id`, c.`customer_id`
) 
SELECT 
	es.`employee_name`, 
	es.`orders_processed`, 
	es.`total_revenue`, 
	tc.`top_customer`, 
	tc.`customer_revenue` 
FROM employee_sales es 
LEFT JOIN top_customers tc ON es.`employee_id` = tc.`employee_id` AND tc.`rnk` = 1 
ORDER BY es.`total_revenue` DESC;

-- Vanna
SELECT 
    e.employee_id, e.first_name as employee_first_name, 
    e.last_name as employee_last_name, 
    COUNT(DISTINCT o.order_id) as orders_processed, 
    ROUND(SUM(o.total_amount), 2) as total_revenue, 
    (
        SELECT c.first_name 
        FROM customers c 
        INNER JOIN orders o2 ON c.customer_id = o2.customer_id 
        WHERE o2.employee_id = e.employee_id 
        GROUP BY c.customer_id, c.first_name 
        ORDER BY SUM(o2.total_amount) DESC 
        LIMIT 1
    ) as top_customer_first_name, 
    (
        SELECT c.last_name 
        FROM customers c 
        INNER JOIN orders o2 ON c.customer_id = o2.customer_id 
        WHERE o2.employee_id = e.employee_id 
        GROUP BY c.customer_id, c.last_name 
        ORDER BY SUM(o2.total_amount) DESC 
        LIMIT 1
    ) as top_customer_last_name 
FROM employees e 
INNER JOIN orders o ON e.employee_id = o.employee_id 
GROUP BY e.employee_id, e.first_name, e.last_name 
ORDER BY total_revenue DESC;

-- AskYourDatabase
SELECT 
    e.employee_id,
    e.first_name,
    e.last_name,
    e.email,
    COUNT(o.order_id) as orders_processed,
    SUM(o.total_amount) as total_revenue,
    top_customer.first_name as top_customer_first,
    top_customer.last_name as top_customer_last,
    top_customer.total_spent as top_customer_spent
FROM employees e
JOIN orders o ON e.employee_id = o.employee_id
LEFT JOIN (
    SELECT 
        o2.employee_id,
        c.customer_id,
        c.first_name,
        c.last_name,
        SUM(o2.total_amount) as total_spent,
        ROW_NUMBER() OVER (PARTITION BY o2.employee_id ORDER BY SUM(o2.total_amount) DESC) as rn
    FROM orders o2
    JOIN customers c ON o2.customer_id = c.customer_id
    GROUP BY o2.employee_id, c.customer_id, c.first_name, c.last_name
) as top_customer ON e.employee_id = top_customer.employee_id AND top_customer.rn = 1
GROUP BY e.employee_id, e.first_name, e.last_name, e.email, top_customer.first_name, top_customer.last_name, top_customer.total_spent
ORDER BY total_revenue DESC;