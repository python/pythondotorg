-- Contract text may use Markdown formatting, but cannot load resources or run
-- raw output commands. These two LaTeX commands are owned by the template.
local template_latex = {
  ["\\newpage"] = true,
  ["\\pagenumbering{gobble}"] = true,
}

function Image(element)
  error("Contract documents cannot embed images or load external resources.")
end

local function restrict_raw(element)
  if element.format ~= "latex" or not template_latex[element.text] then
    error("Contract documents cannot contain raw output commands.")
  end
end

return {{Image = Image, RawBlock = restrict_raw, RawInline = restrict_raw}}
