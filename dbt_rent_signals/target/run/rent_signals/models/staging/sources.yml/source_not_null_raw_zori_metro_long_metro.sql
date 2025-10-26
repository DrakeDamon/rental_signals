
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
        select *
        from RENTS.DBT_DEV_test_failures.source_not_null_raw_zori_metro_long_metro
    
      
    ) dbt_internal_test