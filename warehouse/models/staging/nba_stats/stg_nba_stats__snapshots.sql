-- One row per raw stats.nba.com snapshot file (sidecars excluded), with its capture metadata
-- parsed from the path: raw/nba_stats/<endpoint>/<key>/<observed_at>.json
{%- set endpoints = ['leaguegamelog', 'leaguedashplayerstats', 'commonteamroster', 'drafthistory', 'boxscoretraditionalv3', 'leaguedashteamstats'] %}

with files as (
    {%- for ep in endpoints %}
    select
        '{{ ep }}' as endpoint,
        _FILE_NAME as file_uri,
        payload
    from {{ source('nba_stats', 'nba_stats__' ~ ep) }}
    where not ends_with(_FILE_NAME, '.meta.json')
    {% if not loop.last %}union all{% endif %}
    {%- endfor %}
)

select
    endpoint,
    regexp_extract(file_uri, r'/raw/nba_stats/[^/]+/(.+)/[^/]+\.json$') as snapshot_key,
    parse_timestamp(
        '%Y%m%dT%H%M%E6S',
        regexp_replace(regexp_extract(file_uri, r'/(\d{8}T\d{12})Z\.json$'), r'(\d{6})(\d{6})$', r'\1.\2')
    ) as observed_at,
    file_uri,
    payload
from files
