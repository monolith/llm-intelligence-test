# SOURCES

Fixed, offline-repeatable noise corpus: 24 public-domain prose excerpts (pre-1929 publications,
or pre-1929 English translations of older works), each a contiguous, verbatim passage of
~1,200 words (1,000-1,400) trimmed to a clean paragraph boundary at both ends. Fetched from
Project Gutenberg plain-text editions. n01-n12 are carried over unchanged from v2; n13-n24 are
new for v3.

| File | Work | Author | Year | Source URL | Word count |
|---|---|---|---|---|---|
| n01-origin-of-species.md | On the Origin of Species (Ch. III, "Struggle for Existence") | Charles Darwin | 1859 | https://www.gutenberg.org/cache/epub/1228/pg1228.txt | 1187 |
| n02-innocents-abroad.md | The Innocents Abroad (Ch. VIII, Tangier) | Mark Twain | 1869 | https://www.gutenberg.org/cache/epub/3176/pg3176.txt | 1125 |
| n03-on-liberty.md | On Liberty (Ch. II, "Of the Liberty of Thought and Discussion") | John Stuart Mill | 1859 | https://www.gutenberg.org/cache/epub/34901/pg34901.txt | 1020 |
| n04-economy-of-machinery.md | On the Economy of Machinery and Manufactures (Ch. 1) | Charles Babbage | 1832 | https://www.gutenberg.org/cache/epub/4238/pg4238.txt | 1185 |
| n05-federalist-no-10.md | The Federalist, No. 10 | James Madison | 1787 | https://www.gutenberg.org/cache/epub/1404/pg1404.txt | 1261 |
| n06-household-management.md | The Book of Household Management (Ch. I, "The Mistress") | Isabella Beeton | 1861 | https://www.gutenberg.org/cache/epub/10136/pg10136.txt | 1151 |
| n07-sense-and-sensibility.md | Sense and Sensibility (Ch. I) | Jane Austen | 1811 | https://www.gutenberg.org/cache/epub/161/pg161.txt | 1228 |
| n08-moby-dick.md | Moby-Dick (Ch. 1, "Loomings") | Herman Melville | 1851 | https://www.gutenberg.org/cache/epub/2701/pg2701.txt | 1218 |
| n09-tale-of-two-cities.md | A Tale of Two Cities (Book I, Ch. I, "The Period") | Charles Dickens | 1859 | https://www.gutenberg.org/cache/epub/98/pg98.txt | 1172 |
| n10-frankenstein.md | Frankenstein; or, The Modern Prometheus (Letter 1) | Mary Shelley | 1818 | https://www.gutenberg.org/cache/epub/84/pg84.txt | 1199 |
| n11-wealth-of-nations.md | An Inquiry into the Nature and Causes of the Wealth of Nations (Book I, Ch. IV, "Of the Origin and Use of Money") | Adam Smith | 1776 | https://www.gutenberg.org/cache/epub/3300/pg3300.txt | 1250 |
| n12-common-sense.md | Common Sense ("Of the Origin and Design of Government in General") | Thomas Paine | 1776 | https://www.gutenberg.org/cache/epub/147/pg147.txt | 1189 |
| n13-malay-archipelago.md | The Malay Archipelago (Preface) | Alfred Russel Wallace | 1869 | https://www.gutenberg.org/cache/epub/2530/pg2530.txt | 1315 |
| n14-two-years-before-the-mast.md | Two Years Before the Mast (Ch. I-II, "Departure" / "First Impressions") | Richard Henry Dana Jr. | 1840 | https://www.gutenberg.org/cache/epub/2055/pg2055.txt | 1295 |
| n15-principles-of-political-economy.md | On the Principles of Political Economy, and Taxation (Ch. I, "On Value") | David Ricardo | 1817 | https://www.gutenberg.org/cache/epub/33310/pg33310.txt | 1323 |
| n16-letters-to-his-son.md | Letters to His Son (Letter I) | Lord Chesterfield (Philip Dormer Stanhope) | 1774 | https://www.gutenberg.org/cache/epub/3361/pg3361.txt | 1389 |
| n17-american-womans-home.md | The American Woman's Home (Ch. I, "The Christian Family") | Catharine E. Beecher and Harriet Beecher Stowe | 1869 | https://www.gutenberg.org/cache/epub/6598/pg6598.txt | 1251 |
| n18-odyssey.md | The Odyssey (Book XVI, recognition of Ulysses) | Homer, trans. Samuel Butler | 1900 | https://www.gutenberg.org/cache/epub/1727/pg1727.txt | 1259 |
| n19-scarlet-letter.md | The Scarlet Letter (Ch. I-II, "The Prison-Door" / "The Market-Place") | Nathaniel Hawthorne | 1850 | https://www.gutenberg.org/cache/epub/33/pg33.txt | 1356 |
| n20-anna-karenina.md | Anna Karenina (Part One, Ch. 1) | Leo Tolstoy, trans. Constance Garnett | 1901 | https://www.gutenberg.org/cache/epub/1399/pg1399.txt | 1384 |
| n21-crime-and-punishment.md | Crime and Punishment (Part I, Ch. II) | Fyodor Dostoevsky, trans. Constance Garnett | 1914 | https://www.gutenberg.org/cache/epub/2554/pg2554.txt | 1293 |
| n22-count-of-monte-cristo.md | The Count of Monte Cristo (Ch. 1, "Marseilles-The Arrival") | Alexandre Dumas | 1844 | https://www.gutenberg.org/cache/epub/1184/pg1184.txt | 1244 |
| n23-moonstone.md | The Moonstone (Prologue, "The Storming of Seringapatam") | Wilkie Collins | 1868 | https://www.gutenberg.org/cache/epub/155/pg155.txt | 1351 |
| n24-meditations.md | Meditations (Book I) | Marcus Aurelius, trans. Meric Casaubon | 1634 | https://www.gutenberg.org/cache/epub/2680/pg2680.txt | 1317 |

## Notes on substitutions (v2, n01-n12)

Two initially-planned works were fetched successfully (HTTP 200) but rejected after inspection
because the specific Gutenberg edition was not clean contiguous prose:

- **Pride and Prejudice** (Gutenberg #1342) is the 1894 Hugh Thomson illustrated edition — dozens
  of `[Illustration: ...]` caption lines are interleaved throughout the running text, including
  inside Chapter I. Replaced with Jane Austen's **Sense and Sensibility** (Gutenberg #161), which
  has no illustration captions in the excerpted chapter.
- **The History of the Decline and Fall of the Roman Empire** (Gutenberg #731, the
  Milman/Guizot/Smith annotated edition) interleaves full footnote blocks — "1 (return) [ ... ]"
  — directly inside chapter text, breaking narrative continuity. Replaced with Thomas Paine's
  **Common Sense** (Gutenberg #147) for the legal/historical-document/political-pamphlet slot.

## Notes on substitutions (v3, n13-n24)

- **Alfred Russel Wallace's "My Life: A Record of Events and Opinions"** (1905), the first choice
  for the scientific-memoir slot, has no plain-text edition on Project Gutenberg (not catalogued).
  Substituted with Wallace's **The Malay Archipelago** (Gutenberg #2530), whose Preface is itself
  a first-person scientific memoir recounting his eight years of specimen-collecting.
- **Thomas Henry Huxley's "Autobiography and Selected Essays"** (Gutenberg #1315) was fetched
  (HTTP 200) but rejected: it is an annotated school edition with bracketed inline footnote
  reference numbers scattered through the running text of the autobiography itself (e.g.
  "the pre-Boswellian [2] epoch"), with the corresponding note text collected 4,000+ lines later.
  Replaced by the Wallace substitution above.
- **The Odyssey, Gutenberg #28797** (an alternate scanned edition, sought as a possibly cleaner
  copy) returned HTTP 404. Used Gutenberg #1727 (Samuel Butler's prose translation) instead. This
  edition has ~150 inline endnote-reference numbers glued directly onto words throughout the body
  text (e.g. "the one looking West and the other East.1", "upon the sea,83"); the excerpted stretch
  (Book XVI) was located and hand-verified to fall in one of the edition's longest marker-free
  spans.
- **Fyodor Dostoevsky's "Crime and Punishment," Part I, Chapter I** (the famous opening,
  "...walked slowly, as though in hesitation, towards K. bridge") was passed over because its
  second sentence names a bridge as the chapter's destination and recurring setting. Used Chapter
  II (the tavern scene) instead, which has no such mention.

All 24 final files were verified to contain no `[Illustration]`, `[Footnote]`, or inline
footnote-reference markup, and no passages *about* bridges, railroads, viaducts, mills, weirs,
bells, orchards, ledgers, or village histories as subject matter.
