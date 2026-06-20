# Task Plot Prompt

Create a clean scientific task-flow timeline diagram only.

Leave the top 25% of the image blank for a later fixed header, title, subtitle, and logo overlay. Do not draw any title, subtitle, logo, watermark, or branding.

Task: Transitive Inference Task.

Draw three horizontal timeline rows:

1. Training premise pairs
2. Final test premise pairs
3. Final test probes

Use compact screen thumbnails connected by arrows. Use a white background, crisp dark labels, and restrained accent colors. Make row labels left aligned. Keep all text legible and inside the timeline.

Training premise row phases:

- Fixation, 400 ms: fixation cross.
- Pair display, 3000 ms: two simple symbol glyphs or abstract letters side by side; show keys `Z=left` and `M=right`.
- Training feedback, 800 ms: Correct / Incorrect / Too slow.
- ITI, 400 ms: fixation cross.

Final test premise row phases:

- Fixation, 400 ms.
- Pair display, 3000 ms: adjacent learned pairs AB / BC / CD / DE; show keys `Z=left` and `M=right`.
- No feedback.
- ITI, 400 ms.

Final test probe row phases:

- Fixation, 400 ms.
- Pair display, 3000 ms: BD transitive probe or AE anchor probe; show keys `Z=left` and `M=right`.
- No feedback.
- ITI, 400 ms.

Add a small note near the training row: 4 training blocks, repeat until 80% premise-pair criterion, max 3 attempts. Add a small note near the test rows: final test mixes premise, BD, and AE probes.

Do not include file names or implementation details.
