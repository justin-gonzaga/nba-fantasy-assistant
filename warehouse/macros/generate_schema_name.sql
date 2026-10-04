{#- Layer datasets are named exactly after the layer (staging, intermediate, marts) in dev/prod,
    because each environment is its own project. The ci target prefixes them per PR
    (ci_pr12_staging) so parallel PRs never collide (INFRA-002). -#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- set layer = custom_schema_name if custom_schema_name is not none else target.schema -%}
    {%- if target.name == 'ci' -%}
        {{ target.schema }}_{{ layer | trim }}
    {%- else -%}
        {{ layer | trim }}
    {%- endif -%}
{%- endmacro %}
