-- Product sales across categories with supplier info For each category, show: Category name, total products, total sales quantity, and the main supplier

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
WITH category_supplier_sales AS (
    SELECT
        c.category_id,
        c.category_name,
        s.supplier_id,
        s.supplier_name,
        COUNT(DISTINCT p.product_id) AS products_supplied,
        IFNULL(SUM(od.quantity), 0) AS total_sales_quantity,
        ROW_NUMBER() OVER (
            PARTITION BY c.category_id
            ORDER BY IFNULL(SUM(od.quantity), 0) DESC
        ) AS rn
    FROM
        categories c
    LEFT JOIN
        products p ON c.category_id = p.category_id
    LEFT JOIN
        suppliers s ON p.supplier_id = s.supplier_id
    LEFT JOIN
        order_details od ON p.product_id = od.product_id
    GROUP BY
        c.category_id, c.category_name, s.supplier_id, s.supplier_name
),
category_totals AS (
    SELECT
        c.category_id,
        COUNT(DISTINCT p.product_id) AS total_products,
        IFNULL(SUM(od.quantity), 0) AS total_sales_quantity
    FROM
        categories c
    LEFT JOIN
        products p ON c.category_id = p.category_id
    LEFT JOIN
        order_details od ON p.product_id = od.product_id
    GROUP BY
        c.category_id
)
SELECT
    ct.category_id,
    cs.category_name,
    ct.total_products,
    ct.total_sales_quantity,
    cs.supplier_name AS main_supplier
FROM
    category_totals ct
JOIN
    category_supplier_sales cs
    ON ct.category_id = cs.category_id AND cs.rn = 1
ORDER BY
    cs.category_name;

-- Chat2DB
WITH CategorySales AS (
    SELECT 
        p.category_id,
        c.category_name,
        COUNT(DISTINCT p.product_id) AS total_products,
        SUM(od.quantity) AS total_sales_quantity
    FROM 
        products p
    JOIN 
        categories c ON p.category_id = c.category_id
    LEFT JOIN 
        order_details od ON p.product_id = od.product_id
    GROUP BY 
        p.category_id, c.category_name
),
MainSupplier AS (
    SELECT 
        p.category_id,
        s.supplier_id,
        s.supplier_name,
        COUNT(p.product_id) AS product_count,
        ROW_NUMBER() OVER (PARTITION BY p.category_id ORDER BY COUNT(p.product_id) DESC) AS rn
    FROM 
        products p
    JOIN 
        suppliers s ON p.supplier_id = s.supplier_id
    GROUP BY 
        p.category_id, s.supplier_id, s.supplier_name
)
SELECT 
    cs.category_name,
    cs.total_products,
    cs.total_sales_quantity,
    ms.supplier_name AS main_supplier
FROM 
    CategorySales cs
LEFT JOIN 
    MainSupplier ms ON cs.category_id = ms.category_id AND ms.rn = 1
ORDER BY 
    cs.category_name;

-- AI2sql
SELECT
    c.category_name,
    COUNT(DISTINCT p.product_id) AS total_products,
    SUM(od.quantity) AS total_sales_quantity,
    s.supplier_name AS main_supplier
FROM
    categories c
    JOIN products p ON c.category_id = p.category_id
    LEFT JOIN order_details od ON p.product_id = od.product_id
    LEFT JOIN (
        SELECT
            p2.category_id,
            p2.supplier_id,
            COUNT(*) AS product_count
        FROM
            products p2
        GROUP BY
            p2.category_id, p2.supplier_id
    ) pc ON c.category_id = pc.category_id
    LEFT JOIN suppliers s ON pc.supplier_id = s.supplier_id
WHERE
    pc.product_count = (
        SELECT
            MAX(pc2.product_count)
        FROM (
            SELECT
                p3.supplier_id,
                COUNT(*) AS product_count
            FROM
                products p3
            WHERE
                p3.category_id = c.category_id
            GROUP BY
                p3.supplier_id
        ) pc2
    )
GROUP BY
    c.category_id, s.supplier_id;

-- Sequel
SELECT
  c.category_name,
  COUNT(DISTINCT p.product_id) as total_products,
  COALESCE(SUM(od.quantity), 0) as total_sales_quantity,
  (
    SELECT
      s.supplier_name
    FROM
      supermarket.products p2
      JOIN supermarket.suppliers s ON p2.supplier_id = s.supplier_id
      JOIN supermarket.order_details od2 ON p2.product_id = od2.product_id
    WHERE
      p2.category_id = c.category_id
    GROUP BY
      s.supplier_id,
      s.supplier_name
    ORDER BY
      SUM(od2.quantity) DESC
    LIMIT
      1
  ) as main_supplier
FROM
  supermarket.categories c
  LEFT JOIN supermarket.products p ON c.category_id = p.category_id
  LEFT JOIN supermarket.order_details od ON p.product_id = od.product_id
GROUP BY
  c.category_id,
  c.category_name
ORDER BY
  total_sales_quantity DESC;

-- Vanna
NULL;

-- AskYourDatabase
SELECT 
    c.category_name,
    COUNT(DISTINCT p.product_id) as total_products,
    COALESCE(SUM(od.quantity), 0) as total_sales_quantity,
    main_supplier.supplier_name as main_supplier
FROM categories c
LEFT JOIN products p ON c.category_id = p.category_id
LEFT JOIN order_details od ON p.product_id = od.product_id
LEFT JOIN (
    SELECT 
        p2.category_id,
        s.supplier_name,
        s.supplier_id,
        COUNT(p2.product_id) as supplier_products,
        ROW_NUMBER() OVER (PARTITION BY p2.category_id ORDER BY COUNT(p2.product_id) DESC) as rn
    FROM products p2
    JOIN suppliers s ON p2.supplier_id = s.supplier_id
    GROUP BY p2.category_id, s.supplier_name, s.supplier_id
) as main_supplier ON c.category_id = main_supplier.category_id AND main_supplier.rn = 1
GROUP BY c.category_name, main_supplier.supplier_name
ORDER BY total_sales_quantity DESC;