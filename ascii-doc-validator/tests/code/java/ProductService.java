package com.example.services;

import com.example.models.Product;
import java.util.*;

public class ProductService {
    private List<Product> products = new ArrayList<>();

    public void addProduct(Product p) {
        products.add(p);
    }

    public boolean removeProduct(String sku) {
        return products.removeIf(p -> p.getSku().equals(sku));
    }
}