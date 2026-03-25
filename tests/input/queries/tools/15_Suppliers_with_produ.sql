-- Suppliers with products in multiple price segments. Identify suppliers who provide products in at least 3 different price segments: Budget (<10), Mid-range (10-50), Premium (> 50). Show supplier name and count of products in each segment

-- SQLAI
SELECT
  s.supplier_name,
  SUM(CASE WHEN p.price < 10 THEN 1 ELSE 0 END) AS budget_count,
  SUM(CASE WHEN p.price >= 10 AND p.price <= 50 THEN 1 ELSE 0 END) AS mid_count,
  SUM(CASE WHEN p.price > 50 THEN 1 ELSE 0 END) AS premium_count
FROM suppliers s
JOIN products p ON p.supplier_id = s.supplier_id
WHERE p.price IS NOT NULL
GROUP BY s.supplier_id, s.supplier_name
HAVING
  (SUM(CASE WHEN p.price < 10 THEN 1 ELSE 0 END) > 0)
  + (SUM(CASE WHEN p.price >= 10 AND p.price <= 50 THEN 1 ELSE 0 END) > 0)
  + (SUM(CASE WHEN p.price > 50 THEN 1 ELSE 0 END) > 0) >= 3
ORDER BY s.supplier_name;

-- Text2SQL
SELECT
    s.supplier_id,
    s.supplier_name,
    SUM(CASE WHEN p.price < 10 THEN 1 ELSE 0 END) AS budget_products,
    SUM(CASE WHEN p.price >= 10 AND p.price <= 50 THEN 1 ELSE 0 END) AS midrange_products,
    SUM(CASE WHEN p.price > 50 THEN 1 ELSE 0 END) AS premium_products
FROM
    suppliers s
JOIN
    products p ON s.supplier_id = p.supplier_id
GROUP BY
    s.supplier_id, s.supplier_name
HAVING
    SUM(CASE WHEN p.price < 10 THEN 1 ELSE 0 END) > 0
    AND SUM(CASE WHEN p.price >= 10 AND p.price <= 50 THEN 1 ELSE 0 END) > 0
    AND SUM(CASE WHEN p.price > 50 THEN 1 ELSE 0 END) > 0
ORDER BY
    s.supplier_name

-- Chat2DB
WITH ProductSegments AS (
    SELECT 
        p.product_id,
        p.supplier_id,
        CASE 
            WHEN p.price < 10 THEN 'Budget'
            WHEN p.price BETWEEN 10 AND 50 THEN 'Mid-range'
            ELSE 'Premium'
        END AS price_segment
    FROM 
        products p
),
SupplierSegmentCounts AS (
    SELECT 
        ps.supplier_id,
        ps.price_segment,
        COUNT(ps.product_id) AS product_count
    FROM 
        ProductSegments ps
    GROUP BY 
        ps.supplier_id, ps.price_segment
),
SupplierSegmentSummary AS (
    SELECT 
        ssc.supplier_id,
        COUNT(ssc.price_segment) AS segment_count,
        GROUP_CONCAT(ssc.price_segment ORDER BY ssc.price_segment) AS segments
    FROM 
        SupplierSegmentCounts ssc
    GROUP BY 
        ssc.supplier_id
    HAVING 
        COUNT(ssc.price_segment) >= 3
),
FinalResult AS (
    SELECT 
        s.supplier_name,
        ssc.price_segment,
        ssc.product_count
    FROM 
        SupplierSegmentCounts ssc
    JOIN 
        SupplierSegmentSummary sss ON ssc.supplier_id = sss.supplier_id
    JOIN 
        suppliers s ON ssc.supplier_id = s.supplier_id
)
SELECT 
    fr.supplier_name,
    SUM(CASE WHEN fr.price_segment = 'Budget' THEN fr.product_count ELSE 0 END) AS budget_count,
    SUM(CASE WHEN fr.price_segment = 'Mid-range' THEN fr.product_count ELSE 0 END) AS mid_range_count,
    SUM(CASE WHEN fr.price_segment = 'Premium' THEN fr.product_count ELSE 0 END) AS premium_count
FROM 
    FinalResult fr
GROUP BY 
    fr.supplier_name
ORDER BY 
    fr.supplier_name;

-- AI2sql
SELECT
    s.supplier_name,
    SUM(CASE WHEN p.price < 10 THEN 1 ELSE 0 END) AS budget_count,
    SUM(CASE WHEN p.price BETWEEN 10 AND 50 THEN 1 ELSE 0 END) AS midrange_count,
    SUM(CASE WHEN p.price > 50 THEN 1 ELSE 0 END) AS premium_count
FROM
    suppliers s
    JOIN products p ON s.supplier_id = p.supplier_id
GROUP BY
    s.supplier_id, s.supplier_name
HAVING
    (SUM(CASE WHEN p.price < 10 THEN 1 ELSE 0 END) > 0) +
    (SUM(CASE WHEN p.price BETWEEN 10 AND 50 THEN 1 ELSE 0 END) > 0) +
    (SUM(CASE WHEN p.price > 50 THEN 1 ELSE 0 END) > 0) >= 3;

-- Sequel
NULL;

-- Vanna
NULL;

-- AskYourDatabase
SELECT 
    s.supplier_id,
    s.supplier_name,
    s.contact_person,
    s.email,
    SUM(CASE WHEN p.price < 10 THEN 1 ELSE 0 END) as budget_products,
    SUM(CASE WHEN p.price >= 10 AND p.price <= 50 THEN 1 ELSE 0 END) as midrange_products,
    SUM(CASE WHEN p.price > 50 THEN 1 ELSE 0 END) as premium_products,
    COUNT(DISTINCT CASE 
        WHEN p.price < 10 THEN 'Budget'
        WHEN p.price >= 10 AND p.price <= 50 THEN 'Mid-range'
        WHEN p.price > 50 THEN 'Premium'
    END) as segments_count
FROM suppliers s
JOIN products p ON s.supplier_id = p.supplier_id
GROUP BY s.supplier_id, s.supplier_name, s.contact_person, s.email
HAVING COUNT(DISTINCT CASE 
    WHEN p.price < 10 THEN 'Budget'
    WHEN p.price >= 10 AND p.price <= 50 THEN 'Mid-range'
    WHEN p.price > 50 THEN 'Premium'
END) >= 3
ORDER BY premium_products DESC, midrange_products DESC, budget_products DESC;

-- MyQuery
SELECT 
    S.SUPPLIER_NAME,
    SUM(P.PRICE < 10) AS budget_products,
    SUM(P.PRICE BETWEEN 10 AND 50) AS midrange_products,
    SUM(P.PRICE > 50) AS premium_products,
    COUNT(*) AS total_products
FROM SUPPLIERS S
JOIN PRODUCTS P ON S.SUPPLIER_ID = P.SUPPLIER_ID
GROUP BY S.SUPPLIER_ID, S.SUPPLIER_NAME
HAVING COUNT(DISTINCT CASE 
    WHEN P.PRICE < 10 THEN 1
    WHEN P.PRICE BETWEEN 10 AND 50 THEN 2
    WHEN P.PRICE > 50 THEN 3
END) >= 3
ORDER BY total_products DESC;