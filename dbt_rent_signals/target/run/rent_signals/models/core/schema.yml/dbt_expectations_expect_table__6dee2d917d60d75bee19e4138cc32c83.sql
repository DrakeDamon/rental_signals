
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
        select *
        from RENTS.DBT_DEV_test_failures.dbt_expectations_expect_table__6dee2d917d60d75bee19e4138cc32c83
    
      
    ) dbt_internal_test