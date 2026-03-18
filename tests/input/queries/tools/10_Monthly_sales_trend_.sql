-- Monthly sales trend with employee and customer analysis. Show monthly sales trends including: Month, total revenue, top selling product, best performing employee, most active customer

-- SQLAI
WITH monthly_revenue AS (
  SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month,
         SUM(o.total_amount) AS total_revenue
  FROM orders o
  WHERE o.order_date IS NOT NULL
  GROUP BY month
),
product_month_revenue AS (
  SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month,
         od.product_id,
         SUM(od.quantity * od.unit_price) AS product_revenue
  FROM order_details od
  JOIN orders o ON od.order_id = o.order_id
  GROUP BY month, od.product_id
),
top_product AS (
  SELECT pmr.*,
         ROW_NUMBER() OVER (PARTITION BY pmr.month ORDER BY pmr.product_revenue DESC) AS rn
  FROM product_month_revenue pmr
),
employee_month_revenue AS (
  SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month,
         o.employee_id,
         SUM(o.total_amount) AS employee_revenue
  FROM orders o
  GROUP BY month, o.employee_id
),
top_employee AS (
  SELECT emr.*,
         ROW_NUMBER() OVER (PARTITION BY emr.month ORDER BY emr.employee_revenue DESC) AS rn
  FROM employee_month_revenue emr
),
customer_month_revenue AS (
  SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS month,
         o.customer_id,
         SUM(o.total_amount) AS customer_revenue
  FROM orders o
  GROUP BY month, o.customer_id
),
top_customer AS (
  SELECT cmr.*,
         ROW_NUMBER() OVER (PARTITION BY cmr.month ORDER BY cmr.customer_revenue DESC) AS rn
  FROM customer_month_revenue cmr
)
SELECT mr.month,
       COALESCE(mr.total_revenue, 0) AS total_revenue,
       p.product_name AS top_product,
       tp.product_revenue AS top_product_revenue,
       CONCAT(e.first_name, ' ', e.last_name) AS best_employee,
       te.employee_revenue AS best_employee_revenue,
       CONCAT(c.first_name, ' ', c.last_name) AS most_active_customer,
       tc.customer_revenue AS most_active_customer_revenue
FROM monthly_revenue mr
LEFT JOIN top_product tp ON tp.month = mr.month AND tp.rn = 1
LEFT JOIN products p ON p.product_id = tp.product_id
LEFT JOIN top_employee te ON te.month = mr.month AND te.rn = 1
LEFT JOIN employees e ON e.employee_id = te.employee_id
LEFT JOIN top_customer tc ON tc.month = mr.month AND tc.rn = 1
LEFT JOIN customers c ON c.customer_id = tc.customer_id
ORDER BY mr.month;

-- Text2SQL
WITH monthly_orders AS (
    SELECT
        DATE_FORMAT(order_date, '%Y-%m') AS month,
        order_id,
        employee_id,
        customer_id,
        total_amount
    FROM
        orders
),
monthly_revenue AS (
    SELECT
        month,
        SUM(total_amount) AS total_revenue
    FROM
        monthly_orders
    GROUP BY
        month
),
monthly_product_sales AS (
    SELECT
        mo.month,
        od.product_id,
        SUM(od.quantity) AS total_quantity,
        ROW_NUMBER() OVER (
            PARTITION BY mo.month
            ORDER BY SUM(od.quantity) DESC
        ) AS rn
    FROM
        monthly_orders mo
    JOIN
        order_details od ON mo.order_id = od.order_id
    GROUP BY
        mo.month, od.product_id
),
monthly_employee_sales AS (
    SELECT
        month,
        employee_id,
        SUM(total_amount) AS employee_revenue,
        ROW_NUMBER() OVER (
            PARTITION BY month
            ORDER BY SUM(total_amount) DESC
        ) AS rn
    FROM
        monthly_orders
    GROUP BY
        month, employee_id
),
monthly_customer_orders AS (
    SELECT
        month,
        customer_id,
        COUNT(order_id) AS orders_count,
        ROW_NUMBER() OVER (
            PARTITION BY month
            ORDER BY COUNT(order_id) DESC
        ) AS rn
    FROM
        monthly_orders
    GROUP BY
        month, customer_id
)
SELECT
    mr.month,
    mr.total_revenue,
    p.product_name AS top_selling_product,
    CONCAT(e.first_name, ' ', e.last_name) AS best_performing_employee,
    CONCAT(c.first_name, ' ', c.last_name) AS most_active_customer
FROM
    monthly_revenue mr
LEFT JOIN
    monthly_product_sales mps ON mr.month = mps.month AND mps.rn = 1
LEFT JOIN
    products p ON mps.product_id = p.product_id
LEFT JOIN
    monthly_employee_sales mes ON mr.month = mes.month AND mes.rn = 1
LEFT JOIN
    employees e ON mes.employee_id = e.employee_id
LEFT JOIN
    monthly_customer_orders mco ON mr.month = mco.month AND mco.rn = 1
LEFT JOIN
    customers c ON mco.customer_id = c.customer_id
ORDER BY
    mr.month;

-- Chat2DB
WITH MonthlySales AS (
    SELECT 
        DATE_FORMAT(o.order_date, '%Y-%m') AS order_month,
        SUM(od.quantity * od.unit_price) AS total_revenue,
        o.employee_id,
        o.customer_id,
        od.product_id,
        od.quantity * od.unit_price AS order_revenue
    FROM 
        orders o
    JOIN 
        order_details od ON o.order_id = od.order_id
    WHERE 
        o.status = 'Completed'
    GROUP BY 
        DATE_FORMAT(o.order_date, '%Y-%m'), o.employee_id, o.customer_id, od.product_id, od.quantity, od.unit_price
),
TopSellingProduct AS (
    SELECT 
        order_month,
        product_id,
        SUM(quantity) AS total_quantity_sold,
        ROW_NUMBER() OVER (PARTITION BY order_month ORDER BY SUM(quantity) DESC) AS rn
    FROM 
        order_details
    GROUP BY 
        order_month, product_id
),
BestPerformingEmployee AS (
    SELECT 
        order_month,
        employee_id,
        SUM(order_revenue) AS total_employee_revenue,
        ROW_NUMBER() OVER (PARTITION BY order_month ORDER BY SUM(order_revenue) DESC) AS rn
    FROM 
        MonthlySales
    GROUP BY 
        order_month, employee_id
),
MostActiveCustomer AS (
    SELECT 
        order_month,
        customer_id,
        COUNT(order_id) AS total_orders,
        ROW_NUMBER() OVER (PARTITION BY order_month ORDER BY COUNT(order_id) DESC) AS rn
    FROM 
        MonthlySales
    GROUP BY 
        order_month, customer_id
)
SELECT 
    ms.order_month,
    ms.total_revenue,
    p.product_name AS top_selling_product,
    CONCAT(e.first_name, ' ', e.last_name) AS best_performing_employee,
    CONCAT(c.first_name, ' ', c.last_name) AS most_active_customer
FROM 
    MonthlySales ms
JOIN 
    TopSellingProduct tsp ON ms.order_month = tsp.order_month AND tsp.rn = 1
JOIN 
    BestPerformingEmployee bpe ON ms.order_month = bpe.order_month AND bpe.rn = 1
JOIN 
    MostActiveCustomer mac ON ms.order_month = mac.order_month AND mac.rn = 1
JOIN 
    products p ON tsp.product_id = p.product_id
JOIN 
    employees e ON bpe.employee_id = e.employee_id
JOIN 
    customers c ON mac.customer_id = c.customer_id
GROUP BY 
    ms.order_month, ms.total_revenue, p.product_name, e.first_name, e.last_name, c.first_name, c.last_name
ORDER BY 
    ms.order_month;

-- AI2sql
WITH monthly_sales AS (
    SELECT
        DATE_FORMAT(sale_date, '%Y-%m') AS month,
        SUM(total_amount) AS total_revenue
    FROM sales
    GROUP BY month
),
top_product AS (
    SELECT
        DATE_FORMAT(sale_date, '%Y-%m') AS month,
        product_id,
        SUM(quantity) AS total_sold,
        ROW_NUMBER() OVER (PARTITION BY DATE_FORMAT(sale_date, '%Y-%m') ORDER BY SUM(quantity) DESC) AS rn
    FROM sale_items
    JOIN sales ON sale_items.sale_id = sales.id
    GROUP BY month, product_id
),
best_employee AS (
    SELECT
        DATE_FORMAT(sale_date, '%Y-%m') AS month,
        employee_id,
        SUM(total_amount) AS employee_revenue,
        ROW_NUMBER() OVER (PARTITION BY DATE_FORMAT(sale_date, '%Y-%m') ORDER BY SUM(total_amount) DESC) AS rn
    FROM sales
    GROUP BY month, employee_id
),
active_customer AS (
    SELECT
        DATE_FORMAT(sale_date, '%Y-%m') AS month,
        customer_id,
        COUNT(*) AS orders_count,
        ROW_NUMBER() OVER (PARTITION BY DATE_FORMAT(sale_date, '%Y-%m') ORDER BY COUNT(*) DESC) AS rn
    FROM sales
    GROUP BY month, customer_id
)
SELECT
    ms.month,
    ms.total_revenue,
    p.name AS top_selling_product,
    CONCAT(emp.first_name, ' ', emp.last_name) AS best_performing_employee,
    CONCAT(cust.first_name, ' ', cust.last_name) AS most_active_customer
FROM
    monthly_sales ms
LEFT JOIN top_product tp ON ms.month = tp.month AND tp.rn = 1
LEFT JOIN products p ON tp.product_id = p.id
LEFT JOIN best_employee be ON ms.month = be.month AND be.rn = 1
LEFT JOIN employees emp ON be.employee_id = emp.id
LEFT JOIN active_customer ac ON ms.month = ac.month AND ac.rn = 1
LEFT JOIN customers cust ON ac.customer_id = cust.id
ORDER BY ms.month;

-- Sequel
SELECT
  DATE_FORMAT (o.order_date, '%Y-%m') AS Month,
  CONCAT(c.first_name, ' ', c.last_name) AS TopCustomer,
  COUNT(o.order_id) AS Orders,
  ROUND(SUM(o.total_amount), 2) AS TotalSpent
FROM
  orders o
  JOIN customers c ON o.customer_id = c.customer_id
WHERE
  o.status != 'cancelled'
  AND o.order_date >= DATE_SUB (CURDATE (), INTERVAL 6 MONTH)
GROUP BY
  DATE_FORMAT (o.order_date, '%Y-%m'),
  c.customer_id,
  c.first_name,
  c.last_name
ORDER BY
  Month DESC,
  Orders DESC;

-- Vanna
NULL;

-- AskYourDatabase
SELECT 
    monthly_stats.month_year,
    monthly_stats.total_revenue,
    monthly_stats.total_orders,
    top_product.product_name as top_selling_product,
    top_product.product_quantity as top_product_qty,
    top_employee.first_name as top_employee_first,
    top_employee.last_name as top_employee_last,
    top_employee.employee_revenue as top_employee_revenue,
    top_customer.first_name as top_customer_first,
    top_customer.last_name as top_customer_last,
    top_customer.customer_spent as top_customer_spent
FROM (
    SELECT 
        DATE_FORMAT(o.order_date, '%Y-%m') as month_year,
        SUM(o.total_amount) as total_revenue,
        COUNT(o.order_id) as total_orders
    FROM orders o
    GROUP BY DATE_FORMAT(o.order_date, '%Y-%m')
) as monthly_stats
LEFT JOIN (
    SELECT 
        month_year,
        product_name,
        product_quantity,
        ROW_NUMBER() OVER (PARTITION BY month_year ORDER BY product_quantity DESC) as rn
    FROM (
        SELECT 
            DATE_FORMAT(o.order_date, '%Y-%m') as month_year,
            p.product_name,
            SUM(od.quantity) as product_quantity
        FROM orders o
        JOIN order_details od ON o.order_id = od.order_id
        JOIN products p ON od.product_id = p.product_id
        GROUP BY DATE_FORMAT(o.order_date, '%Y-%m'), p.product_name
    ) as product_sales
) as top_product ON monthly_stats.month_year = top_product.month_year AND top_product.rn = 1
LEFT JOIN (
    SELECT 
        month_year,
        first_name,
        last_name,
        employee_revenue,
        ROW_NUMBER() OVER (PARTITION BY month_year ORDER BY employee_revenue DESC) as rn
    FROM (
        SELECT 
            DATE_FORMAT(o.order_date, '%Y-%m') as month_year,
            e.first_name,
            e.last_name,
            SUM(o.total_amount) as employee_revenue
        FROM orders o
        JOIN employees e ON o.employee_id = e.employee_id
        GROUP BY DATE_FORMAT(o.order_date, '%Y-%m'), e.first_name, e.last_name
    ) as employee_sales
) as top_employee ON monthly_stats.month_year = top_employee.month_year AND top_employee.rn = 1
LEFT JOIN (
    SELECT 
        month_year,
        first_name,
        last_name,
        customer_spent,
        ROW_NUMBER() OVER (PARTITION BY month_year ORDER BY customer_spent DESC) as rn
    FROM (
        SELECT 
            DATE_FORMAT(o.order_date, '%Y-%m') as month_year,
            c.first_name,
            c.last_name,
            SUM(o.total_amount) as customer_spent
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        GROUP BY DATE_FORMAT(o.order_date, '%Y-%m'), c.first_name, c.last_name
    ) as customer_sales
) as top_customer ON monthly_stats.month_year = top_customer.month_year AND top_customer.rn = 1
ORDER BY monthly_stats.month_year DESC;

-- MyQuery
WITH monthly_aggregates AS (
    -- Base monthly sales
    SELECT 
        DATE_FORMAT(O.ORDER_DATE, '%Y-%m') AS month,
        DATE_FORMAT(O.ORDER_DATE, '%M %Y') AS month_name,
        SUM(OD.QUANTITY * OD.UNIT_PRICE) AS total_revenue,
        COUNT(DISTINCT O.ORDER_ID) AS total_orders
    FROM ORDERS O
    JOIN ORDER_DETAILS OD ON O.ORDER_ID = OD.ORDER_ID
    GROUP BY DATE_FORMAT(O.ORDER_DATE, '%Y-%m'), DATE_FORMAT(O.ORDER_DATE, '%M %Y')
),
product_ranking AS (
    SELECT 
        DATE_FORMAT(O.ORDER_DATE, '%Y-%m') AS month,
        P.PRODUCT_NAME,
        ROW_NUMBER() OVER (PARTITION BY DATE_FORMAT(O.ORDER_DATE, '%Y-%m') ORDER BY SUM(OD.QUANTITY) DESC) AS rn
    FROM ORDERS O
    JOIN ORDER_DETAILS OD ON O.ORDER_ID = OD.ORDER_ID
    JOIN PRODUCTS P ON OD.PRODUCT_ID = P.PRODUCT_ID
    GROUP BY DATE_FORMAT(O.ORDER_DATE, '%Y-%m'), P.PRODUCT_NAME
),
employee_ranking AS (
    SELECT 
        DATE_FORMAT(O.ORDER_DATE, '%Y-%m') AS month,
        CONCAT(E.FIRST_NAME, ' ', E.LAST_NAME) AS employee_name,
        ROW_NUMBER() OVER (PARTITION BY DATE_FORMAT(O.ORDER_DATE, '%Y-%m') ORDER BY SUM(OD.QUANTITY * OD.UNIT_PRICE) DESC) AS rn
    FROM ORDERS O
    JOIN ORDER_DETAILS OD ON O.ORDER_ID = OD.ORDER_ID
    JOIN EMPLOYEES E ON O.EMPLOYEE_ID = E.EMPLOYEE_ID
    GROUP BY DATE_FORMAT(O.ORDER_DATE, '%Y-%m'), E.EMPLOYEE_ID, E.FIRST_NAME, E.LAST_NAME
),
customer_ranking AS (
    SELECT 
        DATE_FORMAT(O.ORDER_DATE, '%Y-%m') AS month,
        CONCAT(C.FIRST_NAME, ' ', C.LAST_NAME) AS customer_name,
        ROW_NUMBER() OVER (PARTITION BY DATE_FORMAT(O.ORDER_DATE, '%Y-%m') ORDER BY COUNT(DISTINCT O.ORDER_ID) DESC) AS rn
    FROM ORDERS O
    JOIN CUSTOMERS C ON O.CUSTOMER_ID = C.CUSTOMER_ID
    GROUP BY DATE_FORMAT(O.ORDER_DATE, '%Y-%m'), C.CUSTOMER_ID, C.FIRST_NAME, C.LAST_NAME
)
SELECT 
    MA.month_name,
    MA.total_orders,
    FORMAT(MA.total_revenue, 2) AS total_revenue,
    PR.PRODUCT_NAME AS top_product,
    ER.employee_name AS top_employee,
    CR.customer_name AS most_active_customer
FROM monthly_aggregates MA
LEFT JOIN product_ranking PR ON MA.month = PR.month AND PR.rn = 1
LEFT JOIN employee_ranking ER ON MA.month = ER.month AND ER.rn = 1
LEFT JOIN customer_ranking CR ON MA.month = CR.month AND CR.rn = 1
ORDER BY MA.month;