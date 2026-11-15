# EP09 measuring rule: H3 speed settings, seconds per clip vs does she keep her face

Frozen before any benchmark number exists (the last line holds the sha256 and the clock time). Nothing below moves after the freeze; a change is an AMENDMENT appended at the bottom with its own time, never an edit.

## 1. Test character and shots (EP07 inputs, nothing new)
- Character: synthetic test character **T2** (copper hair, freckles, beauty mark), picked 2026-11-07T12:58Z (look C). Not a real person. Sheet `inputs/sheet_T2.png` sha256 302e103ba..b8da (all input hashes: `inputs/SHA256SUMS`, sha256 4188467d7b8da88a5c85281f3e157505f617773172e91fa2a461ef5db3051943). Identity refs for the score: `inputs/t2_face.png`, `inputs/t2_front_full.png`. Shown only in DARK C cards.
- Shots (same prompt, plate, refs and audio pad as the EP07 takes; the graphs are copied in `inputs/`):
  - wide `T2WIDE-L2` (plate `plate_T2WIDE-L2.png`), close-up `T2FRONT-z125-L2` (1.25 punch-in plate). Line L2 pad `T2WIDE-L2_pad.wav`.
- Size: 1344x768, 141 frames, 24 fps (5.875 s), Ref2VA with the audio guide, as in production.
- Seeds, every setting and shot: **1766580932, 4103, 5207** (the EP07 trio). Clips per setting: 2 shots x 3 seeds = 6.

## 2. Settings (author's recommended sampler, source in `matrix.json`, sha256 947558c83ff28c907e918736faccebad638ebed5d97120b9a09590d1dae5c472)
| id | what | steps / sampler | note |
|---|---|---|---|
| base20 | no speed LoRA | 20, res_multistep + simple | ComfyUI R2V template defaults |
| lx4 | LightX2V Turbo 4-step v0.1, LoRA 1.0 | 4, euler + simple, shift 12/3 | author README + example workflow |
| lx8 | LightX2V Turbo 8-step v1.0 768p, LoRA 1.0 | 8, euler + simple, shift 6/3 | shift 6/3 taken from the sibling FL2VA 768p row: UNVERIFIED for this file |
| pika6 | Pika H3 Flex Ref2VA LoRA 1.0 | 6, lcm, Pika's 6 sigmas, shift 12/3 | Pika README sampling contract |
| hyper6 | HyperFlow H3 Flash (a compressed model, not a LoRA) | 6, euler, HyperFlow sigmas | own Ref2VA INT8 file, runs on the rig instance |
| lx8s12 | lx8 at shift 12/3 | 8, euler + simple | hedge for the unverified shift; reported next to lx8, never replaces it |
Same ComfyUI image, flags and base model file for all (lab and rig run the same image and flags). Not comparable and so not in the matrix: TaoMate 3-step (FL2VA/T2AV adapters only, no Ref2VA adapter exists) and alibaba-pai `MiniMax-H3-Ref2VA-Acc-8Step` (Diffusers format, does not load in ComfyUI).

## 3. What "seconds" means
Wall time of one ComfyUI prompt, from `execution_start` to the end of execution (websocket), warm: text and reference encoding, sampling, video and audio decode, mux and save all included. Excluded: container start, loading the model and the first LoRA patch (the first clip a process runs for a setting is marked `cold` and left out of the headline), copying files, face scoring. **Headline per setting = median of its warm clips (both shots pooled); every clip is reported.** Also recorded per clip: sampler-node seconds, whole-card peak VRAM, energy (nvidia-smi 4 Hz, whole card), and per job a line in our private job ledger (not published). Times are for this 4090 at 350 W, shared host, one session; step time drifts between sessions, so only compare inside this run.

## 4. Face check
- Metric as in EP07 (`scripts/score_face.py` here; in the original run `ep07-realism-measured/metric/score_face.py`, sha256 23322398e2f6cc0dfae63394407646b6a2edab5c7d7b5b32fac1643c2da818bf; AuraFace recognition file sha a7933ea5...fe25c60, YuNet detector, cosine to the mean of the normed embeddings of the two refs): first 120 frames, every 4th frame (30 samples), largest face, frames normalised to 1920x1080. **R1 mean** = mean of the 30 cosines, **R1 min** = the lowest frame.
- Pass line per shot, derived from the baseline (EP07 derived it from an upscaler baseline; here the baseline is the same shot generated with no speed LoRA, because every setting is an independent generation): **line(shot) = mean of base20's three seed R1 means on that shot - 0.028**, plus the absolute floor **R1 min >= 0.37**. The 0.028 and 0.37 are EP07's AuraFace constants (amendment A1 of `TEST-refiner-subject-T2.md`), reused unchanged. Why it transfers: same scorer, same character, same two shots and recipe. Why it needs care: EP07 compared arms that start from one draft, here seeds differ; so the baseline's own seed spread is reported, and base20 is judged by its own line too.
- A seed passes if R1 mean >= line(shot) and R1 min >= 0.37. A setting **kept her face on a shot if at least 2 of its 3 seeds pass** (EP07's 2-of-3). **Kept her face (overall) = kept on both shots.** Per-seed numbers are always shown; nothing is averaged away.
- Cross-reference only, never in the verdict: EP07's upscaler baseline lines (take C 0.510, take W 0.516).

## 5. Stops and failures
A clip that fails (OOM, error) is retried once; a second failure is recorded as `failed` and counts as not measured. A setting that cannot be run (for example HyperFlow's node does not load) is reported as not measured with the error, never replaced by another setting. Order of runs: pika6, lx4, lx8, base20, hyper6, lx8s12 (resumable: one record file per clip, done clips are skipped).

## 6. Not measured
Lip-sync and audio quality, motion and physics, prompt adherence, other characters or framings, clips longer than 5.9 s, other resolutions, the 15 s limit, our VSA node (EP02 setup), TaoMate, CFG variants, LoRA strengths other than 1.0, any quality metric other than the face cosine, and cost in money (GPU time and Wh only). Opinions on looks are subjective and are labelled so.
FROZEN 2026-11-11T21:42:23Z (date -u), sha256 of this file without this line: 1585f3a05568226bdd8cbd8640bba7bfd56753337502749f6a78fc07b52fb5fd. No benchmark record existed (review/ and clips/ empty).

## Amendment 1 (reporting only)
Why: the 0.028 tolerance came from EP07, where compared runs shared one draft. Here every clip is an independent generation; the only independent-seed data with this scorer (EP07 arm K, take C, `test-t2/results_rule.md`: R1 means 0.585, 0.498, 0.564) spans about 0.087, three times the tolerance. So a setting equal to the base could fail a seed by chance.
Unchanged: the pass line (base20 seed-mean minus 0.028, floor R1 min 0.37), the 2-of-3 rule, every measured quantity, seeds, settings, shots. Only what may be SAID about a result changes.
State at amendment time: 1 record existed in `review/records/` (the smoke clip lx4 wide s5207; the night queue had generated none yet); no face score had been computed for any clip (`review/face/` does not exist, no score output anywhere). The lab and rig instances run on the same single physical RTX 4090.
a. base20's per-shot seed range (min to max of its three seed means) is reported and drawn as a band wherever a setting's face result is shown.
b. «lost her», «redrew her» or «not her» may be used for a setting on a shot only if it fails by the rule AND at least 2 of its 3 seed means on that shot are below base20's lowest seed mean on that shot. A setting that fails by the rule without that is reported as «below the line, inside the seed noise».
c. A «seconds per kept clip» winner is named only if it beats the runner-up by at least 2 passing clips; otherwise: «three seeds cannot separate them».
d. If hyper6 runs in a different session or instance than the others, base20's hero-seed clips (seed 5207, both shots) are re-run in that session as a timing anchor, and hyper6's seconds are reported as a ratio to that anchor, labelled as such.
e. If lx8 and lx8s12 give different verdicts, lx8 is reported as «depends on a setting its author has not published», not as a fail.
`ep09_bench.py --aggregate` computes the base band, the two-condition flag, the margin and the seconds-per-kept-clip winner; the words are decided by the script. Also written there, descriptive only: peak VRAM per setting and sampler seconds against total wall seconds per clip.
AMENDMENT 1 FROZEN 2026-11-11T22:05:39Z (date -u), sha256 of this file up to and excluding this line: fc35ba9de0afa5807a4f55ff12548e3ebe96ce91671226910b729cda2b5cdc7a. Original freeze line above is unchanged.

## Amendment 2 (HyperFlow run and its timing anchor; no rule changed)
Why: The HyperFlow node was installed on the second instance by hand (2026-11-12). hyper6 is already named in section 2 and in matrix.json (rig instance, 6 steps, euler, HyperFlow sigmas, EP09 seeds and shots), so its definition is NOT changed. This amendment only records what Amendment 1 (d) requires because hyper6 runs on another instance and in another session than the other settings.
State at amendment time: 2026-11-12T02:29:01Z; review/records has 0 hyper6 records and 0 base20_rig records; the other four headline settings are done and scored (review/speedlora_metrics.json generated 2026-11-12T00:54:23Z); node verified byte-identical to commit 356649c32dca9a1dd46608d530ccb5e025fb338d (git archive diff, only PINNED_COMMIT added); rig container recreated with the weight file mounted read-only (sha256 38782037e343b498...), node loaded without error in the rig log.
a. hyper6 runs as defined (6 clips: 2 shots x seeds 1766580932, 4103, 5207) on the rig instance.
b. Amendment 1 (d) timing anchor: setting base20_rig = base20's own definition (20 steps, res_multistep, no LoRA), seed 5207 only, both shots (2 clips), run on the rig in the same lease as hyper6. hyper6's seconds are reported as ratio to the anchor's warm seconds, labelled as such. The anchor clips never enter any pass line, base band, seconds-per-kept-clip or verdict (base20's three-seed lines stay as frozen on the lab). The anchor's face scores are reported descriptively.
c. matrix.json gained that one setting (new sha256 75b0086d6be1d2a048f6bc074f50979f6179396cdc550fb351b056974ac3dfbb; old file kept as matrix.json.bak-2026-11-12-anchor); the runner accepts an optional per-setting seeds list (backup scripts/ep09_bench.py.bak-2026-11-12-anchor). Nothing else changed. The 8-step HyperFlow LoRA is out of scope.
Unchanged: pass line, 2-of-3 rule, metric, seeds, shots, the Amendment 1 wording rules.
AMENDMENT 2 FROZEN 2026-11-12T02:29:01Z (date -u), sha256 of this file up to and excluding this line: b55d9fdec1ababf5a8e39e53077ca67b9a0b030b369a22dc723c24efc3e96162. No hyper6 or base20_rig record existed.
