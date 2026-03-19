package com.gasstation.test.model;

public class TestCase {
    private String id;
    private String criterion;
    private String name;
    private String description;

    public TestCase() {}

    public TestCase(String id, String criterion, String name, String description) {
        this.id = id;
        this.criterion = criterion;
        this.name = name;
        this.description = description;
    }

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public String getCriterion() { return criterion; }
    public void setCriterion(String criterion) { this.criterion = criterion; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
}
