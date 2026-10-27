"""Shared helpers for SigmaOS-common (inspired by mintcommon).

Provides a safe config get/set layer (atomic writes, dotted keys), an xrandr
command planner (pure -- never executed here), and the standard SigmaOS
path layout. Everything is injectable so the whole module tests without
touching a real system.
"""
import argparse, json, os, sys, tempfile

ENGINE = {
    "name": "sigma-common",
    "summary": "Shared config helpers, xrandr planning, standard paths",
    "language": "python",
    "verbs": ["config-get", "config-set", "xrandr-plan", "paths"],
    "principles": ["DRY", "Information Hiding", "Defensive Programming",
                   "Fail-Fast", "KISS", "Deterministic Testing"],
}

cli_doc = """\
$ sigma-common config-get --file app.conf --key ui.theme
$ sigma-common config-set --file app.conf --key ui.theme --value dark --type str
$ sigma-common config-set --file app.conf --key ui.scale --value 1.25 --type float
$ sigma-common xrandr-plan --output eDP-1 --mode 1920x1080 --pos 0x0 --primary
$ sigma-common paths
"""

DEFAULT_CONFIG_DIR = os.path.expanduser("~/.config/sigmaos")

STD_PATHS = {
    "config_dir": "~/.config/sigmaos",
    "state_dir": "~/.local/state/sigmaos",
    "cache_dir": "~/.cache/sigmaos",
    "log_dir": "~/.local/state/sigmaos/log",
    "data_dir": "~/.local/share/sigmaos",
    "run_dir": "/run/sigmaos",
    "system_config": "/etc/sigmaos",
}


class CommonError(Exception):
    pass


def load_config(path):
    """Parse a nested config file: 'a.b.c = value' lines, '#' comments."""
    config = {}
    if not os.path.exists(path):
        return config
    with open(path, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                raise CommonError(f"{path}:{lineno}: expected key = value")
            key, _, raw = line.partition("=")
            key, raw = key.strip(), raw.strip()
            if not key:
                raise CommonError(f"{path}:{lineno}: empty key")
            node = config
            parts = key.split(".")
            for part in parts[:-1]:
                node = node.setdefault(part, {})
                if not isinstance(node, dict):
                    raise CommonError(f"{path}:{lineno}: key conflict at {key!r}")
            node[parts[-1]] = _coerce(raw)
    return config


def _coerce(raw):
    """Infer a scalar type from config syntax."""
    if raw.startswith('"') and raw.endswith('"') and len(raw) >= 2:
        return raw[1:-1]
    if raw.lower() in ("true", "false"):
        return raw.lower() == "true"
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    return raw


def save_config(path, config):
    """Write nested config as dotted lines, sorted, with atomic replace."""
    lines = []

    def walk(node, prefix):
        for k in sorted(node):
            key = f"{prefix}.{k}" if prefix else k
            v = node[k]
            if isinstance(v, dict):
                walk(v, key)
            else:
                lines.append(f"{key} = {_format(v)}")

    walk(config, "")
    body = "\n".join(lines) + ("\n" if lines else "")
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=directory or ".", prefix=".sigma-conf-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(body)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def _format(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, str):
        return f'"{v}"'
    return str(v)


def config_get(config, dotted_key):
    node = config
    for part in dotted_key.split("."):
        if not isinstance(node, dict) or part not in node:
            raise CommonError(f"no such key: {dotted_key}")
        node = node[part]
    return node


def config_set(config, dotted_key, value):
    """Pure mutation on an in-memory dict; returns the same dict."""
    parts = dotted_key.split(".")
    if any(not p for p in parts):
        raise CommonError(f"invalid key: {dotted_key!r}")
    node = config
    for part in parts[:-1]:
        nxt = node.setdefault(part, {})
        if not isinstance(nxt, dict):
            raise CommonError(f"key conflict at {dotted_key}")
        node = nxt
    node[parts[-1]] = value
    return config


def xrandr_plan(outputs):
    """Pure: build one xrandr command from output dicts (validates modes).

    outputs: [{"name": "eDP-1", "mode": "1920x1080", "pos": "0x0",
               "rate": 60.0, "primary": True, "rotate": "normal",
               "scale": "1x1"}, ...]
    """
    if not outputs:
        raise CommonError("no outputs given")
    seen, primaries, cmd = set(), 0, ["xrandr"]
    for out in outputs:
        name = out.get("name", "")
        if not name or not all(c.isalnum() or c in "-_" for c in name):
            raise CommonError(f"bad output name: {name!r}")
        if name in seen:
            raise CommonError(f"duplicate output: {name}")
        seen.add(name)
        mode = out.get("mode")
        if mode is not None:
            if not re_mode(mode):
                raise CommonError(f"bad mode {mode!r}; expected WxH")
            cmd.append(f"--output {name} --mode {mode}")
        elif out.get("off"):
            cmd.append(f"--output {name} --off")
            continue
        else:
            cmd.append(f"--output {name} --auto")
        rate = out.get("rate")
        if rate is not None:
            if not isinstance(rate, (int, float)) or not (0 < rate <= 500):
                raise CommonError(f"bad refresh rate: {rate!r}")
            cmd.append(f"--rate {rate}")
        pos = out.get("pos")
        if pos is not None:
            if not re_pos(pos):
                raise CommonError(f"bad position {pos!r}; expected XxY")
            cmd.append(f"--pos {pos}")
        rotate = out.get("rotate", "normal")
        if rotate not in ("normal", "left", "right", "inverted"):
            raise CommonError(f"bad rotation: {rotate!r}")
        if rotate != "normal":
            cmd.append(f"--rotate {rotate}")
        scale = out.get("scale")
        if scale is not None:
            if not re_mode(scale):
                raise CommonError(f"bad scale {scale!r}; expected XxY")
            cmd.append(f"--scale {scale}")
        if out.get("primary"):
            primaries += 1
            cmd.append("--primary")
    if primaries > 1:
        raise CommonError("only one output may be primary")
    return " ".join(cmd)


def re_mode(s):
    """WxH / XxY shape check (shared by modes, positions, scales)."""
    if not isinstance(s, str) or "x" not in s:
        return False
    a, _, b = s.partition("x")
    return (a.isdigit() and b.isdigit() and int(a) > 0 and int(b) > 0
            and len(a) <= 5 and len(b) <= 5)


def re_pos(s):
    """Like re_mode but zero allowed (screen origins can be 0x0)."""
    if not isinstance(s, str) or "x" not in s:
        return False
    a, _, b = s.partition("x")
    return (a.isdigit() and b.isdigit() and len(a) <= 5 and len(b) <= 5)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog=ENGINE["name"], description=ENGINE["summary"])
    sub = p.add_subparsers(dest="cmd", required=True)
    cg = sub.add_parser("config-get", help="read a dotted config key")
    cg.add_argument("--file", required=True)
    cg.add_argument("--key", required=True)
    cs = sub.add_parser("config-set", help="write a dotted config key")
    cs.add_argument("--file", required=True)
    cs.add_argument("--key", required=True)
    cs.add_argument("--value", required=True)
    cs.add_argument("--type", default="str", dest="vtype",
                    choices=["str", "int", "float", "bool"])
    xr = sub.add_parser("xrandr-plan", help="print an xrandr command (dry-run)")
    xr.add_argument("--output", required=True)
    xr.add_argument("--mode", default=None)
    xr.add_argument("--pos", default=None)
    xr.add_argument("--rate", type=float, default=None)
    xr.add_argument("--primary", action="store_true")
    xr.add_argument("--rotate", default="normal")
    xr.add_argument("--scale", default=None)
    xr.add_argument("--off", action="store_true")
    sub.add_parser("paths", help="print the standard SigmaOS path layout")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.cmd == "config-get":
            print(json.dumps(config_get(load_config(args.file), args.key)))
        elif args.cmd == "config-set":
            cfg = load_config(args.file)
            value = {"str": args.value, "int": int(args.value),
                     "float": float(args.value),
                     "bool": args.value.lower() in ("1", "true", "yes")}[args.vtype]
            config_set(cfg, args.key, value)
            save_config(args.file, cfg)
            print(f"set {args.key} = {_format(value)}")
        elif args.cmd == "xrandr-plan":
            out = {"name": args.output, "mode": args.mode, "pos": args.pos,
                   "rate": args.rate, "primary": args.primary,
                   "rotate": args.rotate, "scale": args.scale, "off": args.off}
            print(xrandr_plan([{k: v for k, v in out.items()
                                if v not in (None, False)}]))
        elif args.cmd == "paths":
            for name, path in sorted(STD_PATHS.items()):
                print(f"{name}: {path}")
        return 0
    except (CommonError, OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


def self_test() -> None:
    # pure config layer
    cfg = {}
    config_set(cfg, "ui.theme", "dark")
    config_set(cfg, "ui.scale", 1.25)
    config_set(cfg, "hotkeys.lock", "<Super>l")
    config_set(cfg, "telemetry", False)
    assert config_get(cfg, "ui.theme") == "dark"
    assert config_get(cfg, "ui.scale") == 1.25
    assert config_get(cfg, "telemetry") is False
    try:
        config_get(cfg, "ui.nope")
    except CommonError as e:
        assert "no such key" in str(e)
    else:
        raise AssertionError("missing key not caught")
    try:
        config_set(cfg, "ui.theme.mode", "x")  # ui.theme is a str
    except CommonError as e:
        assert "conflict" in str(e)
    else:
        raise AssertionError("key conflict not caught")
    try:
        config_get(cfg, "")
    except CommonError:
        pass
    else:
        raise AssertionError("empty key not caught")

    # file round-trip with atomic write
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "conf", "app.conf")
        save_config(path, cfg)
        body = open(path).read()
        assert 'hotkeys.lock = "<Super>l"' in body
        assert "telemetry = false" in body
        assert body.index("hotkeys.lock") < body.index("ui.scale")  # sorted
        assert load_config(path) == cfg
        # comments, blanks, quoted strings, ints, floats, bools
        open(path, "a").write("# comment\n\nui.extra = \"x y\"\nui.n = 42\n")
        cfg2 = load_config(path)
        assert cfg2["ui"]["extra"] == "x y" and cfg2["ui"]["n"] == 42
        open(path, "a").write("not a valid line\n")
        try:
            load_config(path)
        except CommonError as e:
            assert "expected key = value" in str(e)
        else:
            raise AssertionError("malformed line not caught")
        assert load_config(os.path.join(d, "missing.conf")) == {}

    # xrandr planner
    cmd = xrandr_plan([
        {"name": "eDP-1", "mode": "1920x1080", "pos": "0x0", "rate": 60,
         "primary": True},
        {"name": "HDMI-1", "mode": "2560x1440", "pos": "1920x0", "rate": 144},
    ])
    assert cmd.startswith("xrandr --output eDP-1 --mode 1920x1080")
    assert "--primary" in cmd and "--output HDMI-1" in cmd
    assert xrandr_plan([{"name": "DP-1", "off": True}]) == "xrandr --output DP-1 --off"
    assert "--rotate inverted" in xrandr_plan(
        [{"name": "DP-2", "mode": "1080x1920", "rotate": "inverted"}])
    for bad in ([], [{"name": "eDP 1"}], [{"name": "X", "mode": "fullhd"}],
                [{"name": "A", "pos": "west"}], [{"name": "A", "rate": 999}],
                [{"name": "A", "scale": "big"}]):
        try:
            xrandr_plan(bad)
        except CommonError:
            pass
        else:
            raise AssertionError(f"not rejected: {bad}")
    try:
        xrandr_plan([{"name": "A", "primary": True}, {"name": "B", "primary": True}])
    except CommonError as e:
        assert "primary" in str(e)
    else:
        raise AssertionError("dual primary not caught")

    assert set(STD_PATHS) >= {"config_dir", "state_dir", "cache_dir", "run_dir"}


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
