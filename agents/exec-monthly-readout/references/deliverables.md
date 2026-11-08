# Deliverables when a slide or deck is sent for verification

Every time, both:

1. **PowerPoint** built from the user's own deck slide (unpack the uploaded .pptx; never rebuild from scratch):
   - slide 1 = corrected slide, paste-ready;
   - slide 2 = review copy: yellow cells/text = change vs the user's current slide, orange = needs the user's decision, title replaced with the legend.
   - Workflow: duplicate the slide with the pptx skill's `add_slide.py`, run `scripts/slide_patch.py spec.json` on each (clean, then `--review`), keep only those two slides, clean, re-zip, validate against the original, then render and look at both slides.
   - Recolor delta cells by sign (`delta_rows`), since a value that flipped sign otherwise keeps the old color.
2. **Excel workbook**, one per slide:
   - main tab laid out like the slide, every number a COUNTIFS/SUMIFS over detail tabs; only spend and other non-Salesforce inputs typed, in blue with a source comment;
   - a "slide text" helper line under delta rows in the slide's own format ("-20 | -63%");
   - detail tabs with every record behind the numbers;
   - a "Funnel Text" tab when the slide has bullets: counts plus paste-ready sentences built with formulas;
   - a "Deck vs Live" tab: deck value (typed), live value (linked), delta, and the named record or reason for each move;
   - decision switches (for example the attribution rule) as a data-validated input cell that drives the formulas;
   - recalculate with zero errors, read the values back, and flip each switch once to prove it works.

The reply leads with what to change on the slide, then what verified exactly, then anything needing a decision. Bridge every mismatch to a named record.
