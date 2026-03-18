-- Products with above-average sales in their category. For each product, determine if its total sales quantity is above the average sales quantity of all products in the same category. Show product name, category, total sales, and category average sales

-- SQLAI
WITH agg AS (
  SELECT
    o.employee_id,
    c.address,
    COUNT(DISTINCT o.customer_id) AS cust_count
  FROM orders o
  JOIN customers c ON o.customer_id = c.customer_id
  GROUP BY o.employee_id, c.address
),
emp_agg AS (
  SELECT
    e.employee_id,
    CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
    e.position,
    a.address,
    COALESCE(a.cust_count, 0) AS cust_count
  FROM employees e
  LEFT JOIN agg a ON e.employee_id = a.employee_id
),
ranked AS (
  SELECT
    employee_id,
    employee_name,
    position,
    address,
    cust_count,
    ROW_NUMBER() OVER (PARTITION BY employee_id ORDER BY cust_count DESC, address) AS rn
  FROM emp_agg
)
SELECT
  employee_name,
  position,
  address AS customer_address,
  cust_count AS num_customers_from_address
FROM ranked
WHERE rn = 1
ORDER BY employee_name;

-- Text2SQL
WITH product_sales AS (
    SELECT
        p.product_id,
        p.product_name,
        p.category_id,
        c.category_name,
        IFNULL(SUM(od.quantity), 0) AS total_sales
    FROM
        products p
    JOIN
        categories c ON p.category_id = c.category_id
    LEFT JOIN
        order_details od ON p.product_id = od.product_id
    GROUP BY
        p.product_id, p.product_name, p.category_id, c.category_name
),
category_avg AS (
    SELECT
        category_id,
        AVG(total_sales) AS avg_sales
    FROM
        product_sales
    GROUP BY
        category_id
)
SELECT
    ps.product_name,
    ps.category_name,
    ps.total_sales,
    ca.avg_sales AS category_average_sales
FROM
    product_sales ps
JOIN
    category_avg ca ON ps.category_id = ca.category_id
WHERE
    ps.total_sales > ca.avg_sales
ORDER BY
    ps.category_name, ps.product_name;

-- Chat2DB
WITH EmployeeServiceCounts AS (
    SELECT 
        e.employee_id,
        e.first_name,
        e.last_name,
        e.position,
        c.address,
        COUNT(o.order_id) AS service_count
    FROM 
        employees e
    JOIN 
        orders o ON e.employee_id = o.employee_id
    JOIN 
        customers c ON o.customer_id = c.customer_id
    GROUP BY 
        e.employee_id, e.first_name, e.last_name, e.position, c.address
),
MaxServiceCounts AS (
    SELECT 
        employee_id,
        MAX(service_count) AS max_service_count
    FROM 
        EmployeeServiceCounts
    GROUP BY 
        employee_id
)
SELECT 
    esc.employee_id,
    esc.first_name,
    esc.last_name,
    esc.position,
    esc.address,
    esc.service_count
FROM 
    EmployeeServiceCounts esc
JOIN 
    MaxServiceCounts msc ON esc.employee_id = msc.employee_id AND esc.service_count = msc.max_service_count
ORDER BY 
    esc.employee_id;

-- AI2sql
SELECT
    p.product_name,
    c.category_name,
    SUM(s.quantity) AS total_sales,
    cat_avg.category_avg_sales
FROM
    products p
    JOIN categories c ON p.category_id = c.category_id
    JOIN sales s ON p.product_id = s.product_id
    JOIN (
        SELECT
            p2.category_id,
            AVG(prod_total.total_qty) AS category_avg_sales
        FROM
            products p2
            JOIN (
                SELECT
                    product_id,
                    SUM(quantity) AS total_qty
                FROM
                    sales
                GROUP BY
                    product_id
            ) prod_total ON p2.product_id = prod_total.product_id
        GROUP BY
            p2.category_id
    ) cat_avg ON p.category_id = cat_avg.category_id
GROUP BY
    p.product_id
HAVING
    total_sales > cat_avg.category_avg_sales;

-- Sequel
WITH product_sales AS (
	SELECT 
		p.`product_id`, 
		p.`product_name`, 
		p.`category_id`, 
		c.`category_name`, 
		SUM(od.`quantity`) AS `total_sales` 
	FROM supermarket.products p 
	INNER JOIN supermarket.categories c ON p.`category_id` = c.`category_id` 
	INNER JOIN supermarket.order_details od ON p.`product_id` = od.`product_id` 
	GROUP BY p.`product_id`, p.`product_name`, p.`category_id`, c.`category_name`
), 
category_averages AS (
	SELECT 
		`category_id`, 
		ROUND(AVG(`total_sales`), 2) AS `category_avg_sales` 
	FROM product_sales 
	GROUP BY `category_id`
) 
SELECT 
	ps.`product_name`, 
	ps.`category_name`, 
	ps.`total_sales`, 
	ca.`category_avg_sales` 
FROM product_sales ps 
INNER JOIN category_averages ca ON ps.`category_id` = ca.`category_id` 
WHERE ps.`total_sales` > ca.`category_avg_sales` 
ORDER BY ps.`category_name`, ps.`total_sales` DESC;

-- Vanna
NULL;

-- AskYourDatabase
SELECT 
    e.employee_id,
    e.first_name,
    e.last_name,
    e.position,
    top_address.customer_address,
    top_address.customer_count
FROM employees e
JOIN (
    SELECT 
        o.employee_id,
        c.address as customer_address,
        COUNT(DISTINCT c.customer_id) as customer_count,
        ROW_NUMBER() OVER (PARTITION BY o.employee_id ORDER BY COUNT(DISTINCT c.customer_id) DESC) as rn
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    GROUP BY o.employee_id, c.address
) as top_address ON e.employee_id = top_address.employee_id AND top_address.rn = 1
ORDER BY top_address.customer_count DESC, e.employee_id;

-- MyQuery

WITH product_stats AS (
    SELECT 
        P.PRODUCT_NAME,
        C.CATEGORY_NAME,
        COALESCE(SUM(OD.QUANTITY), 0) AS total_sales,
        ROUND(
            AVG(COALESCE(SUM(OD.QUANTITY), 0)) OVER (PARTITION BY P.CATEGORY_ID),
            2
        ) AS category_avg_sales
    FROM PRODUCTS P
    LEFT JOIN CATEGORIES C ON P.CATEGORY_ID = C.CATEGORY_ID
    LEFT JOIN ORDER_DETAILS OD ON P.PRODUCT_ID = OD.PRODUCT_ID
    GROUP BY P.PRODUCT_ID, P.PRODUCT_NAME, P.CATEGORY_ID, C.CATEGORY_NAME
)
SELECT *
FROM product_stats
WHERE total_sales > category_avg_sales
ORDER BY CATEGORY_NAME, total_sales DESC;WITH employee_address_stats AS (
    -- Calculate customer count for each employee and address combination
    SELECT 
        O.EMPLOYEE_ID,
        CONCAT(E.FIRST_NAME, ' ', E.LAST_NAME) AS employee_name,
        E.POSITION,
        C.ADDRESS,
        COUNT(DISTINCT C.CUSTOMER_ID) AS customers_served,
        MAX(COUNT(DISTINCT C.CUSTOMER_ID)) OVER (PARTITION BY O.EMPLOYEE_ID) AS max_customers_for_employee
    FROM EMPLOYEES E
    JOIN ORDERS O ON E.EMPLOYEE_ID = O.EMPLOYEE_ID
    JOIN CUSTOMERS C ON O.CUSTOMER_ID = C.CUSTOMER_ID
    WHERE C.ADDRESS IS NOT NULL AND C.ADDRESS != ''
    GROUP BY O.EMPLOYEE_ID, E.FIRST_NAME, E.LAST_NAME, E.POSITION, C.ADDRESS
)
SELECT 
    employee_name,
    POSITION,
    ADDRESS AS primary_service_address,
    customers_served
FROM employee_address_stats
WHERE customers_served = max_customers_for_employee
ORDER BY customers_served DESC, employee_name;