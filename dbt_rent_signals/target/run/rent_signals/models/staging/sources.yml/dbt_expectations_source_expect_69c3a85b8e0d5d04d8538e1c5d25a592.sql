
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
        select *
        from RENTS.DBT_DEV_test_failures.dbt_expectations_source_expect_69c3a85b8e0d5d04d8538e1c5d25a592
    
      
    ) dbt_internal_test