package com.example;

public class StringUtils {

    /**
     * Возвращает строку с заглавной первой буквой.
     */
    public String capitalize(String input) {
        if (input == null || input.isEmpty()) return input;
        return input.substring(0,1).toUpperCase() + input.substring(1);
    }

    /**
     * Переворачивает строку задом наперёд.
     */
    public String reverse(String input) {
        return new StringBuilder(input).reverse().toString();
    }
}