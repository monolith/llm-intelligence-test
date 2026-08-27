# SOURCES

Fixed, offline-repeatable noise corpus: 12 public-domain prose excerpts (pre-1929 publications),
each a contiguous, verbatim passage of ~1,200 words trimmed to a clean paragraph boundary.
Fetched from Project Gutenberg plain-text editions.

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

## Notes on substitutions

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

All 12 final files were verified to contain no `[Illustration]`, `[Footnote]`, or inline
`(return) [...]` markup, and no mentions of ledgers, weirs, bells, orchards, mills, or village
histories as subject matter.
