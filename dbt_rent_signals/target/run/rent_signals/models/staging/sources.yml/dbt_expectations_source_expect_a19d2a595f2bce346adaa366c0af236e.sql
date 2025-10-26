
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
        select *
        from RENTS.DBT_DEV_test_failures.dbt_expectations_source_expect_a19d2a595f2bce346adaa366c0af236e
    
      
    ) dbt_internal_test