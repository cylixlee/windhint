# windhint

Configuration-driven batch font hinting for TrueType (`.ttf`) fonts, powered by `ttfautohint`.

## Installation

```bash
pip install windhint
# or
uv tool install windhint
```

## Quick Start

```bash
# 1. Generate a configuration template
windhint --init

# 2. Edit windhint.yaml — set your input and output directories

# 3. Run
windhint
```
 
## Configuration Reference

| Field                   | Type    | Required | Default | Description                                                                    |
| ----------------------- | ------- | -------- | ------- | ------------------------------------------------------------------------------ |
| `input-dir`             | string  | Yes      | —       | Directory containing `.ttf` fonts to hint                                      |
| `output-dir`            | string  | Yes      | —       | Directory where hinted fonts will be written                                   |
| `windows-compatibility` | boolean | No       | `true`  | Add blue zones for `usWinAscent` and `usWinDescent` to avoid clipping          |
| `fallback-stem-width`   | integer | No       | `50`    | Fallback stem width at 2048 UPEM                                               |
| `hinting-range-min`     | integer | No       | `8`     | Minimum PPEM value for hint sets                                               |
| `hinting-range-max`     | integer | No       | `50`    | Maximum PPEM value for hint sets                                               |
| `hinting-limit`         | integer | No       | `200`   | Switch off hinting above this PPEM value; `0` means no limit                   |
| `increase-x-height`     | integer | No       | `14`    | Increase x-height for 6 ≤ PPEM ≤ N; `0` disables                               |
| `stem-width-mode`       | string  | No       | `"sss"` | Stem width mode: three letters of `n` (natural), `q` (quantized), `s` (strong) |

## Example Configuration

```yaml
input-dir: ./fonts/source
output-dir: ./fonts/hinted
windows-compatibility: true
fallback-stem-width: 50
hinting-range-min: 8
hinting-range-max: 50
hinting-limit: 200
increase-x-height: 14
stem-width-mode: sss
```

## CLI Options

| Option          | Description                                              |
| --------------- | -------------------------------------------------------- |
| `--init`        | Generate a `windhint.yaml` configuration template        |
| `-f`, `--force` | Overwrite existing hinted fonts instead of skipping them |

## How It Works

windhint walks `input-dir` recursively, finds all `.ttf` files, mirrors the directory structure under `output-dir`, and invokes `ttfautohint` on each file with the parameters from your configuration. 

By default, fonts that already exist in `output-dir` are skipped — use `--force` to overwrite them.

## License

Apache-2.0
