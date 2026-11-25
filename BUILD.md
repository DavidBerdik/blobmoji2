# Build instructions

Typically build the CBDT first, then COLRv1 and COLRv0, as those vector builds copy name tables and metrics from the CBDT font during post-processing.

## Is this a Unicode rev?

* Update https://github.com/notofonts/nototools, publish the new version
   * Must be done by a Googler. See internal instructions.
* Update emojicompat
   * https://github.com/googlefonts/emojicompat?tab=readme-ov-file#support-new-unicode-sequences
* Update artwork
   * Must be done by a Googler. Work with the emoji design team using internal instructions.

## Update version

Edit `NotoColorEmoji.tmpl.ttx.tmpl`
*   In `<head>` find `fontRevision`.
    *   It should be of the form 2.xxx
    *   Increment xxx by 1
*   In `<name>` find `<namerecord nameID="5" platformID="3" platEncID="1"
    langID="0x409">`
    *   It should look like `Version
        2.017;GOOG;noto-emoji:20180810:f1da3bc656f9`
    *   Update Version to match `<head>` (`Version 2.017` in the example)
    *   Update the date (`20180810` in the example)
    *   Update the commit

## Update new flags

* Add new flags to list in Makefile ([example](https://github.com/googlefonts/noto-emoji-next/commit/21bdd6107fac60979737ac95c2655cb02824d144))
* Update `third_party/region-flags`. For example, for CQ (Sark) update:
   * `third_party/region-flags/png/CQ.png`
      * This file can be highres, it will be resized by the CBDT build process
      * This file should have the proportions of the flag
   * `third_party/region-flags/svg/CQ.svg`
      * This file is *not* required to have the `0 0 128 128` viewbox files in `/svg` have to have
   * `third_party/region-flags/waved-svg/emoji_u1f1e8_1f1f6.svg`
      * This file is produced using https://github.com/rsheeter/warp
      * New flags are added to `wave_list.txt`
         * To wave only the new flag delete other entries locally

## Rebuild the fonts

```bash
# Build CBDT, COLRv1, COLRv0, flags-only, and emojicompat fonts
$ ./full_rebuild.sh
```

### COLRv0 pipeline

COLRv0 is built after CBDT and COLRv1 inside `full_rebuild.sh`:

1. `colrv0_stage_svgs.py` — copies SVGs into `colrv0/staged/`, flattens gradients to solids, runs picosvg, merges same-color paths to stay under OpenType’s 65535 COLRv0 layer limit. Waved region flags additionally union all paths per solid paint (preserving paint-stack order).
2. `colrv0_measure.py --staged --require-under-limit` — aborts the build if layer/glyph estimates still exceed the limit.
3. `colrv0_generate_configs.py` + `nanoemoji` with `glyf_colr_0`.
4. `colrv0_postproc.py` — same cmap/GSUB fixes as COLRv1, but **without** COLRv1 flag soft-light.

Optional: `python colrv0_stage_svgs.py --snap-grid 0.25` if measurement reports you are still over the limit (near-lossless coordinate snapping).
