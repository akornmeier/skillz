# Print and PDF typography

Rules for type on paper and in PDFs. The same (default) and firm convention as SKILL.md applies. Hierarchy, proximity, and measure carry over from the web rules unchanged.

## Contents

- [How print differs](#how-print-differs)
- [The page](#the-page)
- [Setting type](#setting-type)
- [Micro-typography](#micro-typography)
- [Production](#production)
- [PDF](#pdf)
- [Printing from the browser](#printing-from-the-browser)

## How print differs

- The page is fixed and nothing reflows, so every line break, page break, widow, and orphan is yours to control. Control them.
- Units are absolute: points (1pt = 1/72in), picas (12pt), millimetres. One CSS px is 0.75pt.
- Paper resolves finer detail than screens, so print tolerates smaller sizes, lighter weights, and true hairlines.
- Ink and paper are typographic variables; the same face behaves differently on coated stock and newsprint.

## The page

- Fix the format first; margins, grid, and type size all derive from it. A4 is 210 × 297mm; US Letter is 8.5 × 11in; trade paperbacks run near 129 × 198mm or 135 × 216mm. For commercial print, confirm the format against the printer's press sheets early.
- Margins grow inner < top < outer < bottom. The Van de Graaf canon (page in ninths, margins 2:3:4:6) is the classical start; on A4 that is inner 23.3, top 33, outer 46.7, bottom 66mm. Keep the progression; rarely use the literal values. (default)
- Design bound documents as mirrored spreads. Add 5–10mm of inner margin for a perfect binding; the spine eats it.
- Single-sided documents can use equal side margins; keep the bottom larger than the top. (default)
- Derive the grid from the type: body size and leading first, a baseline grid at that leading, then columns with a gutter of one baseline unit, then modular fields. Books need one or two columns; magazines and catalogues six or twelve. Body text locks to the baseline grid; headings, captions, and images take whole multiples of it. (default)

## Setting type

- Prefer faces designed for print, at their intended sizes. Use optical sizes when the family has them: text cuts for roughly 8–14pt, display cuts for 24pt and up. Never set a display cut at text size or a text cut at display size.
- Before committing to a face, check the character set: small caps, oldstyle and tabular figures, fractions, every language the job needs. Print has no fallback font. Check the desktop and PDF-embedding licence separately from any web licence.
- Body 9.5–11.5pt, 10 or 10.5pt as the workhorse; captions 7.5–8.5pt; footnotes 8pt. Judge by x-height, not the number. Nothing meant to be read goes below 6pt. (default, except the 6pt floor)
- Write leading as size/leading ("10.5/14" is 10.5pt type on 14pt baselines). Text wants 2–4pt above the type size (120–135%); longer measures and larger x-heights want more; display sizes tighten toward solid. The leading sets the baseline grid. (default)
- Measure 45–75 characters, 66 ideal; 40–50 per column in multi-column work. Measure, size, and leading are one decision: proof the combination on paper.
- Justify only with hyphenation and a paragraph composer (InDesign's Adobe Paragraph Composer, TeX). Word spacing about 85% minimum, 100% desired, 115% maximum; letterspacing near zero; at most two consecutive hyphenated lines; never hyphenate a paragraph's last word or across a page turn. (default)
- Set narrow measures and captions ragged right, and keep the rag free of shapes and stranded short words. Browsers justify line by line, so print stylesheets stay ragged right. (default)
- Fix widows (a last line stranded at the top of a page) and orphans (a first line stranded at the bottom) by editing the text, tracking, or breaks.

## Micro-typography

These apply on screen too; print just makes every slip visible.

- Track capitals and small caps 5–10% of the size (CSS `letter-spacing: 0.05em`–`0.1em`). Never track lowercase.
- Use true small caps for abbreviations in running text (`font-variant-caps: all-small-caps`), never scaled-down capitals.
- Oldstyle figures in running text (`font-variant-numeric: oldstyle-nums`), lining figures with capitals, tabular figures in tables (`tabular-nums`).
- Real quotation marks and apostrophes. En dash for ranges; em dash, or spaced en dash, for a break in thought. One space after a full stop.
- Hang punctuation into the margin so the text edge reads optically flush (InDesign: Optical Margin Alignment).
- Standard ligatures (fi, fl) always on.

## Production

- Presses print CMYK, whose gamut is smaller than RGB: saturated blues, greens, and oranges dull. Proof colour-critical work on paper.
- Body text is 100K black only (C0 M0 Y0 K100), set to overprint. Four-colour black misregisters into coloured fringes at text sizes. Never use registration black (100/100/100/100) for design.
- Rich black (for example C60 M40 Y40 K100) is for large solid areas only, within the printer's total ink limit.
- Use a spot colour (Pantone) for brand colour on stationery and covers: consistent, outside the CMYK gamut, immune to misregistration. (default)
- Uncoated stock and newsprint spread ink: go slightly larger, choose sturdier faces with open counters, and avoid hairlines. Reversed (white-on-colour) type stays at 8pt or more, medium weight, without fine serifs, and is never reversed out of four-colour black on uncoated stock. Proof on the actual stock.
- Anything that touches the page edge extends 3mm (1/8in in the US) past the trim as bleed. Keep text and critical marks 3–5mm inside the trim.
- Raster images need about 300ppi at printed size. Keep type and logos vector to the press; never rasterize text.

## PDF

- Export PDF/X-4 unless the printer asks for PDF/X-1a. Ask for the printer's export preset or spec and match it; don't invent their limits. (default)
- Embed every font. Subsetting is fine for final output; embed complete fonts only if someone will edit the file downstream. Outline text only as a last resort; outlines kill search, accessibility, and fine rendering.
- Preflight before sending (InDesign or Acrobat) and confirm the trim and bleed boxes survived export. Until a preflight passes, the file is not print-ready; say so.
- Tag PDFs that people will read on screen: heading structure, reading order, alt text, real text. PDF/UA is the accessibility standard; the open-source veraPDF validates it (not PDF/X).
- A browser's "Save as PDF" is RGB, not PDF/X, and has no bleed: fine for office printers and screen reading, not for a press. For commercial print, convert and preflight to the printer's spec with text black coming out 100K, or hand the printer the source.

## Printing from the browser

Specify print styles in pt and mm; on paper they finally mean something.

```css
@media print {
  @page {
    size: A4;                  /* or 210mm 297mm, letter, A5 */
    margin: 20mm 18mm 28mm;    /* single-sided: top, equal sides, bottom largest */
  }
  /* Bound document: uncomment these to replace the margin above with mirrored pages
     (top, inner, bottom, outer on :left; top, outer, bottom, inner on :right).
     Visible margins grow inner < top < outer < bottom, and the inner one also carries
     the 5–10mm the binding swallows (here 15 + 7mm). Check your engine supports them.
  @page :left  { margin: 20mm 22mm 30mm 25mm; }
  @page :right { margin: 20mm 25mm 30mm 22mm; }
  */

  body { font-size: 10.5pt; line-height: 14pt; color: #000; text-align: start; }
  h1, h2, h3, h4 { line-height: 1.15; } /* the fixed 14pt would inherit and overlap wrapped headings */

  h2, h3 { break-after: avoid; }               /* no heading stranded at a page foot */
  figure, table, pre { break-inside: avoid; }
  p { orphans: 2; widows: 2; }
  table { font-variant-numeric: tabular-nums; }

  nav, .site-header, .back-to-top { display: none; }
  a[href^="http"]::after { content: " (" attr(href) ")"; font-size: 0.85em; } /* a printed link shows its URL */
}
```

For running heads, page numbers, and generated tables of contents from HTML, use Paged.js, which polyfills CSS Paged Media.
