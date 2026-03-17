-- Employees who served customers from specific areas: Find employees who have processed orders for customers living in addresses containing "Av." but have NOT processed any orders for customers living in addresses containing "Rua". Include the count of such customers served by each employee

-- SQLAI
SELECT
  product_name,
  category_name,
  product_revenue,
  category_revenue,
  ROUND(product_revenue / category_revenue * 100, 2) AS pct_contribution
FROM (
  SELECT
    p.product_id,
    p.product_name,
    c.category_name,
    p.category_id,
    COALESCE(SUM(od.quantity * od.unit_price), 0) AS product_revenue,
    SUM(COALESCE(SUM(od.quantity * od.unit_price), 0)) OVER (PARTITION BY p.category_id) AS category_revenue
  FROM products p
  JOIN categories c ON c.category_id = p.category_id
  LEFT JOIN order_details od ON od.product_id = p.product_id
  GROUP BY p.product_id, p.product_name, c.category_name, p.category_id
) t
WHERE category_revenue > 0
  AND product_revenue / category_revenue > 0.30
ORDER BY pct_contribution DESC;

-- Text2SQL
WITH employee_address_counts AS (
    SELECT
        e.employee_id,
        CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
        e.position,
        c.address AS customer_address,
        COUNT(DISTINCT c.customer_id) AS customers_count,
        ROW_NUMBER() OVER (
            PARTITION BY e.employee_id
            ORDER BY COUNT(DISTINCT c.customer_id) DESC
        ) AS rn
    FROM
        employees e
    JOIN
        orders o ON e.employee_id = o.employee_id
    JOIN
        customers c ON o.customer_id = c.customer_id
    GROUP BY
        e.employee_id, e.first_name, e.last_name, e.position, c.address
)
SELECT
    employee_name,
    position,
    customer_address,
    customers_count AS number_of_customers_from_address
FROM
    employee_address_counts
WHERE
    rn = 1
ORDER BY
    employee_name

-- Chat2DB
WITH ProductRevenue AS (
    SELECT 
        od.product_id,
        SUM(od.quantity * od.unit_price) AS product_revenue
    FROM 
        order_details od
    JOIN 
        orders o ON od.order_id = o.order_id
    WHERE 
        o.status = 'Completed'
    GROUP BY 
        od.product_id
),
CategoryRevenue AS (
    SELECT 
        p.category_id,
        SUM(pr.product_revenue) AS category_revenue
    FROM 
        ProductRevenue pr
    JOIN 
        products p ON pr.product_id = p.product_id
    GROUP BY 
        p.category_id
),
ProductCategoryRevenue AS (
    SELECT 
        pr.product_id,
        pr.product_revenue,
        p.category_id,
        cr.category_revenue,
        (pr.product_revenue / cr.category_revenue) * 100 AS percentage_contribution
    FROM 
        ProductRevenue pr
    JOIN 
        products p ON pr.product_id = p.product_id
    JOIN 
        CategoryRevenue cr ON p.category_id = cr.category_id
)
SELECT 
    p.product_name,
    c.category_name,
    pcr.product_revenue,
    pcr.category_revenue,
    pcr.percentage_contribution
FROM 
    ProductCategoryRevenue pcr
JOIN 
    products p ON pcr.product_id = p.product_id
JOIN 
    categories c ON p.category_id = c.category_id
WHERE 
    pcr.percentage_contribution > 30
ORDER BY 
    pcr.category_id, pcr.percentage_contribution DESC;

-- AI2sql
SELECT 
    e.employee_id,
    e.name AS employee_name,
    e.position,
    ca.address AS customer_address,
    COUNT(*) AS customer_count
FROM
    services s
    JOIN employees e ON s.employee_id = e.employee_id
    JOIN customers c ON s.customer_id = c.customer_id
    JOIN customer_addresses ca ON c.address_id = ca.address_id
GROUP BY
    e.employee_id, ca.address
HAVING
    customer_count = (
        SELECT 
            MAX(cnt)
        FROM (
            SELECT 
                COUNT(*) AS cnt
            FROM
                services s2
                JOIN customers c2 ON s2.customer_id = c2.customer_id
            WHERE
                s2.employee_id = e.employee_id
            GROUP BY
                c2.address_id
        ) AS subq
    )
ORDER BY
    e.employee_id, customer_count DESC;

-- Sequel
WITH EmployeeAddressCounts AS (
	SELECT 
		e.`employee_id`, 
		e.`first_name`, 
		e.`last_name`, 
		e.`position`, 
		c.`address`, 
		COUNT(DISTINCT o.`customer_id`) AS `number_of_customers`, 
		COUNT(o.`order_id`) AS `total_orders`, 
		ROW_NUMBER() OVER (PARTITION BY e.`employee_id` ORDER BY COUNT(DISTINCT o.`customer_id`) DESC, COUNT(o.`order_id`) DESC) AS `rn` 
	FROM supermarket.employees e INNER JOIN supermarket.orders o ON e.`employee_id` = o.`employee_id` 
	INNER JOIN supermarket.customers c ON o.`customer_id` = c.`customer_id` 
	GROUP BY e.`employee_id`, e.`first_name`, e.`last_name`, e.`position`, c.`address`) 
SELECT 
	`employee_id`, 
	CONCAT(`first_name`, ' ', `last_name`) AS `employee_name`, 
	`position`, 
	`address` AS `customer_address`, 
	`number_of_customers` 
FROM EmployeeAddressCounts 
WHERE `rn` = 1 
ORDER BY `number_of_customers` DESC ;

-- Vanna
WITH product_revenue AS ( 
    SELECT 
        p.product_id, 
        p.product_name, 
        p.category_id, 
        c.category_name, 
        ROUND(SUM(od.quantity * od.unit_price), 2) as product_revenue 
    FROM products p 
    INNER JOIN categories c ON p.category_id = c.category_id 
    INNER JOIN order_details od ON p.product_id = od.product_id 
    GROUP BY p.product_id, p.product_name, p.category_id, c.category_name 
), 
category_revenue AS ( 
    SELECT 
        category_id, 
        category_name, 
        ROUND(SUM(product_revenue), 2) as total_category_revenue 
    FROM product_revenue 
    GROUP BY category_id, category_name 
) 
SELECT 
    cr.category_name, 
    COUNT(*) as num_products_over_30_percent, 
    COUNT(DISTINCT pr.product_id) as distinct_products, 
    ROUND(AVG((pr.product_revenue / cr.total_category_revenue) * 100), 2) as avg_percentage 
FROM product_revenue pr 
INNER JOIN category_revenue cr ON pr.category_id = cr.category_id 
WHERE (pr.product_revenue / cr.total_category_revenue) > 0.30 
GROUP BY cr.category_id, cr.category_name 
ORDER BY num_products_over_30_percent DESC;

-- AskYourDatabase
SELECT 
    p.product_name,
    c.category_name,
    product_revenue.product_revenue,
    category_revenue.category_total_revenue,
    ROUND((product_revenue.product_revenue / category_revenue.category_total_revenue) * 100, 2) as percentage_contribution
FROM products p
JOIN categories c ON p.category_id = c.category_id
JOIN (
    SELECT 
        od.product_id,
        SUM(od.quantity * od.unit_price) as product_revenue
    FROM order_details od
    GROUP BY od.product_id
) as product_revenue ON p.product_id = product_revenue.product_id
JOIN (
    SELECT 
        p2.category_id,
        SUM(od2.quantity * od2.unit_price) as category_total_revenue
    FROM products p2
    JOIN order_details od2 ON p2.product_id = od2.product_id
    GROUP BY p2.category_id
) as category_revenue ON p.category_id = category_revenue.category_id
WHERE (product_revenue.product_revenue / category_revenue.category_total_revenue) * 100 > 30
ORDER BY percentage_contribution DESC, category_name;