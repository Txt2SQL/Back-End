-- Customers who spent more than average. Find customers whose total spending is above the average customer spending

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

-- Products that have never been sold: List all products that have never been included in any order

SELECT PRODUCT_ID, PRODUCT_NAME
FROM PRODUCTS
WHERE PRODUCT_ID NOT IN (
    SELECT DISTINCT PRODUCT_ID
    FROM ORDER_DETAILS
);

-- Employees who processed more orders than average. Find employees who have processed more orders than the average number of orders per employee

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

-- Most expensive product in each category. For each category, show the most expensive product and its price

SELECT C.CATEGORY_ID, P.PRODUCT_ID, P.PRODUCT_NAME, P.PRICE
FROM PRODUCTS P
JOIN CATEGORIES C ON P.CATEGORY_ID = C.CATEGORY_ID
WHERE P.PRICE = (
    SELECT MAX(PRICE)
    FROM PRODUCTS
    WHERE CATEGORY_ID = C.CATEGORY_ID
);

-- Customers who bought the most popular product. Find customers who purchased the product that has been sold the most times

SELECT C.CUSTOMER_ID, C.FIRST_NAME, C.LAST_NAME
FROM CUSTOMERS C
WHERE C.CUSTOMER_ID IN (
    SELECT O.CUSTOMER_ID
    FROM ORDERS O
    JOIN ORDER_DETAILS OD ON O.ORDER_ID = OD.ORDER_ID
    WHERE OD.PRODUCT_ID = (
        SELECT PRODUCT_ID
        FROM ORDER_DETAILS
        GROUP BY PRODUCT_ID
        ORDER BY COUNT(*) DESC
        LIMIT 1
    )
);

-- Customer purchase history with details. Show complete purchase history for each customer including: Customer name, order date, product names, quantities, and total per order

-- Supplier performance analysis. For each supplier, show: Total products supplied, total quantity sold, and total revenue generated, Include suppliers with no sales

-- Employee sales performance with customer details. Show each employee's sales performance including: Employee name, number of orders processed, total revenue, and their top customer

WITH cust_orders AS (
  SELECT o.employee_id, o.customer_id, COUNT(*) AS orders_count
  FROM supermarket.orders o
  GROUP BY o.employee_id, o.customer_id
),
max_per_emp AS (
  SELECT co.employee_id, MAX(co.orders_count) AS max_orders
  FROM cust_orders co
  GROUP BY co.employee_id
)
SELECT DISTINCT
    e.employee_id,
    CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
    c.customer_id,
    CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
    co.orders_count
FROM cust_orders co
JOIN max_per_emp m ON co.employee_id = m.employee_id AND co.orders_count = m.max_orders
JOIN supermarket.employees e ON e.employee_id = co.employee_id
JOIN supermarket.customers c ON c.customer_id = co.customer_id
ORDER BY e.employee_id;

WITH agg AS (
  SELECT
    o.employee_id,
    o.customer_id,
    SUM(od.quantity) AS total_quantity
  FROM orders o
  JOIN order_details od ON o.order_id = od.order_id
  GROUP BY o.employee_id, o.customer_id
)
SELECT
  e.employee_id,
  CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
  c.customer_id,
  CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
  a.total_quantity
FROM (
  SELECT
    a.*,
    ROW_NUMBER() OVER (PARTITION BY a.employee_id ORDER BY a.total_quantity DESC) AS rn
  FROM agg a
) a
JOIN employees e ON e.employee_id = a.employee_id
JOIN customers c ON c.customer_id = a.customer_id
WHERE a.rn = 1
ORDER BY e.employee_id;