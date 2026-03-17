-- Customers with consistent monthly spending pattern. Find customers whose spending in each month of 2024 was within 20% of their average monthly spending (Customers who spend consistently month-to-month). Show customer name, average monthly spending, and consistency flag

-- SQLAI
WITH RECURSIVE months AS (
  SELECT DATE('2024-01-01') AS month_start
  UNION ALL
  SELECT DATE_ADD(month_start, INTERVAL 1 MONTH)
  FROM months
  WHERE month_start < '2024-12-01'
),
monthly_spend AS (
  SELECT c.customer_id,
         c.first_name,
         c.last_name,
         m.month_start,
         COALESCE(SUM(o.total_amount), 0) AS month_spend
  FROM customers c
  CROSS JOIN months m
  LEFT JOIN orders o
    ON o.customer_id = c.customer_id
   AND o.order_date >= m.month_start
   AND o.order_date < DATE_ADD(m.month_start, INTERVAL 1 MONTH)
  GROUP BY c.customer_id, c.first_name, c.last_name, m.month_start
),
per_customer AS (
  SELECT customer_id,
         first_name,
         last_name,
         AVG(month_spend) AS avg_monthly,
         MIN(month_spend) AS min_month_spend,
         MAX(month_spend) AS max_month_spend
  FROM monthly_spend
  GROUP BY customer_id, first_name, last_name
)
SELECT
  CONCAT(first_name, ' ', last_name) AS customer_name,
  ROUND(avg_monthly, 2) AS avg_monthly_spending,
  CASE
    WHEN min_month_spend >= avg_monthly * 0.8
     AND max_month_spend <= avg_monthly * 1.2 THEN 'consistent'
    ELSE 'not_consistent'
  END AS consistency_flag
FROM per_customer
WHERE avg_monthly > 0
ORDER BY customer_name;

-- Text2SQL
WITH customer_monthly_spending AS (
    SELECT
        o.customer_id,
        CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
        DATE_FORMAT(o.order_date, '%Y-%m') AS month,
        SUM(o.total_amount) AS monthly_spending
    FROM
        orders o
    JOIN
        customers c ON o.customer_id = c.customer_id
    WHERE
        YEAR(o.order_date) = 2024
    GROUP BY
        o.customer_id, month
),
customer_avg_spending AS (
    SELECT
        customer_id,
        customer_name,
        AVG(monthly_spending) AS avg_monthly_spending,
        COUNT(*) AS months_with_orders
    FROM
        customer_monthly_spending
    GROUP BY
        customer_id, customer_name
),
customer_consistency AS (
    SELECT
        cms.customer_id,
        cms.customer_name,
        cas.avg_monthly_spending,
        COUNT(
            CASE
                WHEN ABS(cms.monthly_spending - cas.avg_monthly_spending) <= 0.2 * cas.avg_monthly_spending
                THEN 1
                ELSE NULL
            END
        ) AS consistent_months,
        cas.months_with_orders
    FROM
        customer_monthly_spending cms
    JOIN
        customer_avg_spending cas ON cms.customer_id = cas.customer_id
    GROUP BY
        cms.customer_id, cms.customer_name, cas.avg_monthly_spending, cas.months_with_orders
)
SELECT
    customer_name,
    ROUND(avg_monthly_spending, 2) AS average_monthly_spending,
    CASE
        WHEN consistent_months = 12 AND months_with_orders = 12 THEN 'Consistent'
        ELSE 'Not Consistent'
    END AS consistency_flag
FROM
    customer_consistency
WHERE
    months_with_orders = 12
ORDER BY
    customer_name;

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
WITH monthly_spend AS (
    SELECT
        c.customer_id,
        c.customer_name,
        YEAR(o.order_date) AS yr,
        MONTH(o.order_date) AS mnth,
        SUM(o.amount) AS month_spending
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    WHERE o.order_date >= '2024-01-01'
      AND o.order_date < '2025-01-01'
    GROUP BY c.customer_id, c.customer_name, YEAR(o.order_date), MONTH(o.order_date)
),
avg_monthly_spend AS (
    SELECT
        customer_id,
        customer_name,
        AVG(month_spending) AS avg_spending,
        COUNT(*) AS active_months
    FROM monthly_spend
    GROUP BY customer_id, customer_name
),
consistency_check AS (
    SELECT
        ms.customer_id,
        ms.customer_name,
        a.avg_spending,
        ms.mnth,
        ms.month_spending,
        CASE
            WHEN ms.month_spending BETWEEN a.avg_spending * 0.8 AND a.avg_spending * 1.2
            THEN 1 ELSE 0
        END AS within_20pct
    FROM monthly_spend ms
    JOIN avg_monthly_spend a ON ms.customer_id = a.customer_id
)
SELECT
    ac.customer_name,
    ROUND(ac.avg_spending, 2) AS average_monthly_spending,
    CASE
        WHEN COUNT(cc.within_20pct) = 12
             AND SUM(cc.within_20pct) = 12
             AND ac.active_months = 12
        THEN 'YES'
        ELSE 'NO'
    END AS consistency_flag
FROM avg_monthly_spend ac
JOIN consistency_check cc ON ac.customer_id = cc.customer_id
GROUP BY ac.customer_id, ac.customer_name, ac.avg_spending, ac.active_months;

-- Sequel
NULL;

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