# Results (generated from results.json by scripts/make_results_md.py)

Rule file: RULE.md and its two amendments (last freeze line: AMENDMENT 2 FROZEN 2026-11-12T02:29:01Z ...). Metrics generated 2026-11-12T04:00:05Z.
Constants: tolerance 0.028, floor R1 min >= 0.37, 2 of 3 seeds per shot, seeds 1766580932, 4103, 5207.

## Pass lines and the base's own seed spread

| Shot | base20 mean of seed means | base20 seed range | Line (mean - 0.028) |
|---|---|---|---|
| wide | 0.5677 | 0.5576 to 0.5864 (spread 0.0288) | 0.5397 |
| close | 0.5490 | 0.5393 to 0.5614 (spread 0.0221) | 0.5210 |

## Seconds per clip (median of warm clips, both shots pooled)

| Setting | Steps | Seconds | Sampler seconds | Wh (whole card) | Peak VRAM, whole card (MiB) | Warm clips |
|---|---|---|---|---|---|---|
| base20: No speed LoRA (ComfyUI R2V template defaults) | 20 | 600.03 | 575.73 | 51.47 | 24068 | 5 |
| lx8: LightX2V Turbo 8-step v1.0 768p (Ref2VA) | 8 | 267.30 | 243.02 | 21.98 | 23492 | 5 |
| pika6: Pika H3 Flex (Ref2VA LoRA) | 6 | 207.57 | 183.16 | 16.97 | 23492 | 5 |
| lx4: LightX2V Turbo 4-step v0.1 (Ref2VA) | 4 | 146.71 | 122.24 | 11.95 | 23492 | 4 |
| hyper6: HyperFlow H3 Flash (fast model, own loader, 6 steps) | 6 | 194.13 † | 169.37 † | 16.44 † | 24050 | 5 |
| lx8s12 (report only): LightX2V 8-step with default shift 12/3 (hedge for the unverified shift) | 8 | 267.51 | 243.15 | 22.06 | 23492 | 5 |
| base20_rig (report only): base20 timing anchor on the rig (Amendment 2): seed 5207 only, both shots | 20 | 617.85 † | 582.71 † | 52.37 † | 23506 | 1 |

† 2nd ComfyUI instance, same card. Peak VRAM is the whole card with two ComfyUI instances sharing it, so it does not show what a setting needs.

## Face check, every seed (R1 mean / R1 min; pass = mean >= line and min >= 0.37)

| Setting | Shot | Seed 1766580932 | Seed 4103 | Seed 5207 | Seeds passed | Verdict |
|---|---|---|---|---|---|---|
| base20 | wide | 0.5589 / 0.5081 pass | 0.5864 / 0.5215 pass | 0.5576 / 0.4695 pass | 3 of 3 | passes the rule; seeds under the base's lowest seed: 0 |
| base20 | close | 0.5614 / 0.5039 pass | 0.5393 / 0.4667 pass | 0.5463 / 0.5006 pass | 3 of 3 | passes the rule; seeds under the base's lowest seed: 0 |
| lx8 | wide | 0.5529 / 0.4426 pass | 0.5200 / 0.4412 FAIL | 0.5465 / 0.4547 pass | 2 of 3 | passes the rule; seeds under the base's lowest seed: 3 |
| lx8 | close | 0.5637 / 0.4760 pass | 0.5598 / 0.4830 pass | 0.5883 / 0.5134 pass | 3 of 3 | passes the rule; seeds under the base's lowest seed: 0 |
| pika6 | wide | 0.5222 / 0.4569 FAIL | 0.5529 / 0.4541 pass | 0.5346 / 0.4902 FAIL | 1 of 3 | fails the rule; seeds under the base's lowest seed: 3 |
| pika6 | close | 0.5685 / 0.5161 pass | 0.5546 / 0.4664 pass | 0.5624 / 0.4861 pass | 3 of 3 | passes the rule; seeds under the base's lowest seed: 0 |
| lx4 | wide | 0.5344 / 0.4619 FAIL | 0.5332 / 0.4441 FAIL | 0.5344 / 0.4695 FAIL | 0 of 3 | fails the rule; seeds under the base's lowest seed: 3 |
| lx4 | close | 0.5695 / 0.4925 pass | 0.5697 / 0.5012 pass | 0.5566 / 0.4821 pass | 3 of 3 | passes the rule; seeds under the base's lowest seed: 0 |
| hyper6 † | wide | 0.5763 / 0.4712 pass | 0.5570 / 0.4826 pass | 0.5934 / 0.1437 FAIL | 2 of 3 | passes the rule; seeds under the base's lowest seed: 1 |
| hyper6 † | close | 0.5946 / 0.4936 pass | 0.5408 / 0.4792 pass | 0.5847 / 0.5165 pass | 3 of 3 | passes the rule; seeds under the base's lowest seed: 0 |
| lx8s12 | wide | 0.5483 / 0.4838 pass | 0.5308 / 0.4502 FAIL | 0.5553 / 0.4839 pass | 2 of 3 | passes the rule; seeds under the base's lowest seed: 3 |
| lx8s12 | close | 0.5711 / 0.5061 pass | 0.5293 / 0.4742 pass | 0.5891 / 0.4593 pass | 3 of 3 | passes the rule; seeds under the base's lowest seed: 1 |
| base20_rig † | wide | - | - | 0.5576 / 0.4695 pass | 1 of 1 | not decided (anchor clip only); seeds under the base's lowest seed: 0 |
| base20_rig † | close | - | - | 0.5463 / 0.5006 pass | 1 of 1 | not decided (anchor clip only); seeds under the base's lowest seed: 0 |

## Every clip

| Clip | Instance | Cold | Seconds | Sampler s | Peak MiB | Wh | Peak W | R1 mean | R1 min |
|---|---|---|---|---|---|---|---|---|---|
| base20__close__s1766580932 | lab |  | 618.24 | 582.97 | 23428 | 52.2 | 362 | 0.5614 | 0.5039 |
| base20__close__s4103 | lab |  | 599.94 | 575.58 | 24068 | 51.4 | 364 | 0.5393 | 0.4667 |
| base20__close__s5207 | lab |  | 600.93 | 576.46 | 24068 | 51.47 | 364 | 0.5463 | 0.5006 |
| base20__wide__s1766580932 | lab | cold | 619.73 | 583.39 | 20868 | 52.04 | 364 | 0.5589 | 0.5081 |
| base20__wide__s4103 | lab |  | 600.03 | 575.73 | 24068 | 51.34 | 363 | 0.5864 | 0.5215 |
| base20__wide__s5207 | lab |  | 599.76 | 575.50 | 24068 | 51.49 | 364 | 0.5576 | 0.4695 |
| base20_rig__close__s5207 | rig |  | 617.85 † | 582.71 † | 22834 | 52.37 † | 363 | 0.5463 | 0.5006 |
| base20_rig__wide__s5207 | rig | cold | 618.26 † | 582.45 † | 23506 | 52.5 † | 365 | 0.5576 | 0.4695 |
| hyper6__close__s1766580932 | rig |  | 210.00 † | 173.38 † | 23442 | 17.25 † | 364 | 0.5946 | 0.4936 |
| hyper6__close__s4103 | rig |  | 194.13 † | 169.37 † | 23858 | 16.44 † | 363 | 0.5408 | 0.4792 |
| hyper6__close__s5207 | rig |  | 194.12 † | 169.33 † | 23826 | 16.48 † | 364 | 0.5847 | 0.5165 |
| hyper6__wide__s1766580932 | rig | cold | 211.72 † | 173.03 † | 19984 | 17.0 † | 363 | 0.5763 | 0.4712 |
| hyper6__wide__s4103 | rig |  | 192.69 † | 167.74 † | 23826 | 16.28 † | 365 | 0.5570 | 0.4826 |
| hyper6__wide__s5207 | rig |  | 194.61 † | 169.74 † | 24050 | 16.39 † | 368 | 0.5934 | 0.1437 |
| lx4__close__s1766580932 | lab |  | 164.78 | 129.49 | 23364 | 12.83 | 364 | 0.5695 | 0.4925 |
| lx4__close__s4103 | lab |  | 146.71 | 122.17 | 23492 | 11.94 | 361 | 0.5697 | 0.5012 |
| lx4__close__s5207 | lab |  | 146.70 | 122.30 | 23492 | 11.94 | 365 | 0.5566 | 0.4821 |
| lx4__wide__s1766580932 | lab | cold | 164.88 | 129.54 | 23428 | 12.82 | 366 | 0.5344 | 0.4619 |
| lx4__wide__s4103 | lab |  | 146.35 | 121.98 | 23492 | 11.95 | 360 | 0.5332 | 0.4441 |
| lx4__wide__s5207 | lab | cold | 168.53 | 130.12 | 21074 | 12.76 | 361 | 0.5344 | 0.4695 |
| lx8__close__s1766580932 | lab |  | 285.65 | 250.37 | 23460 | 22.84 | 364 | 0.5637 | 0.4760 |
| lx8__close__s4103 | lab |  | 267.29 | 242.99 | 23492 | 21.95 | 366 | 0.5598 | 0.4830 |
| lx8__close__s5207 | lab |  | 267.15 | 242.83 | 23492 | 21.98 | 364 | 0.5883 | 0.5134 |
| lx8__wide__s1766580932 | lab | cold | 287.40 | 251.43 | 21604 | 22.76 | 364 | 0.5529 | 0.4426 |
| lx8__wide__s4103 | lab |  | 267.95 | 243.73 | 23428 | 21.98 | 366 | 0.5200 | 0.4412 |
| lx8__wide__s5207 | lab |  | 267.30 | 243.02 | 23492 | 21.97 | 364 | 0.5465 | 0.4547 |
| lx8s12__close__s1766580932 | lab |  | 286.31 | 250.90 | 23108 | 22.94 | 363 | 0.5711 | 0.5061 |
| lx8s12__close__s4103 | lab |  | 267.47 | 243.09 | 23492 | 22.06 | 363 | 0.5293 | 0.4742 |
| lx8s12__close__s5207 | lab |  | 267.58 | 243.15 | 23492 | 22.03 | 367 | 0.5891 | 0.4593 |
| lx8s12__wide__s1766580932 | lab | cold | 286.46 | 250.29 | 21604 | 22.8 | 362 | 0.5483 | 0.4838 |
| lx8s12__wide__s4103 | lab |  | 267.39 | 243.16 | 23492 | 22.03 | 364 | 0.5308 | 0.4502 |
| lx8s12__wide__s5207 | lab |  | 267.51 | 243.07 | 23492 | 22.07 | 365 | 0.5553 | 0.4839 |
| pika6__close__s1766580932 | lab |  | 226.03 | 190.79 | 23492 | 17.81 | 364 | 0.5685 | 0.5161 |
| pika6__close__s4103 | lab |  | 207.48 | 183.11 | 23492 | 16.97 | 366 | 0.5546 | 0.4664 |
| pika6__close__s5207 | lab |  | 207.89 | 183.20 | 23492 | 16.97 | 366 | 0.5624 | 0.4861 |
| pika6__wide__s1766580932 | lab | cold | 227.20 | 190.79 | 20772 | 17.71 | 364 | 0.5222 | 0.4569 |
| pika6__wide__s4103 | lab |  | 207.57 | 183.16 | 23492 | 16.92 | 365 | 0.5529 | 0.4541 |
| pika6__wide__s5207 | lab |  | 207.47 | 183.15 | 23492 | 16.97 | 365 | 0.5346 | 0.4902 |

† 2nd ComfyUI instance, same card. 'Cold' = the first clip a process ran for a setting (model load and LoRA patch); it is left out of the median.
