SELECT 
    product_id,
    product_name,
    price,
    stock_quantity
FROM Products
WHERE product_id NOT IN (
    SELECT DISTINCT product_id 
    FROM Order_Details
)
ORDER BY product_name;