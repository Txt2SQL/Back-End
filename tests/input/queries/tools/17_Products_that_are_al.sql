-- Products that are always sold together (co-purchased 100% of the time). Find pairs of products where whenever product A is purchased, product B is also in the same order, and vice versa (bidirectional relationship). Show product pairs and the number of times they appear together

-- SQLAI
WITH prod_orders AS (
  SELECT product_id, COUNT(DISTINCT order_id) AS total_orders
  FROM order_details
  GROUP BY product_id
)
SELECT
  od1.product_id AS product_a_id,
  pA.product_name  AS product_a_name,
  od2.product_id AS product_b_id,
  pB.product_name  AS product_b_name,
  COUNT(DISTINCT od1.order_id) AS together_count
FROM order_details od1
JOIN order_details od2
  ON od1.order_id = od2.order_id
  AND od1.product_id < od2.product_id
JOIN prod_orders pa ON pa.product_id = od1.product_id
JOIN prod_orders pb ON pb.product_id = od2.product_id
JOIN products pA ON pA.product_id = od1.product_id
JOIN products pB ON pB.product_id = od2.product_id
GROUP BY od1.product_id, od2.product_id, pA.product_name, pB.product_name
HAVING COUNT(DISTINCT od1.order_id) = pa.total_orders
   AND COUNT(DISTINCT od1.order_id) = pb.total_orders
ORDER BY together_count DESC;

-- Text2SQL
WITH product_orders AS (
    SELECT
        od.product_id,
        od.order_id
    FROM
        order_details od
),
product_pairs AS (
    SELECT
        po1.product_id AS product_a,
        po2.product_id AS product_b,
        po1.order_id
    FROM
        product_orders po1
    JOIN
        product_orders po2 ON po1.order_id = po2.order_id AND po1.product_id < po2.product_id
),
pair_counts AS (
    SELECT
        pp.product_a,
        pp.product_b,
        COUNT(*) AS times_together
    FROM
        product_pairs pp
    GROUP BY
        pp.product_a, pp.product_b
),
product_a_orders AS (
    SELECT
        product_id AS product_a,
        COUNT(DISTINCT order_id) AS orders_with_a
    FROM
        product_orders
    GROUP BY
        product_id
),
product_b_orders AS (
    SELECT
        product_id AS product_b,
        COUNT(DISTINCT order_id) AS orders_with_b
    FROM
        product_orders
    GROUP BY
        product_id
)
SELECT
    pa.product_name AS product_a_name,
    pb.product_name AS product_b_name,
    pc.times_together
FROM
    pair_counts pc
JOIN
    product_a_orders pao ON pc.product_a = pao.product_a
JOIN
    product_b_orders pbo ON pc.product_b = pbo.product_b
JOIN
    products pa ON pc.product_a = pa.product_id
JOIN
    products pb ON pc.product_b = pb.product_id
WHERE
    pc.times_together = pao.orders_with_a
    AND pc.times_together = pbo.orders_with_b
ORDER BY
    pc.times_together DESC, product_a_name, product_b_name

-- Chat2DB
WITH ProductPairs AS (
    SELECT 
        od1.product_id AS product_id_1,
        od2.product_id AS product_id_2,
        COUNT(*) AS pair_count
    FROM 
        order_details od1
    JOIN 
        order_details od2 ON od1.order_id = od2.order_id AND od1.product_id < od2.product_id
    GROUP BY 
        od1.product_id, od2.product_id
),
ProductOrders AS (
    SELECT 
        product_id,
        COUNT(DISTINCT order_id) AS order_count
    FROM 
        order_details
    GROUP BY 
        product_id
),
BidirectionalPairs AS (
    SELECT 
        pp.product_id_1,
        pp.product_id_2,
        pp.pair_count,
        po1.order_count AS product_1_order_count,
        po2.order_count AS product_2_order_count
    FROM 
        ProductPairs pp
    JOIN 
        ProductOrders po1 ON pp.product_id_1 = po1.product_id
    JOIN 
        ProductOrders po2 ON pp.product_id_2 = po2.product_id
    WHERE 
        pp.pair_count = po1.order_count AND pp.pair_count = po2.order_count
),
ProductNames AS (
    SELECT 
        product_id,
        product_name
    FROM 
        products
)
SELECT 
    pn1.product_name AS product_name_1,
    pn2.product_name AS product_name_2,
    bp.pair_count
FROM 
    BidirectionalPairs bp
JOIN 
    ProductNames pn1 ON bp.product_id_1 = pn1.product_id
JOIN 
    ProductNames pn2 ON bp.product_id_2 = pn2.product_id
ORDER BY 
    bp.pair_count DESC;

-- AI2sql
WITH ProductPairs AS (
    SELECT
        LEAST(oi1.product_id, oi2.product_id) AS product_id_1,
        GREATEST(oi1.product_id, oi2.product_id) AS product_id_2,
        oi1.order_id
    FROM
        order_items oi1
        JOIN order_items oi2 ON oi1.order_id = oi2.order_id AND oi1.product_id < oi2.product_id
),
PairCounts AS (
    SELECT
        product_id_1,
        product_id_2,
        COUNT(*) AS together_count
    FROM
        ProductPairs
    GROUP BY
        product_id_1,
        product_id_2
),
ProductOrderCounts AS (
    SELECT
        product_id,
        COUNT(DISTINCT order_id) AS order_count
    FROM
        order_items
    GROUP BY
        product_id
)
SELECT
    pc.product_id_1,
    pc.product_id_2,
    pc.together_count
FROM
    PairCounts pc
    JOIN ProductOrderCounts p1 ON pc.product_id_1 = p1.product_id
    JOIN ProductOrderCounts p2 ON pc.product_id_2 = p2.product_id
WHERE
    pc.together_count = p1.order_count
    AND pc.together_count = p2.order_count
ORDER BY
    pc.together_count DESC, pc.product_id_1, pc.product_id_2;

-- Sequel
WITH product_orders AS (
	SELECT DISTINCT 
		od.`order_id`, 
		od.`product_id` 
	FROM supermarket.order_details od
), 
product_pair_counts AS (
	SELECT 
		po1.`product_id` AS `product_a_id`, 
		po2.`product_id` AS `product_b_id`, 
		COUNT(DISTINCT po1.`order_id`) AS `times_together` 
	FROM product_orders po1 
	INNER JOIN product_orders po2 ON po1.`order_id` = po2.`order_id` AND po1.`product_id` < po2.`product_id` 
	GROUP BY po1.`product_id`, po2.`product_id`
), 
individual_product_counts AS (
	SELECT 
		`product_id`, 
		COUNT(DISTINCT `order_id`) AS `total_orders` 
	FROM product_orders 
	GROUP BY `product_id`
) 
SELECT 
	pa.`product_name` AS Product A, 
	pb.`product_name` AS Product B, 
	ppc.`times_together` AS Times Purchased Together, 
	ipa.`total_orders` AS Product A Total Orders, 
	ipb.`total_orders` AS Product B Total Orders
FROM product_pair_counts ppc 
INNER JOIN individual_product_counts ipa ON ppc.`product_a_id` = ipa.`product_id` 
INNER JOIN individual_product_counts ipb ON ppc.`product_b_id` = ipb.`product_id` 
INNER JOIN supermarket.products pa ON ppc.`product_a_id` = pa.`product_id` 
INNER JOIN supermarket.products pb ON ppc.`product_b_id` = pb.`product_id` 
WHERE ppc.`times_together` = ipa.`total_orders` AND ppc.`times_together` = ipb.`total_orders` AND ppc.`times_together` > 1 
ORDER BY ppc.`times_together` DESC ;

-- Vanna
NULL;

-- AskYourDatabase
WITH product_order_counts AS (
    SELECT 
        od.product_id,
        COUNT(DISTINCT o.order_id) as total_orders
    FROM orders o
    JOIN order_details od ON o.order_id = od.order_id
    GROUP BY od.product_id
),
product_pairs AS (
    SELECT 
        od1.product_id as product_id_1,
        od2.product_id as product_id_2,
        COUNT(DISTINCT o.order_id) as together_count
    FROM orders o
    JOIN order_details od1 ON o.order_id = od1.order_id
    JOIN order_details od2 ON o.order_id = od2.order_id
    WHERE od1.product_id < od2.product_id
    GROUP BY od1.product_id, od2.product_id
)
SELECT 
    p1.product_name as product_a,
    p2.product_name as product_b,
    pp.together_count as times_together
FROM product_pairs pp
JOIN products p1 ON pp.product_id_1 = p1.product_id
JOIN products p2 ON pp.product_id_2 = p2.product_id
JOIN product_order_counts poc1 ON pp.product_id_1 = poc1.product_id
JOIN product_order_counts poc2 ON pp.product_id_2 = poc2.product_id
WHERE pp.together_count = poc1.total_orders
  AND pp.together_count = poc2.total_orders
ORDER BY pp.together_count DESC;