package com.example.controllers;

import com.example.models.User;
import java.util.*;

public class UserController {
    private Map<Long, User> db = new HashMap<>();

    public User getUser(Long id) {
        return db.get(id);
    }

    public void createUser(Long id, String name) {
        db.put(id, new User(id, name));
    }
}