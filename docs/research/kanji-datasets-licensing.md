# Kanji datasets: can a commercial JLPT kanji trainer use them? (licensing research)

Researched 2026-10-04 (all URLs accessed that day). **Not legal advice.** Product assumed: paid and/or ad-supported app sold to
individuals in the US and Australia.

Method note: pages were read through a fetch tool that returns summaries, so quotes below are as returned by the tool, not
checked against raw HTML. VERIFIED = a primary page (project, licence body, government) was fetched and says this.
UNVERIFIED = secondary source, search snippet, or primary page not retrievable. Confidence: High = primary and unambiguous,
Medium = primary but summarised or ambiguous scope, Low = secondary only.

## 1. The two licence families that matter

| Licence | Commercial use | Attribution | Share-alike |
|---|---|---|---|
| CC BY 2.0 FR / 2.5 / 3.0 / 4.0 | yes | credit author/source, link licence | none |
| CC BY-SA 3.0 (KanjiVG) | yes | credit author, link licence, keep notices | adaptations only under BY-SA 3.0 (or later/compatible jurisdiction port). A work merely placed in a "Collection" is not an adaptation (legal code s.1, VERIFIED) |
| CC BY-SA 4.0 (EDRDG, Wikipedia, Kanjium) | yes | credit, link licence, **indicate changes**, keep notices | "Adapted Material" must be BY-SA 4.0 or compatible. 4.0 also treats a database that includes a substantial part of a licensed database as adapted material (s.4, VERIFIED via summary) |

Sources: https://creativecommons.org/licenses/by-sa/3.0/legalcode and https://creativecommons.org/licenses/by-sa/4.0/legalcode
(VERIFIED, High for the definitions; Medium for how they apply to a merged product database).
CC's own wiki: "The ShareAlike condition applies only for works considered adaptations under copyright law, not simply in
collections with other works" (https://wiki.creativecommons.org/wiki/ShareAlike_interpretation, VERIFIED, Medium).

Practical reading (not legal advice): share-alike attaches to the licensed **data and anything derived from that data** (for
example your kanji table that copies or merges KANJIDIC2 fields), not automatically to unrelated app code. No primary source
I could reach states this for the EDRDG licence specifically. A web search summary asserted "application code need not be open
source" but the page it came from was not identified, so treat as UNVERIFIED (Low). Lawyer question 1.

## 2. Source-by-source

### 2.1 EDRDG files: KANJIDIC2, JMdict, JMnedict/ENAMDICT, RADKFILE/KRADFILE
- Contains: KANJIDIC2 = XML with 13,108 kanji (JIS X 0208/0212/0213): readings, meanings, stroke count, grade, freq,
  old-JLPT level, dictionary indexes. JMdict = multilingual word dictionary (incl. priority tags). JMnedict = proper names.
  KRADFILE/RADKFILE = kanji-to-component decomposition (6,355 JIS X 0208 kanji; extended RADKFILE2/KRADFILE2 for 5,801 more,
  copyright of Jim Rose, same licence). VERIFIED:
  https://www.edrdg.org/wiki/KANJIDIC_Project.html, https://www.edrdg.org/krad/kradinf.html,
  https://www.edrdg.org/enamdict/enamdict_doc.html
- Licence: Creative Commons Attribution-ShareAlike **4.0** as the EDRDG Licence Statement, copyright held by the
  Electronic Dictionary Research and Development Group (Breen assigned copyright in March 2000).
  Licence page: https://www.edrdg.org/edrdg/licence.html (VERIFIED, High on version; Medium on exact wording because the page
  was read via summary). The page lists JMdict, EDICT, ENAMDICT, COMPDIC, KANJIDIC2, KANJIDIC, KANJD212, RADKFILE/KRADFILE as covered.
- Commercial use: **yes.** Quote: "provided the conditions above are met, there is NO restriction placed on commercial use of
  the files. The files can be bundled with software and sold for whatever the developer wants to charge." (VERIFIED)
- Attribution (conditions on software/apps): acknowledge usage and source "in the documentation, publicity material, WWW site of
  the package/server, etc."; provide copies of, or links to, the documentation and licence files (local copy or the Monash/EDRDG
  location). For apps the page points to an About / Sources screen; for web displays of dictionary content, acknowledgement on
  each page. (VERIFIED, Medium: the per-screen wording came from a summary.)
- Share-alike: "If you alter, transform, or build upon this work, you may distribute the resulting work only under the same,
  similar or a compatible licence." The page does not define "work" or say whether an app or product database is a "resulting
  work". (VERIFIED text; scope UNCLEAR.)
- Extra EDRDG-specific conditions (not in plain CC BY-SA): (a) "there must be a procedure for regular updating of the data
  from the most recent versions available" for apps/servers using the files; (b) you must not claim copyright over EDRDG
  material; (c) no warranty. (VERIFIED, Medium.) Condition (a) is an extra restriction beyond CC BY-SA 4.0, so a lawyer should
  confirm it is enforceable and what a compliant "procedure" is for an offline app (e.g. update on each app release or a data
  sync). Donations are suggested for commercial use (not mandatory).
- Fields useful here, with limits:
  - `jlpt`: "The pre-2010 level of the Japanese Language Proficiency Test (JLPT) in which the kanji occurs (1-4)."
    (https://www.edrdg.org/wiki/KANJIDIC_Project.html, VERIFIED). It is **not** N5 to N1 (section 3).
  - `freq`: "The 2,501 most-used characters have a ranking ... based on an analysis of word frequencies in the Mainichi Shimbun over
    4 years by Alexandre Girardi" (same page, VERIFIED). Newspaper-biased; the tail is imprecise (legacy doc, UNVERIFIED wording).
    Rights in the underlying Mainichi text are not discussed by EDRDG: flagged for lawyer (Q4), but the data is a ranking, not text.
  - `grade`: G1-G6 elementary (1,026 kanji in the current doc), G8 secondary, G9-G10 name kanji (same page, VERIFIED).
    An older doc says "1006 Kanji" (https://www.edrdg.org/kanjidic/kanjidic_doc_legacy.html): the 2020 curriculum moved
    20 kanji down, so older mirrors differ. Check the file version you ship.
- Example sentences in JMdict/Tatoeba are separate (see 2.4).

### 2.2 KanjiVG (stroke order SVG)
- Contains: SVG stroke paths, stroke order, component groups, per kanji. Copyright Ulrich Apel.
- Licence: **CC BY-SA 3.0** ("KanjiVG is copyright Ulrich Apel and released under the Creative Commons Attribution-Share Alike
  3.0 licence", https://github.com/KanjiVG/kanjivg and https://kanjivg.tagaini.net/ ; licence text
  https://creativecommons.org/licenses/by-sa/3.0/legalcode). VERIFIED, High.
- Commercial: yes. Attribution: credit Ulrich Apel / KanjiVG, link the licence.
- Share-alike: applies to **adaptations of the SVGs** (edited paths, animated variants, converted/simplified files, a database
  built from them). Shipping them unmodified inside an app bundle is plausibly a Collection, not an adaptation (CC BY-SA 3.0 s.1,
  VERIFIED text; application to an app is Medium). Converting SVG to your own animation format is likely an adaptation: that
  derived asset set must be BY-SA 3.0. Note the 3.0 clause barring "effective technological measures" that restrict recipients
  (relevant to DRM and app-store wrappers: lawyer Q3).
- Unclear: BY-SA 3.0 is not one-way compatible with BY-SA 4.0 in the same way 4.0 is with GPLv3; merging KanjiVG-derived
  assets with BY-SA 4.0 data into one derived dataset needs a licence-compatibility opinion (Q2).

### 2.3 Tanos / Jonathan Waller JLPT lists (the "N5-N1" lists)
- Contains: vocabulary, kanji and grammar lists per N-level, as PDF/DOC/Anki/MEM; `(c) Jonathan Waller`, dated 2011 on the N5 page
  (http://www.tanos.co.uk/jlpt/jlpt5/, VERIFIED).
- Licence: "Everything on this site (that I'm not selling), is licenced under Creative Commons 'BY'. Basically this means ... use
  anything here however you like (commercial or non-commercial), but credit my site."
  (http://www.tanos.co.uk/jlpt/sharing/, VERIFIED, High.) The CC version is **not stated** on the page; downstream projects
  describe it as CC BY (Bluskyo/JLPT_Vocabulary: "licenced under Creative Commons 'BY' by Jonathan Waller", UNVERIFIED version).
  Attribution: credit Jonathan Waller and link tanos.co.uk/jlpt. No share-alike. Materials Waller sells are excluded (not relevant to the lists).
- Who maintains: Jonathan Waller (tanos.co.uk). The lists are a community reconstruction, not official (section 3).
  The method used to build the kanji list is not stated on pages I could fetch: UNVERIFIED.
- Data format: no official machine-readable download. Third-party conversions exist (Bluskyo/JLPT_Vocabulary JSON/CSV under
  MIT code but data still CC BY; Kanjium and Kanji-Dojo both use Waller data). A conversion's own licence must not be trusted
  over Waller's; re-derive from Waller's files or credit both.
- Open question: Waller's lists may themselves derive from the old official lists (copyright status of those unknown). UNVERIFIED (Q5).

### 2.4 Tatoeba sentences
- Contains: user-contributed sentence pairs, with per-sentence author; many Japanese/English pairs originate from the
  Tanaka Corpus (public domain per Tatoeba). Audio is separate.
- Licence: text **CC BY 2.0 FR**; a subset also **CC0 1.0**. Quote: "These files are released under CC BY 2.0 FR." and "A part of
  our sentences are also available under CC0 1.0." (https://tatoeba.org/en/downloads, VERIFIED, High.)
- Terms: attribution means citing the author of each sentence ("using, reusing, modifying and distributing the sentence is only
  allowed if the name of the author is cited", https://tatoeba.org/en/terms_of_use, VERIFIED). Per-sentence credit in-app is
  burdensome: use the CC0 subset, or a per-screen author line, or an in-app credits page listing authors if the licence allows
  it (lawyer Q5). Audio: licence is chosen by each contributor; if not stated, reuse outside Tatoeba is restricted. **Do not use
  Tatoeba audio** without per-file checks.
- No share-alike. Commercial use: yes.

### 2.5 Japanese government lists: Joyo kanji and grade (kyoiku kanji) table
- Contains: Joyo kanji table (2,136 kanji, cabinet notification of 30 Nov 2010) and the 学年別漢字配当表 (grade allocation) as PDFs
  on the Agency for Cultural Affairs site (https://www.bunka.go.jp/kokugo_nihongo/sisaku/joho/joho/kijun/naikaku/kanji/index.html,
  VERIFIED that both are hosted; no terms on that page).
- Copyright: Japan Copyright Act Art. 13 excludes "notifications, instructions, circular notices, and other similar materials
  issued by a national ... government agency" from copyright (https://www.japaneselawtranslation.go.jp/en/laws/view/3379/en,
  VERIFIED). A cabinet notification is plausibly in this class; whether the grade table (part of the curriculum guidelines) is also
  covered is UNVERIFIED. MEXT site terms: CC BY 4.0 compatible, cite "出典：文部科学省ホームページ（URL）", state if you edited, do not
  imply government authorship; third-party content excluded (https://www.mext.go.jp/b_menu/1351168.htm, VERIFIED for MEXT;
  the Agency for Cultural Affairs site's own terms were not retrieved: UNVERIFIED).
- Commercial: yes, with the MEXT-style source credit as a precaution. No share-alike.
- The kanji set itself (a list of characters) is a fact list; the risk is in the PDF text and any copied annotations.

### 2.6 Frequency and corpus sources
| Source | What / terms | Commercial | Status |
|---|---|---|---|
| Aozora Bunko (https://www.aozora.gr.jp/guide/kijyunn.html) | Public-domain Japanese literature; input files may be freely copied/redistributed "regardless of paid or free"; asks that metadata (title, author, input staff) be kept; in-copyright works are not reusable commercially. VERIFIED | yes for PD works | Good corpus for self-computed counts, but skewed to pre-1950 prose (old kanji/usage). Filter out in-copyright entries. |
| Scriptin kanji-frequency (https://github.com/scriptin/kanji-frequency) | Counts from Aozora, Japanese Wikipedia (100k articles, Jan 2023), Wikinews; data and code **CC BY 4.0**. VERIFIED licence label | yes, attribution | Derived from CC BY-SA Wikipedia text, yet licensed CC BY: whether pure character counts are an "adaptation" is a lawyer question (Q4). Wikinews text is CC BY 2.5. |
| Japanese Wikipedia dump | Dumps: GFDL and CC BY-SA 4.0 for original text; "use at your own risk". https://dumps.wikimedia.org/legal.html VERIFIED | yes, BY-SA | Text copying triggers BY-SA; counting kanji frequencies from it is generally treated as fact extraction but is not settled (Q4). Wiktionary frequency lists derived from Wikipedia are marked CC BY-SA (https://en.wiktionary.org/wiki/Wiktionary:Frequency_lists/Japanese, VERIFIED). |
| BCCWJ (NINJAL) (https://clrd.ninjal.ac.jp/bccwj/en/) | 100M-word balanced corpus. "Requests to use the corpus for commercial purposes are considered on an individual basis"; word/kanji frequency lists "free for use for research or educational purposes" (https://clrd.ninjal.ac.jp/bccwj/en/freq-list.html). VERIFIED | **No** without NINJAL contract (search summary: paid 2-year contract; UNVERIFIED) | Best frequency data, but excluded from a commercial app unless licensed. Use only to sanity-check own counts offline, if at all (even that needs a lawyer view). |
| Google Books Ngram | Data "may be freely used for any purpose"; compilation CC BY 3.0 (https://books.google.com/ngrams/info, https://storage.googleapis.com/books/ngrams/books/datasetsv3.html). VERIFIED | yes | **Japanese is not among the corpora** (English, Chinese simplified, French, German, Hebrew, Spanish, Russian, Italian). Not usable for Japanese. VERIFIED |
| Leeds CTS internet-jp frequency list (http://corpus.leeds.ac.uk/frqc/) | Word frequencies; secondary sources say CC BY 2.5 (and Kanji-Dojo lists it as CC BY). Page fetch failed. **UNVERIFIED** | likely yes | Word-level, web-biased; confirm licence page before use. |
| Kodansha / commercial kanji dictionaries | Proprietary ranking and dictionaries. Not fetched; copyright presumed. | no | Avoid. |
| Kanjium (https://github.com/mifunetoshiro/kanjium) | Aggregate database, **CC BY-SA 4.0** for the package; merges EDICT, KANJIDIC, KRADFILE, Tatoeba, Waller JLPT, frequency from Japanese Wikipedia and "over 5,000 novels"; embeds third-party items (fonts, chineseetymology.org images (c) Richard Sears) with their own terms. VERIFIED | yes, but it inherits every upstream condition | Convenient, but the "5,000 novels" frequency source is not licensed or even named. Prefer the upstreams to Kanjium. The whole package is BY-SA, so pulling it in makes your derived table BY-SA. |

Kyoiku/Joyo-based "grade" order and the newspaper `freq` from KANJIDIC2 give two frequency-ish orderings under the
EDRDG licence with no extra source. Self-computed Aozora + Wikipedia counts can fill in beyond rank 2,500.

## 3. JLPT levels: what exists and how old levels map

- The JLPT changed from 4 levels (1984-2009) to 5 levels (N1-N5) in 2010. Mapping (Wikipedia, secondary, UNVERIFIED primary):
  N1 slightly harder than old 1; N2 about old 2; N3 a new level between old 2 and old 3; N4 about old 3; N5 about old 4.
  https://en.wikipedia.org/wiki/Japanese-Language_Proficiency_Test
- Official lists: the JLPT FAQ states the "Test Content Specifications" (which held vocabulary/kanji/grammar lists) are not
  published for the new test, giving the reason "the ultimate goal of studying Japanese is to use the language to communicate rather
  than simply memorizing vocabulary, kanji and grammar items." (https://www.jlpt.jp/e/faq/, VERIFIED; the year 2010 and the old
  lists dated 1994/2004 come from Wikipedia, UNVERIFIED.) So **no official N5-N1 kanji list exists**; every N-level kanji list
  (Waller, Kanjium, apps) is unofficial. Marketing text must say "JLPT-aligned" or "based on commonly used study lists",
  never "official JLPT list".
- KANJIDIC2 `jlpt` is the old 1-4 scale (VERIFIED above). A public GitHub issue shows another commercial-style site mislabelled
  these as N levels: 一, 人, 日, 本, 学 showed "N4" when they should be N5; only 103 kanji carry the lowest level 4
  and none carry level 5 (https://github.com/serpcompany/zenbujapanese-monorepo/issues/485, secondary, UNVERIFIED counts).
  Mapping you can use: KANJIDIC2 4 to N5, 3 to N4. Old 2 and old 1 map to N2 and N1, but **N3 cannot be recovered** from the
  old scale (it sits inside old 2), so an open N3 boundary needs Waller's list or your own cut. Do not label KANJIDIC2
  levels as N-levels in the UI.
- JLPT name and logo: the JLPT site copyright is "The Japan Foundation / Japan Educational Exchanges and Services"; its site
  policy allows personal, educational and cited use, and requires prior written permission for other uses
  (https://www.jlpt.jp/e/policy.html, VERIFIED). No trademark guidance was found: UNVERIFIED. Use "JLPT" only descriptively, no
  logo, add "not affiliated" notice, and ask a lawyer about a nominative use in app-store titles (Q5).

## 4. Scheduling side: FSRS
- FSRS repo, py-fsrs (`fsrs` on PyPI) and ts-fsrs are all **MIT** (https://github.com/open-spaced-repetition/free-spaced-repetition-scheduler,
  .../py-fsrs, .../ts-fsrs; VERIFIED licence labels). ts-fsrs implements FSRS v6. Commercial use: yes. Obligation: keep the MIT
  copyright notice and licence text in distributions; no share-alike. Any other FSRS port (Swift, Dart, Rust ...) needs its own
  licence check (UNVERIFIED). Algorithm ideas are not licensed separately here (patents: not researched, UNVERIFIED).

## 5. How existing apps comply (evidence)
- **Kanji Dojo** (syt0r, https://github.com/syt0r/Kanji-Dojo, VERIFIED, repo archived 2026-08-27): GPL-3.0 app listing KanjiVG
  (BY-SA 3.0), KANJIDIC (listed as BY-SA 3.0, though EDRDG's current licence is 4.0), Tanos (CC BY), JMdict and JmdictFurigana
  (BY-SA 4.0), Leeds list (CC BY), yomichan-jlpt-vocab (BY-SA 4.0). Distributed on Google Play, App Store and F-Droid. It complies
  by being open source, so it shows the attribution page pattern but **not** that a closed-source commercial app is fine.
  (Also, GPLv3 vs CC BY-SA 3.0 compatibility is itself disputed; not our problem if we stay closed.)
- Kanjium: re-releases everything as CC BY-SA 4.0 and credits upstreams (above).
- I found no verified public statement from a closed-source commercial app on how it satisfies the EDRDG share-alike clause.
  Could not confirm either way: UNVERIFIED.

## 6. Summary table

| Source | Licence (version) | Commercial | Attribution | Share-alike scope | Status |
|---|---|---|---|---|---|
| KANJIDIC2 | EDRDG = CC BY-SA 4.0 + extra conditions | yes | About/Sources screen + links to docs/licence | derived data "under same/similar/compatible licence"; extra "regular updating" duty | conditions, lawyer Q1, Q2 |
| JMdict / JMnedict | same | yes | same | same | conditions |
| KRADFILE/RADKFILE | same (RADKFILE2 (c) Jim Rose, same licence) | yes | same | same | conditions |
| KanjiVG | CC BY-SA 3.0 | yes | credit Ulrich Apel, link licence | adaptations of the SVGs; a plain bundle is likely a Collection | conditions, Q3 |
| Tanos JLPT lists | CC "BY" (version unstated) | yes | credit Jonathan Waller + site link | none | attribution only (version caveat) |
| Tatoeba sentences | CC BY 2.0 FR; part CC0 1.0 | yes | author of each sentence | none | attribution only; CC0 subset easiest; no audio |
| Joyo + grade table | Art. 13 Copyright Act (notification); MEXT CC BY 4.0-compatible | yes | source credit | none | likely attribution only |
| Aozora Bunko (PD works) | public domain, reuse terms | yes | keep metadata (requested) | none | attribution only |
| Scriptin frequency | CC BY 4.0 (derived from BY-SA Wikipedia) | yes | credit author | none claimed | lawyer Q4 |
| JA Wikipedia / Wiktionary lists | CC BY-SA 4.0 (+GFDL) | yes | credit, indicate changes | text copying only; counting unsettled | Q4 |
| BCCWJ | research/education free; commercial by contract | no | n/a | n/a | avoid |
| Google Books Ngram | CC BY 3.0 compilation | yes | link requested | none | no Japanese data |
| Leeds JP list | CC BY 2.5? (UNVERIFIED) | likely | cite | none | verify |
| Kanjium | CC BY-SA 4.0 aggregate | with upstream terms | all upstreams | whole package BY-SA | avoid; use upstreams |
| FSRS (ts-fsrs, py-fsrs) | MIT | yes | keep licence notice | none | safe |

## 7. Recommended stacks

**A. Safe stack (attribution only, no share-alike on your data):**
1. Kanji set and grade: Joyo list + 学年別漢字配当表 (government; cite MEXT/Agency for Cultural Affairs).
2. Level labels: Waller (tanos) N5-N1 kanji lists, CC BY (credit; confirm CC version in writing).
3. Frequency: your own counts from Aozora Bunko public-domain texts (keep metadata; exclude in-copyright works), plus a
   documented, hand-checked Wikinews/other CC BY corpus if you want modern usage. Do not copy Wikipedia text, only use counts after lawyer OK.
4. Sentences: Tatoeba CC0 1.0 subset (no author credit) or CC BY 2.0 FR with a credits page; no audio.
5. Scheduling: FSRS (MIT).

**B. Conditions stack (usable, but share-alike and extra obligations; get legal sign-off before launch):**
- KANJIDIC2 readings/meanings, KRADFILE components, JMdict words, KanjiVG strokes. These are the practical data for "readings,
  meanings, stroke order, example words". Isolate them in a separate, clearly licensed data package (EDRDG data as BY-SA 4.0;
  KanjiVG derivatives as BY-SA 3.0) with provenance per field, keep the app code, quiz logic, learner model and your own content
  in a separate repository/database, and ship an About/Sources screen plus an update procedure.

**Avoid / pay or ask:** BCCWJ and any NINJAL data (commercial contract), Kodansha lists, Kanjium as a whole, Tatoeba audio,
Leeds list until its licence is confirmed, JLPT logo or "official" claims, any Wikipedia text copy.

## 8. Open questions for a lawyer (US and Australia)
1. **Share-alike scope under the EDRDG licence.** If KANJIDIC2/JMdict fields are loaded into the product database next to our own
   content (difficulty scores, distractors, mnemonics, learner statistics), which parts must be BY-SA 4.0: just the EDRDG-derived
   columns, the whole table, or the whole database? Does the app code stay proprietary? Is a separate store with a join key enough?
2. **EDRDG extra conditions and licence mixing.** Is the "regular updating" duty and the "do not claim copyright" clause
   enforceable on top of CC BY-SA 4.0, and how to satisfy it for an offline app? Can BY-SA 4.0 (EDRDG), BY-SA 3.0 (KanjiVG) and CC BY
   data be combined into one derived dataset, given the licences are not mutually one-way compatible (3.0 to 4.0)?
3. **App stores and DRM.** Do store terms, DRM, or paywalls conflict with the BY-SA bar on technical measures restricting
   recipients' rights, for the data (not the code)? Does shipping SVGs unmodified in an app bundle count as a Collection?
4. **Counted data derived from copyrighted or BY-SA text** (Mainichi-derived `freq`, Wikipedia-derived counts, Scriptin's
   CC BY labelling): are aggregate character frequencies an adaptation in US and Australian law, and what do Japanese
   law and the Wikipedia licence say about text and data analysis? (Sui generis database rights exist in the EU, not in the US/AU;
   sale outside US/AU would need a separate view. UNVERIFIED.)
5. **Provenance and branding.** Are Waller's lists derived from the old official JLPT lists whose rights are unclear? May the app
   say "JLPT N5-N1" in its name and store listing (descriptive/nominative use), and is a per-sentence Tatoeba author credit
   needed on screen, or does a credits page meet CC BY 2.0 FR?

## 9. Suggested follow-ups (spikes)
- Spike 1: email EDRDG (the contact address on the EDRDG licence page) and Jonathan Waller to ask in writing: (a) EDRDG on share-alike
  scope for a product database; (b) Waller on CC version and provenance of the kanji lists. Cheap, and answers Q1, Q2, Q5.
- Spike 2: diff KANJIDIC2 `jlpt` (old) against Waller's N5-N1 lists to document the mapping empirically (N5 vs old 4, etc.).
- Spike 3: compute Aozora-only kanji frequency, compare its ranks with KANJIDIC2 `freq` for the top 2,500 kanji; record rank
  correlation to decide if modern-usage supplement is needed.
- Retrieve (not done): the Leeds licence page, the Agency for Cultural Affairs terms, the BCCWJ manual's licence text, and the full
  raw text of the EDRDG licence page.
