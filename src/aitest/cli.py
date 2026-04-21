from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import typer
from dotenv import load_dotenv

app = typer.Typer(add_completion=False)

_SUBCOMMANDS = frozenset({"init", "gen", "gen-all", "run", "heal"})


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> None:
    """入口：无子命令或首参为 pytest 选项/路径时，自动插入 `run`（`aitest -q` 等价 `aitest run -q`）。"""
    argv = sys.argv[1:]
    if not argv:
        sys.argv = [sys.argv[0], "run"]
    elif argv[0] == "help":
        sys.argv = [sys.argv[0], "--help"]
    elif argv[0] not in _SUBCOMMANDS and argv[0] not in ("--help", "-h", "--version"):
        sys.argv = [sys.argv[0], "run", *argv]
    app()


@app.command("init")
def init_cmd() -> None:
    """生成默认目录与示例配置（不覆盖已有文件）。"""
    root = _repo_root()
    (root / "cases").mkdir(parents=True, exist_ok=True)
    (root / "tests" / "generated").mkdir(parents=True, exist_ok=True)
    (root / "reports").mkdir(parents=True, exist_ok=True)

    env_ex = root / ".env.example"
    if not env_ex.is_file():
        env_ex.write_text(
            "LLM_BASE_URL=\nLLM_API_KEY=\nLLM_MODEL=\nTEST_USERNAME=\nTEST_PASSWORD=\n",
            encoding="utf-8",
        )
    cfg = root / "aitest.yaml"
    if not cfg.is_file():
        cfg.write_text(
            "paths:\n  cases: cases\n  generated: tests/generated\n",
            encoding="utf-8",
        )
    typer.echo("init: cases/, tests/generated/, reports/ ready; see .env.example")


@app.command()
def gen(
    case: Path = typer.Argument(..., exists=True, readable=True, path_type=Path),
    out: Path | None = typer.Option(None, "--out", help="生成目录，默认 tests/generated"),
) -> None:
    """根据 Markdown 用例调用 LLM 生成 Playwright+pytest 文件。"""
    load_dotenv()
    from aitest.gen import run_gen

    out_dir = out.resolve() if out else None
    try:
        written = run_gen(case.resolve(), out_dir=out_dir)
    except Exception as exc:  # noqa: BLE001
        typer.secho(f"gen failed: {type(exc).__name__}: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"written: {written}")


@app.command("gen-all")
def gen_all(
    cases_dir: Path | None = typer.Option(
        None,
        "--cases",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        path_type=Path,
        help="用例目录，默认仓库根下 cases/",
    ),
    out: Path | None = typer.Option(
        None,
        "--out",
        path_type=Path,
        help="生成目录，默认 tests/generated",
    ),
    fail_fast: bool = typer.Option(
        False,
        "--fail-fast",
        help="任一条生成失败立即退出（默认：记录错误并继续下一条）",
    ),
    exit_zero: bool = typer.Option(
        False,
        "--exit-zero",
        help="即使有失败也使用进程退出码 0（仍会打印失败列表；适合不想打断脚本的场景）",
    ),
) -> None:
    """对 cases 下所有 .md 逐个执行 gen（每次都会调用 LLM，注意费用与耗时）。"""
    load_dotenv()
    from aitest.gen import run_gen

    root = _repo_root()
    cdir = (cases_dir or root / "cases").resolve()
    out_dir = out.resolve() if out else None
    files = sorted(cdir.glob("*.md"))
    if not files:
        typer.echo(f"no .md under {cdir}", err=True)
        raise typer.Exit(code=1)
    ok: list[Path] = []
    failed: list[tuple[Path, str]] = []
    for f in files:
        typer.echo(f"generating from {f} ...")
        try:
            written = run_gen(f, out_dir=out_dir)
        except Exception as exc:  # noqa: BLE001 — 批量任务需汇总
            msg = f"{type(exc).__name__}: {exc}"
            typer.secho(f"  FAILED: {msg}", fg=typer.colors.RED, err=True)
            failed.append((f, msg))
            if fail_fast:
                raise typer.Exit(code=1) from exc
            continue
        typer.echo(f"  written: {written}")
        ok.append(f)

    typer.echo("")
    typer.echo(f"summary: ok={len(ok)} failed={len(failed)} total={len(files)}")
    for path, msg in failed:
        typer.secho(f"  - {path}: {msg}", fg=typer.colors.RED, err=True)
    if failed and not exit_zero:
        raise typer.Exit(code=1)


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def run(ctx: typer.Context) -> None:
    """运行 pytest；未知参数全部透传。示例: aitest run tests/generated -k baidu -v"""
    load_dotenv()
    root = _repo_root()
    extra = list(ctx.args)
    cmd = [sys.executable, "-m", "pytest", *extra]
    if not extra:
        cmd.append(str(root / "tests"))
    typer.echo(" ".join(cmd))
    raise SystemExit(subprocess.call(cmd, cwd=str(root)))


@app.command()
def heal(
    case_id: str = typer.Argument(..., help="用例 id，与 test_<id>.py 一致"),
    generated: Path | None = typer.Option(None, "--generated", path_type=Path),
    reports: Path | None = typer.Option(None, "--reports", path_type=Path),
) -> None:
    """读取 reports/last_failure.txt 与 tests/generated，输出 heal diff。"""
    load_dotenv()
    from aitest.heal import run_heal

    try:
        out = run_heal(
            case_id=case_id,
            generated_dir=generated.resolve() if generated else None,
            reports_dir=reports.resolve() if reports else None,
        )
    except FileNotFoundError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from exc
    except Exception as exc:  # noqa: BLE001
        typer.secho(f"heal failed: {type(exc).__name__}: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"diff written: {out}")


if __name__ == "__main__":
    main()
