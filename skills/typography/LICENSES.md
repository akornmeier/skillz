# Licensing and attribution

## Source

The rules, numbers, and CSS in this skill are condensed and rewritten from the Typography Handbook, web and print editions, read 2026-11-06:

- Site: https://typographyhandbook.com/ and https://typographyhandbook.com/print/
- Original: Typography Handbook by Kenneth Wang, https://github.com/KennethWangDotDev/TypographyHandbook
- License: MIT, per the notice the site ships (reproduced below)

The measure default is `30em`, not the handbook's `65ch`. Measured in Chromium on 2026-11-06 with English prose, `65ch` held 75–92 characters per line across eight common faces (Georgia, Times New Roman, system-ui, Helvetica, Arial, Charter, Palatino, Verdana), while `30em` held 58–74. The handbook's 45–75 and ideal-66 targets are unchanged.

The handbook lists veraPDF as a print preflight tool; veraPDF validates PDF/A and PDF/UA, not PDF/X, so this skill names it only for accessibility checks.

Where the handbook was internally inconsistent, this skill picks one value. It sets variable-font weights with `font-weight` instead of `font-variation-settings`. It states the contrast of its dark-mode color ranges (about 13–16:1) instead of a 10:1 target those ranges cannot meet. It also requires links to have a color as well as an underline, to agree with ui-rules. Added beyond the source: the characters-per-line estimate, the computed contrast values in the template, the fluid scale numbers, mirrored `@page :left/:right` margins, and the note that a browser's Save as PDF is not press-ready.

The site's `/resources` page (foundry, font, mockup, and stock-photo lists) is not included.

## MIT notice

```
The MIT License (MIT)

Copyright (c) 2016 Kenneth Wang

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

This notice is not legal advice.
