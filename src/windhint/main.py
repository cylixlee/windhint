import os
import pathlib
import subprocess
import sys
import argparse
import importlib.resources

import yaml
from pydantic import BaseModel, Field, ValidationError
from tqdm import tqdm

CONFIGURATION_CANDIDATES: list[str] = [
    "windhint.yaml",
    "windhint.yml",
    "Windhint.yaml",
    "Windhint.yml",
]
POSTFIX_LEN = 32


class WindhintConf(BaseModel):
    input_dir: str = Field(alias="input-dir")
    """
    Directory containing .ttf font files to hint.
    """

    output_dir: str = Field(alias="output-dir")
    """
    Directory where hinted fonts will be written.
    """

    windows_compatibility: bool = Field(default=True, alias="windows-compatibility")
    """
    Whether to add blue zones for `usWinAscent` and `usWinDescent` to avoid clipping. (default: True)
    """

    fallback_stem_width: int = Field(default=50, alias="fallback-stem-width")
    """
    Fallback stem width (default: 50 font units at 2048 UPEM)
    """

    hinting_range_min: int = Field(default=8, alias="hinting-range-min")
    """
    The minimum PPEM value for hint sets (default: 8)
    """

    hinting_range_max: int = Field(default=50, alias="hinting-range-max")
    """
    The maximum PPEM value for hint sets (default: 50)
    """

    hinting_limit: int = Field(default=200, alias="hinting-limit")
    """
    Switch off hinting above this PPEM value; value 0 means no limit (default: 200)
    """

    increase_x_height: int = Field(default=14, alias="increase-x-height")
    """
    Increase x height for sizes in the range 6<=PPEM<=N; value 0 switches off this feature (default: 14)
    """

    stem_width_mode: str = Field(default="sss", alias="stem-width-mode")
    """
    Select stem width mode for grayscale, GDI ClearType, and DW ClearType, where S is a string of three letters with
    possible values
                             
    - `n' for natural
    - `q' for quantized
    - `s' for strong
    
    (default: sss)
    """


def init_config() -> None:
    confpath = pathlib.Path.cwd() / "windhint.yaml"
    if confpath.exists():
        print(f"error: {confpath} already exists in the current directory.", file=sys.stderr)
        sys.exit(1)

    template = importlib.resources.files("windhint").joinpath("template.yaml").read_text()
    confpath.write_text(template)
    print(f"Created {confpath}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="windhint",
        description="Batch hint TrueType fonts using ttfautohint with a YAML configuration.",
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Create a windhint.yaml configuration file in the current directory.",
    )
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Overwrite existing hinted fonts instead of skipping them.",
    )
    cli_args = parser.parse_args()

    if cli_args.init:
        init_config()
        return

    confpath: pathlib.Path | None = None
    for candidate in CONFIGURATION_CANDIDATES:
        p = pathlib.Path(os.getcwd()) / candidate
        if p.exists():
            confpath = p
            break
    if not confpath:
        errmsg = f"error: No configuration found ({' || '.join(CONFIGURATION_CANDIDATES)}). Aborting."
        print(errmsg, file=sys.stderr)
        sys.exit(1)

    try:
        with confpath.open() as f:
            conf = WindhintConf.model_validate(yaml.safe_load(f))
    except ValidationError as e:
        print("error: Invalid configuration", file=sys.stderr)
        errors = e.errors(include_url=False, include_context=False, include_input=False)
        for err in errors:
            print(f"error: {err['msg']}", file=sys.stderr)
        sys.exit(1)

    args: list[str] = []
    for k, v in dict(conf).items():
        if k in ["input_dir", "output_dir"]:
            continue
        if isinstance(v, bool):
            args.append(f"--{k.replace('_', '-')}")
        else:
            args.append(f"--{k.replace('_', '-')}={v}")

    input_dir = pathlib.Path(conf.input_dir).as_posix()
    output_dir = pathlib.Path(conf.output_dir).as_posix()

    try:
        pathlib.Path(conf.output_dir).relative_to(pathlib.Path(conf.input_dir))
        print("error: output-dir must not be a subdirectory of input-dir", file=sys.stderr)
        sys.exit(1)
    except ValueError:
        pass

    inputs: list[pathlib.Path] = []
    outputs: list[pathlib.Path] = []
    for root, _, files in os.walk(input_dir):
        rootpath = pathlib.Path(root)
        mirrorpath = pathlib.Path(rootpath.as_posix().replace(input_dir, output_dir))
        for f in files:
            if f.endswith(".ttf"):
                output_path = mirrorpath / f
                if not cli_args.force and output_path.exists():
                    continue
                inputs.append(rootpath / f)
                outputs.append(output_path)

    z = list(zip(inputs, outputs))
    if len(z) == 0:
        print("Nothing to do.")
        return
    with tqdm(total=len(z), desc="HINTING") as progress:
        for v, t in z:
            if len(v.name) < POSTFIX_LEN + 3:
                progress.set_postfix_str(v.name + " " * (POSTFIX_LEN + 3 - len(v.name)))
            else:
                progress.set_postfix_str(v.name[:POSTFIX_LEN] + "...")
            t.parent.mkdir(parents=True, exist_ok=True)
            hint(args, v.as_posix(), t.as_posix())
            progress.update()


def hint(args: list[str], input_file: str, output_file: str) -> None:
    try:
        subprocess.run(
            [sys.executable, "-m", "ttfautohint", *args, input_file, output_file],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"error: Failed to ttfautohint: {e.stderr}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Aborting.")
