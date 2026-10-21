#!/usr/bin/env python3
"""Bounded LSP client for OdooLS workspace-symbol queries."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import queue
import subprocess
import sys
import threading
import time
from typing import Any


def find_binary(explicit: str | None) -> pathlib.Path:
    if explicit:
        path = pathlib.Path(explicit).resolve()
        if path.is_file():
            return path
        raise FileNotFoundError(path)
    for name in ("odoo_ls_server.exe", "odoo_ls_server"):
        for directory in os.environ.get("PATH", "").split(os.pathsep):
            path = pathlib.Path(directory) / name
            if path.is_file():
                return path
    home = pathlib.Path.home()
    candidates = sorted(
        (home / ".vscode" / "extensions").glob("odoo.odoo-*/odoo_ls_server.exe"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if candidates:
        return candidates[0]
    raise FileNotFoundError("odoo_ls_server not found; install the VS Code extension Odoo.odoo")


class LspClient:
    def __init__(self, process: subprocess.Popen[bytes], workspace_folders: list[dict[str, str]]) -> None:
        self.process = process
        self.workspace_folders = workspace_folders
        self.messages: queue.Queue[dict[str, Any]] = queue.Queue()
        self.next_id = 1
        self.ready = threading.Event()
        self.reader = threading.Thread(target=self._read_loop, daemon=True)
        self.reader.start()

    def _read_loop(self) -> None:
        stream = self.process.stdout
        assert stream is not None
        while True:
            headers: dict[str, str] = {}
            while True:
                line = stream.readline()
                if not line:
                    return
                if line in (b"\r\n", b"\n"):
                    break
                key, _, value = line.decode("ascii", errors="replace").partition(":")
                headers[key.lower().strip()] = value.strip()
            length = int(headers.get("content-length", "0"))
            if not length:
                continue
            payload = stream.read(length)
            try:
                self.messages.put(json.loads(payload.decode("utf-8")))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue

    def send(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        framed = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body
        assert self.process.stdin is not None
        self.process.stdin.write(framed)
        self.process.stdin.flush()

    def notify(self, method: str, params: Any = None) -> None:
        payload: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        self.send(payload)

    def request(self, method: str, params: Any, timeout: float) -> Any:
        request_id = self.next_id
        self.next_id += 1
        self.send({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        deadline = time.monotonic() + timeout
        deferred: list[dict[str, Any]] = []
        try:
            while time.monotonic() < deadline:
                remaining = max(0.05, deadline - time.monotonic())
                try:
                    message = self.messages.get(timeout=remaining)
                except queue.Empty:
                    break
                if message.get("id") == request_id and ("result" in message or "error" in message):
                    if "error" in message:
                        raise RuntimeError(json.dumps(message["error"], ensure_ascii=False))
                    return message.get("result")
                if "method" in message and "id" in message:
                    self._respond_to_server(message)
                else:
                    self._handle_notification(message)
        finally:
            for message in deferred:
                self.messages.put(message)
        raise TimeoutError(f"OdooLS request timed out: {method}")

    def _respond_to_server(self, message: dict[str, Any]) -> None:
        method = message.get("method")
        if method == "workspace/configuration":
            items = (message.get("params") or {}).get("items") or []
            result: Any = [None for _ in items]
        elif method == "workspace/workspaceFolders":
            result = self.workspace_folders
        else:
            result = None
        self.send({"jsonrpc": "2.0", "id": message["id"], "result": result})

    def _handle_notification(self, message: dict[str, Any]) -> None:
        if message.get("method") == "$Odoo/loadingStatusUpdate" and message.get("params") == "stop":
            self.ready.set()

    def wait_until_ready(self, timeout: float) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.ready.is_set():
                return True
            try:
                message = self.messages.get(timeout=min(1.0, max(0.05, deadline - time.monotonic())))
            except queue.Empty:
                continue
            if "method" in message and "id" in message:
                self._respond_to_server(message)
            else:
                self._handle_notification(message)
        return self.ready.is_set()


def location_of(symbol: dict[str, Any]) -> tuple[str, int, int]:
    location = symbol.get("location") or {}
    uri = location.get("uri") or ""
    start = ((location.get("range") or {}).get("start") or {})
    path = pathlib.Path(uri.removeprefix("file:///").replace("/", os.sep)) if uri else pathlib.Path()
    return str(path), int(start.get("line", 0)) + 1, int(start.get("character", 0)) + 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Query OdooLS with a bounded workspace-symbol result")
    parser.add_argument("query")
    parser.add_argument("--repo", default=os.getcwd())
    parser.add_argument("--binary")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--log-level", choices=("trace", "debug", "info", "warn", "error"), default="error")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-match", action="store_true")
    args = parser.parse_args()
    if args.limit < 1 or args.limit > 100:
        parser.error("--limit must be between 1 and 100")

    repo = pathlib.Path(args.repo).resolve()
    config = repo / "odools.toml"
    if not config.is_file():
        raise FileNotFoundError(f"missing {config}; run pg_setup_odools.ps1 first")
    binary = find_binary(args.binary)
    command = [str(binary), "--config-path", str(config), "--log-level", args.log_level]
    process = subprocess.Popen(
        command,
        cwd=repo,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    root_uri = repo.as_uri()
    workspace_folders = [{"uri": root_uri, "name": repo.name}]
    client = LspClient(process, workspace_folders)
    try:
        client.request(
            "initialize",
            {
                "processId": os.getpid(),
                "rootUri": root_uri,
                "workspaceFolders": workspace_folders,
                "capabilities": {
                    "window": {"workDoneProgress": True},
                    "workspace": {"workspaceFolders": True, "symbol": {}},
                    "textDocument": {},
                },
                "clientInfo": {"name": "pg-odoo-navigator", "version": "1.0"},
            },
            min(args.timeout, 60.0),
        )
        client.notify("initialized", {})
        started = time.monotonic()
        ready = client.wait_until_ready(max(1.0, args.timeout - (time.monotonic() - started)))
        if not ready:
            raise TimeoutError(f"OdooLS indexing did not become ready within {args.timeout:.0f}s")
        response = client.request("workspace/symbol", {"query": args.query}, min(30.0, args.timeout))
        result: list[dict[str, Any]] = list(response or [])
        bounded = result[: args.limit]
        normalized = []
        for symbol in bounded:
            path, line, column = location_of(symbol)
            normalized.append(
                {
                    "name": symbol.get("name"),
                    "kind": symbol.get("kind"),
                    "container": symbol.get("containerName"),
                    "path": path,
                    "line": line,
                    "column": column,
                }
            )
        payload = {
            "query": args.query,
            "repo": str(repo),
            "binary": str(binary),
            "index_ready": ready,
            "returned": len(normalized),
            "truncated": len(result) > len(normalized),
            "symbols": normalized,
        }
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"OdooLS: {len(normalized)} result(s) for {args.query!r}")
            for item in normalized:
                print(f"{item['name']}\t{item['path']}:{item['line']}:{item['column']}")
        if args.require_match and not normalized:
            return 4
        return 0
    finally:
        try:
            client.request("shutdown", None, 3.0)
            client.notify("exit")
        except (BrokenPipeError, OSError, RuntimeError, TimeoutError):
            pass
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # concise, machine-friendly failure
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
