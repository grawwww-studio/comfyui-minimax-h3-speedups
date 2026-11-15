# Eye table (subjective, from frames; not a second metric)

One reader, 30 clips, six frames each. The strip images are not in this repo.

## Method (shown as written)
1. Blind pass. For each shot x seed (6 strips) the same 6 frames from the 5 headline settings (base20, lx8, lx4, pika6, hyper6): frames 10, 29, 46, 67, 86, 140 (0.42, 1.21, 1.92, 2.79, 3.58, 5.83 s). Frame 29 is the open-vowel mouth (it sits at the loudest stretch of the audio guide, ~1.9-2.1 s, and the mouth is open on it in every clip), frame 140 is the last frame. Rows shuffled per strip, letters only. The key was not opened, nor the metrics file, until the blind notes below were written. lx8s12 and base20_rig were not in the blind pass (report-only settings).
2. Judged on: identity against the character sheet (green eyes, dense freckles, bangs/hairline, face shape, cheek mole), mouth and teeth, earrings (pearl drop + hoop, ear cuff), skin texture, motion artefacts across the 6 frames.
3. Unblinded, joined with the face number (R1 mean per clip), then picked moments.
Strips (not published): face = tight crop, zoom = 1:1 crop of frames 29 and 140, full = whole frame, one blind and one labelled version per shot and seed.
What this is: one reader looking at stills of 6 moments per clip. Not judged: motion at speed, audio, lip-sync timing, anything between the 6 frames.

## Blind notes (plain words, written before unblinding)
- All 30 clips read as the same woman: copper bangs, green eyes, freckles, pearl drops, mole. At full-frame strip size I could not tell the settings apart without hunting; the differences below show only on the enlarged face crops.
- Skin/freckles are what moves: some rows have denser, crisper freckles and sharper eyes at the last frame, others a smoother, younger, softer face with a narrower look.
- Mouths: open vowel and teeth look plausible in every row; no melted teeth, no wrong lip shape. Earrings: pearl drop and hoop present in every row; I cannot tell the rows apart on them.
- Motion in the 6 frames: no smear, flicker or frozen patch seen.
- Two things that are not about the face: (1) one wide clip has a pampas-grass plume and a dark object added at the right edge in all frames; (2) in wide 4103 and 1766580932 some rows are framed larger (face bigger, shoulders in view). The framing differences are real and visible in the strips.

## Unblinded: eye position (1 = looked most like the sheet, of 5) with the R1 mean of the same clip
| strip | base20 | lx8 | lx4 | pika6 | hyper6 |
|---|---|---|---|---|---|
| wide 5207 | 1 (0.558) | 2 (0.546) | 4 (0.534) | 5 (0.535) | 3 (0.593, min 0.144) |
| wide 4103 | 3 (0.586) | 4 (0.520) | 1 (0.533) | 5 (0.553) | 2 (0.557) |
| wide 1766580932 | 3 (0.559) | 4 (0.553) | 1 (0.534) | 5 (0.522) | 2 (0.576) |
| close 5207 | 4 (0.546) | 1 (0.588) | 2 (0.557) | 5 (0.562) | 3 (0.585) |
| close 4103 | 5 (0.539) | 2 (0.560) | 1 (0.570) | 4 (0.555) | 3 (0.541) |
| close 1766580932 | 2 (0.561) | 4 (0.564) | 1 (0.569) | 5 (0.568) | 3 (0.595) |
| mean eye position | 3.0 | 2.8 | 1.7 | 4.8 | 2.7 |
Rules from `results.json`: wide line 0.540 (base mean 0.568, band 0.558-0.586), close line 0.521 (base mean 0.549, band 0.539-0.561). Verdicts: lx8, hyper6, base20 kept on both shots; lx4 and pika6 fail wide (all three seeds under the base's lowest) and keep close.

## Where the eye agrees and disagrees with the number
- base20: nothing to compare (it is the line). Eye puts it mid-pack (3.0).
- lx8 (kept both): agrees. Eye puts it level with base (2.8 vs 3.0); the one failing clip, wide 4103 (0.520), is also 4th by eye, but only by a little.
- hyper6 (kept both): agrees. Eye 2.7, level with base. The metric's odd clip, wide 5207 (mean 0.593 but min 0.144), is explained by the eye: its first ~0.4 s are framed wrongly (head cut at the forehead, body and jeans in view, 0.00-0.25 s), then it settles by frame ~12; base20 does not do this. A viewer sees that at normal size.
- lx4 (fails wide, keeps close): the eye disagrees on wide. I put lx4 first or second in 5 of 6 strips, including two of the three wide ones (4th on wide 5207); I see the same woman, with dense freckles. The number says all three wide seeds sit under the base's lowest (0.533-0.534 against 0.558). What I see does not support calling it a different face. Seen at normal size the difference is not visible; I cannot name a feature that moved.
- pika6 (fails wide, keeps close): the eye puts it last in 5 of 6 strips (4th in the sixth), so it agrees with the wide fail in direction. On close it disagrees with the number (0.555-0.568, level with or above base). What the eye sees is softer freckles and a smoother, narrower-looking face at the last frame, visible only on enlarged crops. Still her.
- Overall: the eye's top pick matches the metric's top clip in only 2 of 6 strips (close 5207, close 4103). Gaps between settings are too small to see at normal viewing size; they show on enlarged face crops (wide shot: face is ~200 px tall, so crops are the only way). The strongest differences are not identity: the hyper6 opening framing, the pampas plume in lx8 wide 1766580932, and the larger framing of some wide clips.


## Moments worth looking at (clip, timecode, what to look at, crop box in 1344x768)
Clear to a viewer:
1. hyper6, wide, seed 5207, 0.00-0.50 s (frames 0-12): the first half second is framed wrong (head cut off, body and jeans visible) before it settles; base20 same seed starts framed right. Crop: full frame. This is the one place the eye and the metric's min (0.144) agree outright. It reads on the full frame.
2. lx8, wide, seed 1766580932, 0.00-5.88 s: a pampas-grass plume and a dark shape appear at the right of the frame in every frame; base20, lx4, pika6, hyper6 do not have them. Crop about x 700-1000, y 80-560 (approximate, measured from the 480 px face crop). An invented prop: a viewer sees it. This is not a face fault, so it does not belong in the face verdict, but it is the clearest difference between settings I found.
3. wide, seed 4103, 5.83 s (last frame), base20 and hyper6 versus the others: base20 and hyper6 are framed larger (face bigger, neck and shoulders in view); lx4, lx8, pika6 smaller. Crop (430,40)-(910,400). Shown side by side the framing difference reads at once.
4. close, seed 1766580932, 5.83 s, pika6 vs base20 vs lx4: freckles and eyes. Pika's face looks smoother and its eyes rounder; base and lx4 are denser. Crop (380,20)-(1020,500). Visible only enlarged.
5. close, seed 4103, 1.21 s (open vowel), lx4 vs pika6: mouth shape and freckle density at the cheek. Crop (380,20)-(1020,500). Weak: the open vowel looks right in both; the difference is the skin.
Where a setting looks as good as the base: lx4 close (3 seeds), lx8 close (seed 5207 first), hyper6 close (3 seeds), lx8 and hyper6 wide at the last frame (seed 1766580932 and 4103 aside from framing). On these I could not name a difference at normal size.


## Corrections and limits
- hyper6 wide seed 5207 does not pass the rule: its mean (0.593) is above the line, but its R1 min (0.144) is under the 0.37 floor, because of the badly framed opening (moment 1). The blind notes above were written before this was checked against the number and are unchanged.
- Not judged: motion at speed, audio, lip-sync timing, anything between the six frames per clip. Lips and teeth: nothing I could see wrong at those frames; that is not a statement about lip-sync.
- The eye's top pick matches the metric's top clip in only 2 of 6 strips (close 5207, close 4103).
