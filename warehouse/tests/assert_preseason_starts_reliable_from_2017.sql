-- DATA-030: starts are usable (non-null) from 2017-18 on and missing before (box-score quality).
select season
from {{ ref('int_preseason_role') }}
group by season
having (season >= '2017-18' and countif(pre_start_share is not null) = 0)
    or (season < '2017-18' and countif(pre_start_share is not null) > 0)
