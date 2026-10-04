# Player images and NBA data licensing: what is free to use (Courtside)

Researched 2026-10-04 for the owner's questions (headshots, logos, paid licences, ads). **Not legal advice.** Prices are
search-snippet figures, **UNVERIFIED** until a provider quotes.

## What the app does today
`apps/web/src/features/players/format.ts` `headshotUrl` hotlinks `https://cdn.nba.com/headshots/nba/latest/260x190/<id>.png`.
No licence covers this. Fine for the owner's private use; not for a public or ad-supported product.

## Paid routes (UNVERIFIED prices from search snippets)
| Route | Notes | Reported price |
|---|---|---|
| Sportradar Images API | headshots, logos (NBA logos via AP), action shots | custom quote, about US$500 to 5,000+ a month |
| SportsDataIO commercial licence | licensed headshots (studio or cropped action photos); logos by sales agreement | about US$500 to 1,000+ a month, quoted |
| SportsDataIO Discovery Lab (hobby) | stats; not licensed for commercial redistribution | about US$99 a month (fantasy); free tier = last season |

Owner direction 2026-10-04: **no paid licensing for now.**

## Free alternative investigated: Wikimedia Commons (via Wikidata P18)
Method: a Wikidata query for basketball players with an NBA team and an image (P18), matched by normalised name to the
top 300 rows of the 2026-27 "All 9 cats" auction board; licence and year read from the Commons API (`extmetadata`).

| Result | Value |
|---|---|
| Top 50 / top 150 / top 260 (of 300 rows) with a Commons image | 21 / 70 / 116 (about 42 % to 47 %) |
| Licences on the 116 | CC BY-SA 2.0 (39), CC BY 2.0 (31), CC BY-SA 4.0 (30), CC BY 4.0 (11), CC BY 3.0 (3), CC0 (2) |
| Photo year | 2012 to 2026, most 2019 to 2023; 13 from 2024 or later |
| Not found in top 30 | 16, including SGA, Maxey, Barnes, Mitchell, Durant, Cunningham, Mobley |

Caveats: Wikidata P18 is a floor (some players have Commons photos not linked to Wikidata); name matching can miss
suffixes and accents; photos are mixed in age, crop and size.

**What the licences require**: commercial use is allowed (CC BY, CC BY-SA, CC0). Every CC BY / BY-SA image needs
attribution (author, licence, link to the file); BY-SA asks adaptations (a crop may count) to be shared alike. A copyright
licence does **not** clear personality or publicity rights, and does not cover NBA or team marks. Team logos are not an
option from Commons for this purpose.

**Verdict**: legal for a free or ad-supported app if attribution is kept per image, but only about 45 % coverage, uneven
quality and an attribution page to maintain. Recommended as an optional later task, not a launch requirement; the public
launch default is initials plus a team-colour chip.

## Policy implemented by DATA-039 and WEB-039
`DATA_LICENSE=personal` (default) keeps hotlinked headshots for the owner only and keeps sign-up closed to strangers; any
public launch needs `commercial` or the image-free presentation.
