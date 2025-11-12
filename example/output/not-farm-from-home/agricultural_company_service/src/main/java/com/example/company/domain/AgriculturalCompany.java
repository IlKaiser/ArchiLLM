package com.example.company.domain;

import javax.persistence.*;
import java.util.Objects;

@Entity
@Table(name = "agricultural_company")
public class AgriculturalCompany {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String name;

    // TODO: Add more aggregate fields as needed

    protected AgriculturalCompany() {
        // for JPA
    }

    public AgriculturalCompany(String name) {
        this.name = name;
    }

    public Long getId() {
        return id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    // TODO: Add aggregate business methods

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof AgriculturalCompany)) return false;
        AgriculturalCompany that = (AgriculturalCompany) o;
        return Objects.equals(id, that.id);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }
}