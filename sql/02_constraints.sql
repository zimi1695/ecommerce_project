USE ecommerce;

-- ============================================================
-- Foreign Keys for dimension / bridge tables
-- ============================================================

-- products -> categories
ALTER TABLE products
    ADD CONSTRAINT fk_products_category
    FOREIGN KEY (category_id)
    REFERENCES categories (category_id)
    ON UPDATE RESTRICT
    ON DELETE RESTRICT;

-- product_brands -> products
ALTER TABLE product_brands
    ADD CONSTRAINT fk_product_brands_product
    FOREIGN KEY (product_id)
    REFERENCES products (product_id)
    ON UPDATE RESTRICT
    ON DELETE RESTRICT;

-- product_brands -> brands
ALTER TABLE product_brands
    ADD CONSTRAINT fk_product_brands_brand
    FOREIGN KEY (brand_id)
    REFERENCES brands (brand_id)
    ON UPDATE RESTRICT
    ON DELETE RESTRICT;
