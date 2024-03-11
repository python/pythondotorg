#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
# Source: https://github.com/pandocker/pandoc-docx-pagebreak-py/
# Revision: c8cddccebb78af75168da000a3d6ac09349bef73
# ------------------------------------------------------------------------------
# MIT License
# 
# Copyright (c) 2018 pandocker
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ------------------------------------------------------------------------------

""" pandoc-docx-pagebreakpy
Pandoc filter to insert pagebreak as openxml RawBlock
Only for docx output

Trying to port pandoc-doc-pagebreak
- https://github.com/alexstoick/pandoc-docx-pagebreak
"""

import panflute as pf


class DocxPagebreak(object):
    pagebreak = pf.RawBlock("<w:p><w:r><w:br w:type=\"page\" /></w:r></w:p>", format="openxml")
    sectionbreak = pf.RawBlock("<w:p><w:pPr><w:sectPr><w:type w:val=\"nextPage\" /></w:sectPr></w:pPr></w:p>",
                               format="openxml")
    toc = pf.RawBlock(r"""
<w:sdt>
    <w:sdtContent xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
        <w:p>
            <w:r>
                <w:fldChar w:fldCharType="begin" w:dirty="true" />
                <w:instrText xml:space="preserve">TOC \o "1-3" \h \z \u</w:instrText>
                <w:fldChar w:fldCharType="separate" />
                <w:fldChar w:fldCharType="end" />
            </w:r>
        </w:p>
    </w:sdtContent>
</w:sdt>
""", format="openxml")

    def action(self, elem, doc):
        if isinstance(elem, pf.RawBlock):
            if elem.text == r"\newpage":
                if (doc.format == "docx"):
                    elem = self.pagebreak
            # elif elem.text == r"\newsection":
            #     if (doc.format == "docx"):
            #         pf.debug("Section Break")
            #         elem = self.sectionbreak
            #     else:
            #         elem = []
            elif elem.text == r"\toc":
                if (doc.format == "docx"):
                    pf.debug("Table of Contents")
                    para = [pf.Para(pf.Str("Table"), pf.Space(), pf.Str("of"), pf.Space(), pf.Str("Contents"))]
                    div = pf.Div(*para, attributes={"custom-style": "TOC Heading"})
                    elem = [div, self.toc]
                else:
                    elem = []
        return elem


def main(doc=None):
    dp = DocxPagebreak()
    return pf.run_filter(dp.action, doc=doc)


if __name__ == "__main__":
    main()
