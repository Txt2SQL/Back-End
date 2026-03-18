-- Products that represent more than 30% of their category's revenue. Identify products whose total revenue contributes to more than 30% of the total revenue of their respective category. Show product name, category, product revenue, category revenue, and percentage contribution

-- SQLAI
WITH months AS (
  SELECT 1 AS month UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
  UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8
  UNION ALL SELECT 9 UNION ALL SELECT 10 UNION ALL SELECT 11 UNION ALL SELECT 12
),
customer_months AS (
  SELECT c.customer_id, c.first_name, c.last_name, m.month
  FROM customers c
  CROSS JOIN months m
),
monthly_spend AS (
  SELECT
    cm.customer_id,
    cm.first_name,
    cm.last_name,
    cm.month,
    COALESCE(SUM(o.total_amount), 0) AS month_total
  FROM customer_months cm
  LEFT JOIN orders o
    ON o.customer_id = cm.customer_id
   AND YEAR(o.order_date) = 2024
   AND MONTH(o.order_date) = cm.month
  GROUP BY cm.customer_id, cm.first_name, cm.last_name, cm.month
),
avg_monthly AS (
  SELECT
    customer_id,
    first_name,
    last_name,
    AVG(month_total) AS avg_monthly
  FROM monthly_spend
  GROUP BY customer_id, first_name, last_name
)
SELECT
  CONCAT(a.first_name, ' ', a.last_name) AS customer_name,
  ROUND(a.avg_monthly, 2) AS average_monthly_spending,
  'consistent' AS consistency_flag
FROM avg_monthly a
WHERE NOT EXISTS (
  SELECT 1
  FROM monthly_spend m
  WHERE m.customer_id = a.customer_id
    AND (m.month_total < a.avg_monthly * 0.8 OR m.month_total > a.avg_monthly * 1.2)
)
ORDER BY a.last_name, a.first_name;

-- Text2SQL
WITH product_revenue AS (
    SELECT
        p.product_id,
        p.product_name,
        p.category_id,
        c.category_name,
        IFNULL(SUM(od.quantity * od.unit_price), 0) AS product_total_revenue
    FROM
        products p
    JOIN
        categories c ON p.category_id = c.category_id
    LEFT JOIN
        order_details od ON p.product_id = od.product_id
    GROUP BY
        p.product_id, p.product_name, p.category_id, c.category_name
),
category_revenue AS (
    SELECT
        category_id,
        SUM(product_total_revenue) AS category_total_revenue
    FROM
        product_revenue
    GROUP BY
        category_id
)
SELECT
    pr.product_name,
    pr.category_name,
    pr.product_total_revenue AS product_revenue,
    cr.category_total_revenue,
    ROUND(
        (pr.product_total_revenue / cr.category_total_revenue) * 100, 2
    ) AS percentage_contribution
FROM
    product_revenue pr
JOIN
    category_revenue cr ON pr.category_id = cr.category_id
WHERE
    cr.category_total_revenue > 0
    AND (pr.product_total_revenue / cr.category_total_revenue) > 0.3
ORDER BY
    pr.category_name, percentage_contribution DESC;

-- Chat2DB
WITH MonthlySpending AS (
    SELECT 
        o.customer_id,
        DATE_FORMAT(o.order_date, '%Y-%m') AS order_month,
        SUM(od.quantity * od.unit_price) AS monthly_spending
    FROM 
        orders o
    JOIN 
        order_details od ON o.order_id = od.order_id
    WHERE 
        YEAR(o.order_date) = 2024 AND o.status = 'Completed'
    GROUP BY 
        o.customer_id, DATE_FORMAT(o.order_date, '%Y-%m')
),
AverageMonthlySpending AS (
    SELECT 
        customer_id,
        AVG(monthly_spending) AS avg_monthly_spending
    FROM 
        MonthlySpending
    GROUP BY 
        customer_id
),
ConsistencyCheck AS (
    SELECT 
        ms.customer_id,
        ms.order_month,
        ms.monthly_spending,
        ams.avg_monthly_spending,
        ABS(ms.monthly_spending - ams.avg_monthly_spending) / ams.avg_monthly_spending * 100 AS spending_variation_percentage
    FROM 
        MonthlySpending ms
    JOIN 
        AverageMonthlySpending ams ON ms.customer_id = ams.customer_id
)
SELECT 
    c.first_name,
    c.last_name,
    ams.avg_monthly_spending,
    CASE 
        WHEN MAX(cc.spending_variation_percentage) <= 20 THEN 'Consistent'
        ELSE 'Not Consistent'
    END AS consistency_flag
FROM 
    ConsistencyCheck cc
JOIN 
    customers c ON cc.customer_id = c.customer_id
JOIN 
    AverageMonthlySpending ams ON cc.customer_id = ams.customer_id
GROUP BY 
    c.customer_id, c.first_name, c.last_name, ams.avg_monthly_spending
ORDER BY 
    c.customer_id;

-- AI2sql
SELECT
    p.product_name,
    c.category_name,
    SUM(oi.quantity * oi.unit_price) AS product_revenue,
    cat_revenues.category_revenue,
    ROUND(SUM(oi.quantity * oi.unit_price) / cat_revenues.category_revenue * 100, 2) AS percentage_contribution
FROM
    products p
    JOIN categories c ON p.category_id = c.category_id
    JOIN order_items oi ON p.product_id = oi.product_id
    JOIN (
        SELECT
            p2.category_id,
            SUM(oi2.quantity * oi2.unit_price) AS category_revenue
        FROM
            products p2
            JOIN order_items oi2 ON p2.product_id = oi2.product_id
        GROUP BY
            p2.category_id
    ) cat_revenues ON c.category_id = cat_revenues.category_id
GROUP BY
    p.product_id, p.product_name, c.category_name, cat_revenues.category_revenue
HAVING
    SUM(oi.quantity * oi.unit_price) > 0.3 * cat_revenues.category_revenue
ORDER BY
    percentage_contribution DESC;

-- Sequel
WITH
  ProductRevenue AS (
    SELECT
      p.product_id,
      p.product_name,
      p.category_id,
      c.category_name,
      SUM(od.quantity * od.unit_price) AS product_revenue
    FROM
      supermarket.products p
      INNER JOIN supermarket.order_details od ON p.product_id = od.product_id
      INNER JOIN supermarket.categories c ON p.category_id = c.category_id
    GROUP BY
      p.product_id,
      p.product_name,
      p.category_id,
      c.category_name
  ),
  CategoryRevenue AS (
    SELECT
      category_id,
      SUM(product_revenue) AS category_revenue
    FROM
      ProductRevenue
    GROUP BY
      category_id
  )
SELECT
  pr.product_name,
  pr.category_name,
  ROUND(pr.product_revenue, 2) AS product_revenue,
  ROUND(cr.category_revenue, 2) AS category_revenue,
  ROUND(
    (pr.product_revenue / cr.category_revenue * 100),
    2
  ) AS percentage_contribution
FROM
  ProductRevenue pr
  INNER JOIN CategoryRevenue cr ON pr.category_id = cr.category_id
WHERE
  (pr.product_revenue / cr.category_revenue * 100) > 30
ORDER BY
  percentage_contribution DESC;

-- Vanna
NULL;

-- AskYourDatabase
SELECT 
    c.customer_id,
    c.first_name,
    c.last_name,
    ROUND(customer_avg.avg_monthly_spending, 2) as avg_monthly_spending,
    'Consistent' as consistency_flag
FROM customers c
JOIN (
    SELECT 
        customer_id,
        AVG(monthly_spending) as avg_monthly_spending
    FROM (
        SELECT 
            o.customer_id,
            DATE_FORMAT(o.order_date, '%Y-%m') as month_year,
            SUM(o.total_amount) as monthly_spending
        FROM orders o
        WHERE YEAR(o.order_date) = 2024
        GROUP BY o.customer_id, DATE_FORMAT(o.order_date, '%Y-%m')
    ) as monthly_totals
    GROUP BY customer_id
) as customer_avg ON c.customer_id = customer_avg.customer_id
WHERE NOT EXISTS (
    SELECT 1
    FROM (
        SELECT 
            o2.customer_id,
            DATE_FORMAT(o2.order_date, '%Y-%m') as month_year,
            SUM(o2.total_amount) as monthly_spending
        FROM orders o2
        WHERE YEAR(o2.order_date) = 2024
        GROUP BY o2.customer_id, DATE_FORMAT(o2.order_date, '%Y-%m')
    ) as monthly_check
    WHERE monthly_check.customer_id = c.customer_id
    AND (monthly_check.monthly_spending < customer_avg.avg_monthly_spending * 0.8 
         OR monthly_check.monthly_spending > customer_avg.avg_monthly_spending * 1.2)
)
ORDER BY avg_monthly_spending DESC;

-- MyQuery

WITH revenue_stats AS (
    SELECT 
        P.PRODUCT_NAME,
        C.CATEGORY_NAME,
        SUM(OD.QUANTITY * OD.UNIT_PRICE) AS product_revenue,
        SUM(SUM(OD.QUANTITY * OD.UNIT_PRICE)) OVER (PARTITION BY P.CATEGORY_ID) AS category_revenue
    FROM PRODUCTS P
    JOIN CATEGORIES C ON P.CATEGORY_ID = C.CATEGORY_ID
    LEFT JOIN ORDER_DETAILS OD ON P.PRODUCT_ID = OD.PRODUCT_ID
    GROUP BY P.PRODUCT_ID, P.PRODUCT_NAME, P.CATEGORY_ID, C.CATEGORY_NAME
)
SELECT 
    PRODUCT_NAME,
    CATEGORY_NAME,
    FORMAT(product_revenue, 2) AS product_revenue,
    FORMAT(category_revenue, 2) AS category_revenue,
    CONCAT(ROUND(product_revenue / category_revenue * 100, 2), '%') AS contribution
FROM revenue_stats
WHERE product_revenue / category_revenue > 0.3
  AND product_revenue > 0
ORDER BY CATEGORY_NAME, product_revenue DESC;