# comfyui-minimax-h3-speedups

Four ways to make the MiniMax H3 video model faster in ComfyUI, timed against the plain 20-step run on one RTX 4090, and checked for one thing: does the generated woman still look like the character sheet she was generated from. The rule that decides "still her" was written and frozen before the first clip was measured. This is the material behind the YouTube episode «MiniMax H3 in ComfyUI: 600s to 147s with a 4-Step LoRA (RTX 4090 Face Check)».

- Video: link added when the episode is public
- Test log, not a benchmark: one character, two framings, three seeds, one card. Read "What was not measured" before you copy a number.

## What was tested

Reference-to-video with an audio guide (Ref2VA), 1344x768, 141 frames at 24 fps (5.875 s), one synthetic test character (not a real person), two shots (a wide shot and a close-up), three seeds each (1766580932, 4103, 5207). Five settings, 6 clips each, 30 headline clips:

| Setting | Made by | What it is | Steps |
|---|---|---|---|
| base20 | (reference) | ComfyUI's Reference-to-Video template defaults, no speed-up | 20 |
| lx8 | lightx2v / ModelTC | LightX2V Turbo 8-step v1.0 768p Ref2VA LoRA, strength 1.0 | 8 |
| pika6 | Pika-Labs | Pika H3 Flex Ref2VA LoRA, strength 1.0, Pika's six sigmas | 6 |
| lx4 | lightx2v / ModelTC | LightX2V Turbo 4-step v0.1 Ref2VA LoRA, strength 1.0 | 4 |
| hyper6 | Video Rebirth | HyperFlow H3 Flash, its own fast model with its own loader (not a LoRA, not an official MiniMax product) | 6 |

Two extra settings are reported next to them and never replace a headline one: lx8s12 (lx8 at the model's default shift 12/3, because the shift 6/3 used for lx8 was taken from a sibling file and is unverified for this one) and base20_rig (the base re-run on the second ComfyUI instance, see the dagger below).

## The rule, short

Full text, frozen before measuring: [RULE.md](RULE.md) (with two reporting amendments; what differs from our private original is in [RULE-REDACTIONS.md](RULE-REDACTIONS.md)).

- Face score: cosine similarity between the face in the clip and the mean of two reference faces of the sheet, 30 frames per clip (first 120 frames, every 4th), AuraFace recognition model, YuNet detector. Per clip: R1 mean and R1 min.
- Pass line per shot: the mean of the base's three seed means on that shot, minus 0.028, and R1 min of at least 0.37. A seed passes if both hold; a setting passes a shot if 2 of 3 seeds pass; it passes the rule if it passes both shots.
- Seconds: wall time of one ComfyUI prompt, warm clips only (the first clip a process runs for a setting is marked cold and left out), median of both shots pooled.
- The base's own seed spread (0.029 wide, 0.022 close) is about the size of the 0.028 tolerance, so the verdicts are read together with it: a setting is only called clearly lower when at least two of its three seed means are under the base's lowest seed mean on that shot.

## Results

All figures are from [results.json](results.json); [results.md](results.md) has every seed and every clip.

Speed (median of warm clips, both shots pooled, seconds per clip):

| Setting | Steps | Seconds | Times as fast as base | Sampler seconds | Wh per clip (whole card) | Peak VRAM, whole card (MiB) |
|---|---|---|---|---|---|---|
| base20 (reference) | 20 | 600.03 | 1.0 | 575.73 | 51.47 | 24068 |
| lx8 (lightx2v / ModelTC) | 8 | 267.30 | 2.2 | 243.02 | 21.98 | 23492 |
| pika6 (Pika-Labs) | 6 | 207.57 | 2.9 | 183.16 | 16.97 | 23492 |
| lx4 (lightx2v / ModelTC) | 4 | 146.71 | 4.1 | 122.24 | 11.95 | 23492 |
| hyper6 (Video Rebirth) | 6 | 194.13 † | about three times † | 169.37 † | 16.44 † | 24050 |

Face check against the frozen rule (seeds passed of 3, per shot; the rule needs 2 of 3 on both shots):

Pass lines: wide 0.540 (base mean 0.568, seed range 0.558 to 0.586); close 0.521 (base mean 0.549, seed range 0.539 to 0.561).

| Setting | Rule, wide shot | Rule, close shot | Passing clips of 6 | Wide seeds under the base's lowest | Verdict by the rule | By eye (separate, subjective) |
|---|---|---|---|---|---|---|
| base20 (reference) | 3 of 3 | 3 of 3 | 6 | 0 of 3 | passes both shots (it is the line) | mid-pack (mean eye position 3.0 of 5) |
| lx8 (lightx2v / ModelTC) | 2 of 3 | 3 of 3 | 5 | 3 of 3 | passes both shots | level with the base (2.8) |
| pika6 (Pika-Labs) | 1 of 3 | 3 of 3 | 4 | 3 of 3 | fails the wide shot, passes the close-up | last in 5 of 6 strips (4.8): softer freckles, smoother face, only on enlarged crops; still the same woman |
| lx4 (lightx2v / ModelTC) | 0 of 3 | 3 of 3 | 3 | 3 of 3 | fails the wide shot, passes the close-up | first or second in 5 of 6 strips (1.7): same woman, dense freckles; could not name what moved |
| hyper6 (Video Rebirth) | 2 of 3 | 3 of 3 | 5 | 1 of 3 | passes both shots | level with the base (2.7); one wide clip starts badly framed (see failures) |

R1 mean per seed (seeds 1766580932 / 4103 / 5207; ✓ passes both the line and the 0.37 floor, ✗ does not):

| Setting | Wide | Close |
|---|---|---|
| base20 (reference) | 0.559 ✓ / 0.586 ✓ / 0.558 ✓ | 0.561 ✓ / 0.539 ✓ / 0.546 ✓ |
| lx8 (lightx2v / ModelTC) | 0.553 ✓ / 0.520 ✗ / 0.546 ✓ | 0.564 ✓ / 0.560 ✓ / 0.588 ✓ |
| pika6 (Pika-Labs) | 0.522 ✗ / 0.553 ✓ / 0.535 ✗ | 0.568 ✓ / 0.555 ✓ / 0.562 ✓ |
| lx4 (lightx2v / ModelTC) | 0.534 ✗ / 0.533 ✗ / 0.534 ✗ | 0.569 ✓ / 0.570 ✓ / 0.557 ✓ |
| hyper6 (Video Rebirth) | 0.576 ✓ / 0.557 ✓ / 0.593 ✗ | 0.595 ✓ / 0.541 ✓ / 0.585 ✓ |

† 2nd ComfyUI instance, same card.

How to read it:

- Fastest is lx4 at 146.71 s a clip, 4.1 times as fast as the 600.03 s base (the episode rounds these to 147 s and 600 s).
- The opening pair in the video is wide seed 4103: 146.35 s against 600.03 s; 147 s is the 4-step's median.
- lx8 (2.2 times as fast) and hyper6 pass both shots, like the base. lx4 and pika6 fail the wide shot and pass the close-up.
- On the wide shot all three seeds of lx4 and pika6, and of lx8, are under the base's lowest seed mean (0.558); only hyper6 stays with the base (mean of its three seed means 0.5756; its seed 4103 is 0.55702, a hair under the base's lowest). lx8 still passes the rule on two seeds, by under 0.015 (+0.0132 and +0.0068 over the line); its seed 4103 is the lowest mean of any speed-up clip, 0.5200.
- On the close-up all 12 speed-up seed means are inside or above the base's seed range (lowest base close mean 0.539).
- HyperFlow † ran on a second ComfyUI instance on the same card. Against the base re-run on that instance (seed 5207, 617.85 †) it is about three times as fast (617.85 / 194.13 = 3.18); against the first instance's base median it is 3.09. Both are "about three times".
- Everything outside the sampler (text and reference encoding, decode, mux, save) costs about 24 to 25 s a clip in all five settings (about 35 s on the first clip after a shot change), so the speed-up is all in the sampler and the 4-step runs into that floor.

## Eye check

Separate from the number and subjective: one reader, six frames of each of the 30 clips, rows shuffled and unlabelled first, then joined with the score. See [eye-table.md](eye-table.md). The short version: all 30 clips read as the same woman at normal size; differences show only on enlarged face crops. The eye agrees with the score for lx8, hyper6 and the direction of the pika6 wide result, and disagrees for lx4 on the wide shot, where it put lx4 first in two of three strips (4th in the third); first or second in 5 of 6 overall. Not judged by eye: motion at speed, audio, lip-sync timing, anything between the six frames.

## Reproduce

You need your own test character (a character sheet, a face close-up and a full-body front view for the score), two room plates (wide and a 1.25 punch-in), and a short audio guide. Our sheet, plates and audio are not in this repo, so the scores will differ from ours on your material; the method is what transfers.

1. ComfyUI 0.42.1, Python 3.12, PyTorch 2.13.0 (CUDA 13.0 build), launched with `--disable-pinned-memory --cache-ram 6 --disable-comfy-compiler`. We ran two instances on the same card: the first for base20, lx4, lx8, pika6 and lx8s12, the second for hyper6 and the base20 anchor (HyperFlow's node lives there). A single instance works too; then the dagger does not apply to your numbers.
2. Model files, from their authors' own pages (links in [NOTICE.md](NOTICE.md); this repo ships none of them and has no downloader). File names used by the workflows:
   - base: `minimax_h3_ref2va_pruned_int8_convrot.safetensors`, `minimax_h3_video_vae_fp16.safetensors`, `minimax_h3_audio_vae_fp32.safetensors`, `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`
   - lx4: `minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors`; lx8 and lx8s12: `minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors`
   - pika6: `pika_h3_flex_ref2va_comfy_bf16.safetensors` (loaded as a LoRA at 1.0 with Pika's six sigmas; the label stays "Pika H3 Flex (Ref2VA LoRA), 6 steps")
   - hyper6: `minimax_h3_ref2va_hyperflow_flash_14b-int8_convrot.safetensors` and the HyperFlow ComfyUI node, which we ran from the author's repository at commit `356649c32dca9a1dd46608d530ccb5e025fb338d` (GPL-3.0; not copied here, install it from the author's page).
3. Workflows: [workflows/api/](workflows/api/) holds the twelve graphs (6 settings x 2 shots, seed 5207, API format) exactly as the runner submitted them, with only the file names of the character sheet, room plates and audio changed to generic ones (`character_sheet.png`, `room_plate_wide.png`, `room_plate_close.png`, `audio_pad.wav`). Submit one with a POST to your ComfyUI's `/prompt` (`{"prompt": <file contents>}`). [workflows/ui/](workflows/ui/) holds the same six graphs in UI format (drag onto the ComfyUI canvas), one per setting for the wide shot: the close-up graph differs only in the prompt (`prompts/close.txt`), the room plate (`room_plate_close.png`) and the save prefix. The UI files were exported by loading the API graphs into a ComfyUI 0.42.1 page (nothing was run) and checked by loading each back: all nodes found, no missing node types. The sheet, plate and audio file names do not exist on your machine, so ComfyUI flags those four input nodes until you pick your own files. The prompts are in [prompts/](prompts/).
4. The runner: copy your files into `inputs/` under the names in `matrix.json`/`bench.py` (`sheet_T2.png`, `plate_T2WIDE-L2.png`, `plate_T2FRONT-z125-L2.png`, `T2WIDE-L2_pad.wav`), set `COMFY_PORT_LAB`, `COMFY_CONTAINER_LAB`, `COMFY_INPUT_LAB`, `COMFY_OUTPUT_LAB` (and `_RIG`), then
   ```bash
   python3 -I scripts/bench.py --dry-run          # no GPU: matrix, estimated time, builds all graphs
   python3 -I scripts/bench.py --target lab       # resumable: one record per clip in review/records/
   python3 -I scripts/bench.py --target rig       # hyper6 and the base20 anchor, on the second instance
   ```
5. Face check (CPU): put `glintr100.onnx` (AuraFace, recognition file only) in `scripts/weights/auraface/` and `sface.onnx` and `yunet.onnx` (OpenCV Zoo) in `scripts/weights/opencv_zoo/`; the script refuses files whose sha256 differs from the ones it expects. Then `scripts/score_clips.sh FACE_REF.png FRONT_REF.png`, `python3 -I scripts/bench.py --aggregate` (writes `review/speedlora_metrics.json`) and `python3 -I scripts/make_results_md.py`.
6. Check: `python3 -I scripts/bench.py --aggregate` on the shipped `review/records/` and `review/face/face_scores.jsonl` rebuilds every number in `results.json` (we did this before publishing: identical apart from the clip paths and the generation time).

The shipped `scripts/score_face.py` differs from the frozen EP07 file only in its header comment and one path line (the original's sha256 is in RULE.md, section 4).

## What was NOT measured

Lip-sync and audio quality, motion and physics, prompt adherence, other characters, other framings, clips longer than 5.9 s, other resolutions, other cards (one RTX 4090), LoRA strengths other than 1.0, CFG variants, any quality measure other than the face cosine, and cost in money (GPU time and watt-hours only). Whole-card VRAM peaks were 23,492 to 24,068 MiB (about 22.9 to 23.5 GiB) across the settings; that is the whole card with two ComfyUI instances loaded, not what any one model requires. The eye check judged six frames per clip, not video at speed.

## Failures and corrections

- Power: RULE.md section 3 says the card ran at 350 W. The logged whole-card power peaks per clip are 360 to 368 W (38 clips with a reading, column Peak W in results.md). The rule was frozen as written and is not edited; energy figures are measured, not derived from 350 W.
- HyperFlow, wide shot, seed 5207: the clip starts badly framed (head cut off at the forehead, body and jeans in view, roughly the first 0.4 s, frames 0 to 12) before it settles. Its R1 mean is 0.593, above the line, but its R1 min is 0.144, under the 0.37 floor, so that seed fails; the setting still passes the wide shot with the other two seeds. The floor caught a framing fault, not a different face.
- lx8 wide, seed 1766580932: a pampas-grass plume and a dark shape appear at the right edge in every frame, in no other setting. An invented prop, not a face fault, so it is not in the face verdict.
- Some wide clips are framed larger (face bigger, shoulders in view): base20 and hyper6 on seed 4103 against the others.
- lx8 uses shift 6/3 taken from a sibling file's table, unverified for the Ref2VA file. lx8s12 (shift 12/3) gives the same verdict, 5 passing clips of 6 for both, so lx8 is reported as measured.
- Timing correction: a first comparison of the base on the second instance with the base on the first (617.85 † s against 600.93 s, same seed and shot) looked about 3 % slower. That compared a clip right after a shot change with a steady one. The first clip after a shot change is about 16 to 19 s slower in every setting. The slower first clips are of two kinds: the first clip after a process start (marked cold in results.md, left out of every median) and the first clip after a shot change (not marked cold, so it stays in the median, which one slow clip among four or five barely moves: lx4 is 146.71 s with it and 146.70 s without). Like for like, both being the first close clip after a shot change, the second instance took 617.85 † s (seed 5207) against 618.24 s on the first (seed 1766580932), a ratio of 0.9994. Checked on seed 5207, both shots: the base re-run on the second instance decodes to the same video and the same audio as on the first (md5 of the decoded streams).
- The rule's wording (RULE.md, Amendment 1) predates the eye table; the eye table is read next to the number and does not change any verdict.
- Label change: results.json (frozen) calls hyper6 "compressed model"; results.md shows "fast model, own loader" because the base file is itself pruned, so "compressed" distinguished nothing. Only the display label changed, no figure.
- The score line is tight: the base's own three seeds spread about as far as the 0.028 tolerance, so a setting equal to the base could fail a seed by chance. That is why the amendments limit what may be said, and why per-seed numbers are always shown.
- The eye table was written blind and then joined with the score; one of its first readings (that the HyperFlow wide seed 5207 passed) was wrong and is corrected in it.

## Credits and licences

- This repo's own code and text: MIT, see [LICENSE](LICENSE).
- Models and files are not included. The four speed-up files are: the LightX2V Turbo 4-step LoRA, the LightX2V Turbo 8-step LoRA, Pika H3 Flex (used as a LoRA) and HyperFlow H3 Flash. Each of these files is distributed by its author under the MiniMax H3 Community License Agreement (link in [NOTICE.md](NOTICE.md)). That agreement has territorial and use restrictions, including for the EU, UK, South Korea and the US, so read it and obtain any authorization it requires from MiniMax before you run these files. This repository is not a licence and says nothing about what is permitted for you.
- No model weights are included in this repo; get each file from its author (see [NOTICE.md](NOTICE.md)).
- Not affiliated with MiniMax, Video Rebirth, Pika or LightX2V; no endorsement is implied. HyperFlow H3 Flash is not an official MiniMax product.
- Clips generated by these models are AI-generated; label them as such wherever you publish them.
- Not legal advice. Third-party notes and links: [NOTICE.md](NOTICE.md).

More from us: https://grawwww.xyz
