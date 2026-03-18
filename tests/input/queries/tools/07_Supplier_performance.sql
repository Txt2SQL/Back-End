-- Supplier performance analysis. For each supplier, show: Total products supplied, total quantity sold, and total revenue generated, Include suppliers with no sales

-- SQLAI
SELECT
  s.supplier_id,
  s.supplier_name,
  COALESCE(p_cnt.total_products, 0)       AS total_products_supplied,
  COALESCE(sales_agg.total_quantity, 0)   AS total_quantity_sold,
  COALESCE(sales_agg.total_revenue, 0.00) AS total_revenue
FROM suppliers s
LEFT JOIN (
  SELECT supplier_id, COUNT(*) AS total_products
  FROM products
  GROUP BY supplier_id
) p_cnt ON p_cnt.supplier_id = s.supplier_id
LEFT JOIN (
  SELECT p.supplier_id,
         SUM(od.quantity) AS total_quantity,
         SUM(od.quantity * od.unit_price) AS total_revenue
  FROM order_details od
  JOIN products p ON od.product_id = p.product_id
  GROUP BY p.supplier_id
) sales_agg ON sales_agg.supplier_id = s.supplier_id
ORDER BY total_revenue DESC;

-- Text2SQL
SELECT
    s.supplier_id,
    s.supplier_name,
    COUNT(DISTINCT p.product_id) AS total_products_supplied,
    IFNULL(SUM(od.quantity), 0) AS total_quantity_sold,
    IFNULL(SUM(od.quantity * od.unit_price), 0) AS total_revenue_generated
FROM
    suppliers s
LEFT JOIN
    products p ON s.supplier_id = p.supplier_id
LEFT JOIN
    order_details od ON p.product_id = od.product_id
GROUP BY
    s.supplier_id, s.supplier_name
ORDER BY
    s.supplier_id;

-- Chat2DB
SELECT 
    s.supplier_id,
    s.supplier_name,
    COUNT(DISTINCT p.product_id) AS total_products_supplied,
    COALESCE(SUM(od.quantity), 0) AS total_quantity_sold,
    COALESCE(SUM(od.quantity * od.unit_price), 0) AS total_revenue_generated
FROM 
    suppliers s
LEFT JOIN 
    products p ON s.supplier_id = p.supplier_id
LEFT JOIN 
    order_details od ON p.product_id = od.product_id
GROUP BY 
    s.supplier_id, s.supplier_name
ORDER BY 
    s.supplier_id;

-- AI2sql
SELECT
    s.supplier_id,
    s.supplier_name,
    COUNT(DISTINCT p.product_id) AS total_products_supplied,
    IFNULL(SUM(oi.quantity), 0) AS total_quantity_sold,
    IFNULL(SUM(oi.quantity * oi.unit_price), 0) AS total_revenue_generated
FROM
    suppliers s
    LEFT JOIN products p ON s.supplier_id = p.supplier_id
    LEFT JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY
    s.supplier_id, s.supplier_name;

-- Sequel
SELECT
  COUNT(supplier_id) AS total_suppliers,
  SUM(
    CASE
      WHEN total_revenue > 0 THEN 1
      ELSE 0
    END
  ) AS active_suppliers,
  SUM(
    CASE
      WHEN total_revenue = 0 THEN 1
      ELSE 0
    END
  ) AS inactive_suppliers,
  ROUND(
    AVG(
      CASE
        WHEN total_revenue > 0 THEN total_revenue
      END
    ),
    2
  ) AS avg_revenue,
  MAX(total_revenue) AS max_revenue
FROM
  (
    SELECT
      s.supplier_id,
      COALESCE(SUM(od.quantity * od.unit_price), 0) AS total_revenue
    FROM
      suppliers s
      LEFT JOIN products p ON s.supplier_id = p.supplier_id
      LEFT JOIN order_details od ON p.product_id = od.product_id
    GROUP BY
      s.supplier_id
  ) AS stats;

-- Vanna
SELECT 
    s.supplier_id, 
    s.supplier_name, 
    COUNT(DISTINCT p.product_id) as total_products_supplied, 
    SUM(COALESCE(od.quantity, 0)) as total_quantity_sold, 
    ROUND(SUM(COALESCE(od.quantity * od.unit_price, 0)), 2) as total_revenue_generated 
FROM suppliers s 
LEFT JOIN products p ON s.supplier_id = p.supplier_id 
LEFT JOIN order_details od ON p.product_id = od.product_id 
GROUP BY s.supplier_id, s.supplier_name 
ORDER BY total_revenue_generated DESC, s.supplier_name;

-- AskYourDatabase
SELECT 
    s.supplier_id,
    s.supplier_name,
    s.contact_person,
    s.email,
    COUNT(DISTINCT p.product_id) as total_products_supplied,
    COALESCE(SUM(od.quantity), 0) as total_quantity_sold,
    COALESCE(SUM(od.quantity * od.unit_price), 0) as total_revenue
FROM suppliers s
LEFT JOIN products p ON s.supplier_id = p.supplier_id
LEFT JOIN order_details od ON p.product_id = od.product_id
GROUP BY s.supplier_id, s.supplier_name, s.contact_person, s.email
ORDER BY total_revenue DESC;

-- MyQuery

SELECT 
    S.SUPPLIER_ID,
    S.SUPPLIER_NAME,
    S.CONTACT_PERSON,
    S.PHONE,
    S.EMAIL,
    COUNT(DISTINCT P.PRODUCT_ID) AS total_products_supplied,
    COALESCE(SUM(OD.QUANTITY), 0) AS total_quantity_sold,
    COALESCE(SUM(OD.QUANTITY * OD.UNIT_PRICE), 0) AS total_revenue,
    COUNT(DISTINCT OD.ORDER_ID) AS total_orders_with_products
FROM SUPPLIERS S
    JOIN PRODUCTS P ON S.SUPPLIER_ID = P.SUPPLIER_ID
    JOIN ORDER_DETAILS OD ON P.PRODUCT_ID = OD.PRODUCT_ID
GROUP BY 
    S.SUPPLIER_ID,
    S.SUPPLIER_NAME,
    S.CONTACT_PERSON,
    S.PHONE,
    S.EMAIL
ORDER BY total_revenue DESC, S.SUPPLIER_NAME;