{#- stats.nba.com payloads carry resultSets[0] = {headers: [...], rowSet: [[...], ...]}.
    nba_stats_rows(): latest snapshot per request key for an endpoint, exploded to one row per
    rowSet entry with `headers` and `vals` as ARRAY<STRING>. `result_set` picks another set
    (e.g. 1 = Coaches in commonteamroster, DATA-038).
    nba_stats_col(): one typed column looked up by header name, so a reordered payload
    still maps correctly. -#}
{% macro nba_stats_rows(endpoint, key_like=none, result_set=0) -%}
    select
        s.snapshot_key,
        s.observed_at,
        json_value_array(s.payload, '$.resultSets[{{ result_set }}].headers') as headers,
        json_value_array(r) as vals
    from (
        select *
        from {{ ref('stg_nba_stats__snapshots') }}
        where endpoint = '{{ endpoint }}'
        {%- if key_like %} and snapshot_key like '{{ key_like }}'{% endif %}
        qualify row_number() over (partition by snapshot_key order by observed_at desc) = 1
    ) as s,
    unnest(json_query_array(s.payload, '$.resultSets[{{ result_set }}].rowSet')) as r
{%- endmacro %}

{% macro nba_stats_col(header, type, alias) -%}
    safe_cast(
        vals[safe_offset((select off from unnest(headers) as h with offset as off where h = '{{ header }}'))]
        as {{ type }}
    ) as {{ alias }}
{%- endmacro %}
