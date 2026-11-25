![Noto](images/noto.png)
# Noto Emoji
Noto Emoji (Stands for No Tofu) is an open source (Open Font License 1.1) emoji library that provides standard Unicode emoji support and tools for working with them including:

- A Unicode compliant color emoji [font](https://github.com/googlefonts/noto-emoji/raw/main/fonts/NotoColorEmoji.ttf).
- A full library of Noto color emoji font files including vector svgs and pngs
- [Metadata](https://github.com/googlefonts/emoji-metadata) for Emoji Input (including shortcodes, emoji ordering, ascii equivalents)

## Color Font

The latest font file is found [here](https://github.com/DavidBerdik/blobmoji2/releases/latest/download/NotoColorEmoji.ttf). If you want to download a specific version please check the [releases section](https://github.com/DavidBerdik/blobmoji2/releases/latest)

## Monochrome Font

The black-and-white emoji font is back under active development and is available as a [variable font](https://fonts.google.com/noto/specimen/Noto+Emoji)

## Color font formats

Blobmoji2 ships several color builds from the same SVG artwork:

| File | Format | Notes |
| --- | --- | --- |
| `NotoColorEmoji.ttf` | CBDT/CBLC (bitmap) | Broad legacy support (Android, Chrome, etc.) |
| `Noto-COLRv1.ttf` | COLRv1 + glyf | Gradients, soft-light on flags; newer stacks |
| `Noto-COLRv0.ttf` | COLRv0 + glyf | Flat colors only (gradients flattened at build time); useful for older Qt / mobile Linux renderers with COLRv0 but not COLRv1 |

CBDT/CBLC is described in [issue #36](https://github.com/googlei18n/noto-emoji/issues/36) for Linux fontconfig setup.

Build everything (including COLRv0) with `./full_rebuild.sh` or `docker_build.sh` — see [BUILD.md](BUILD.md).

## License

Emoji fonts (under the fonts subdirectory) are under the
[SIL Open Font License, version 1.1](fonts/LICENSE).<br/>
Tools and most image resources are under the [Apache license, version 2.0](./LICENSE).
Flag images under third_party/region-flags are in the public domain or
otherwise exempt from copyright ([more info](third_party/region-flags/LICENSE)).
