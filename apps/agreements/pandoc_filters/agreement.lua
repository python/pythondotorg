-- Layout and safety for agreement documents.
--   ::: sub        third-level clauses: indented in DOCX/PDF, a styled div in HTML
--   ::: pagebreak  hard page break in DOCX/PDF, dropped in HTML
-- Documents may be written by PSF staff, so they cannot embed images: pandoc would fetch them.

local function is_paged()
  return FORMAT == "docx" or FORMAT == "latex" or FORMAT == "pdf"
end

function Image(element)
  error("Agreement documents cannot embed images or load external resources.")
end

function Div(el)
  if el.classes:includes("pagebreak") then
    if FORMAT == "docx" then
      return pandoc.RawBlock("openxml", '<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
    elseif is_paged() then
      return pandoc.RawBlock("latex", "\\newpage")
    end
    return {}
  end
  if el.classes:includes("sub") and is_paged() then
    return pandoc.BlockQuote(el.content)
  end
end
