
CREATE INDEX product_title_index IF NOT EXISTS
FOR (p:Product)
ON (p.title);

CREATE INDEX product_category_index IF NOT EXISTS
FOR (c:Category)
ON (c.name);
CREATE INDEX product_title_index IF NOT EXISTS
FOR (p:Product)
ON (p.title);

CREATE INDEX product_category_index IF NOT EXISTS
FOR (c:Category)
ON (c.name);