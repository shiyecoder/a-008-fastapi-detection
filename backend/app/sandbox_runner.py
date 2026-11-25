"""
Python 沙箱执行器：在子进程中真实执行目标脚本，并通过 monkey-patch
拦截网络/进程/文件写入/eval/exec 等危险调用，把行为以 JSON 事件流写到 stdout。

被拦截的危险调用不会真实落地（直接抛 PermissionError 或返回空），
因此即使目标文件是真实 webshell，也不会破坏宿主机。

使用方式：
    python sandbox_runner.py <target_file>
输出（stderr 行为流，stdout 留给目标自身输出）：
    __SBX__{"type":"network","addr":"1.2.3.4:80"}
    __SBX__{"type":"process","cmd":"whoami"}
    ...
"""
import sys
import os
import json
import time
import socket
import builtins
import subprocess
import traceback

_EVENTS = []
_T0 = time.time()


def _rec(event_type, **kw):
    """记录一条行为事件并立即刷新到 stderr"""
    ev = {"type": event_type, "ts": round(time.time() - _T0, 4)}
    ev.update(kw)
    _EVENTS.append(ev)
    try:
        sys.stderr.write("__SBX__" + json.dumps(ev, ensure_ascii=False) + "\n")
        sys.stderr.flush()
    except Exception:
        pass


# ---------- 1. 网络层拦截 ----------
_orig_sock_connect = socket.socket.connect
_orig_sock_connect_ex = socket.socket.connect_ex


def _hook_connect(self, addr):
    _rec("network", addr=str(addr), api="socket.connect")
    raise PermissionError("[sandbox] network connect blocked")


def _hook_connect_ex(self, addr):
    _rec("network", addr=str(addr), api="socket.connect_ex")
    return 1


socket.socket.connect = _hook_connect
socket.socket.connect_ex = _hook_connect_ex


def _hook_getaddrinfo(host, *a, **kw):
    _rec("dns", host=str(host))
    return []


socket.getaddrinfo = _hook_getaddrinfo


# ---------- 2. 进程派生拦截 ----------
_orig_popen_init = subprocess.Popen.__init__


def _hook_popen_init(self, args, *a, **kw):
    _rec("process", cmd=str(args)[:300], api="subprocess.Popen")
    raise PermissionError("[sandbox] subprocess blocked")


subprocess.Popen.__init__ = _hook_popen_init


def _hook_os_system(cmd):
    _rec("process", cmd=str(cmd)[:300], api="os.system")
    return 1


os.system = _hook_os_system


_orig_popen = os.popen


def _hook_os_popen(cmd, *a, **kw):
    _rec("process", cmd=str(cmd)[:300], api="os.popen")
    raise PermissionError("[sandbox] os.popen blocked")


os.popen = _hook_os_popen


for _name in ("execv", "execve", "execvp", "execvpe", "execl", "execle", "execlp", "execlpe", "spawnv", "spawnve"):
    if hasattr(os, _name):
        def _make_hook(n):
            def _h(*a, **kw):
                _rec("process", cmd=str(a)[:300], api=f"os.{n}")
                raise PermissionError(f"[sandbox] os.{n} blocked")
            return _h
        setattr(os, _name, _make_hook(_name))


# ---------- 3. 文件写入拦截 ----------
_orig_open = builtins.open
_SANDBOX_DIR = os.environ.get("SBX_DIR", "")


def _hook_open(file, mode="r", *a, **kw):
    try:
        m = str(mode)
        is_write = any(c in m for c in ("w", "a", "+", "x"))
        target_path = str(file)
        # 沙箱目录内的写允许（避免影响目标自身），沙箱目录外的写阻断
        if is_write:
            abs_target = os.path.abspath(target_path) if not target_path.startswith("/dev") else target_path
            in_sandbox = bool(_SANDBOX_DIR) and abs_target.startswith(os.path.abspath(_SANDBOX_DIR))
            _rec("file_write", path=target_path, mode=m, in_sandbox=in_sandbox)
            if not in_sandbox:
                raise PermissionError("[sandbox] file write outside sandbox blocked")
    except PermissionError:
        raise
    except Exception:
        pass
    return _orig_open(file, mode, *a, **kw)


builtins.open = _hook_open


_orig_remove = os.remove


def _hook_remove(path, *a, **kw):
    _rec("file_delete", path=str(path), api="os.remove")
    raise PermissionError("[sandbox] file delete blocked")


os.remove = _hook_remove
os.unlink = _hook_remove


# ---------- 4. 动态代码执行拦截 ----------
_orig_eval = builtins.eval
_orig_exec = builtins.exec


def _hook_eval(src, *a, **kw):
    _rec("eval", code=str(src)[:200], api="builtins.eval")
    return None


def _hook_exec(src, *a, **kw):
    _rec("exec", code=str(src)[:200], api="builtins.exec")
    return None


builtins.eval = _hook_eval
builtins.exec = _hook_exec


_orig_compile = builtins.compile


def _hook_compile(src, *a, **kw):
    _rec("compile", code=str(src)[:200], api="builtins.compile")
    return _orig_compile(src, *a, **kw)


builtins.compile = _hook_compile


# ---------- 5. 敏感路径访问监测 ----------
_orig_listdir = os.listdir
_SENSITIVE = ("/etc/passwd", "/etc/shadow", "C:\\Windows\\System32", "C:\\Windows\\system32")


def _hook_listdir(path="."):
    p = str(path)
    if any(s in p for s in _SENSITIVE):
        _rec("sensitive_access", path=p, api="os.listdir")
    return _orig_listdir(path)


os.listdir = _hook_listdir


# ---------- 6. 执行目标 ----------
def main():
    if len(sys.argv) < 2:
        _rec("error", msg="no target file")
        return 1
    target = sys.argv[1]
    if not os.path.exists(target):
        _rec("error", msg=f"target not found: {target}")
        return 1

    try:
        with open(target, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()
    except Exception as e:
        _rec("error", msg=f"read fail: {e}")
        return 1

    _rec("start", file=target, size=len(code))
    g = {"__name__": "__main__", "__file__": target, "__builtins__": builtins}
    try:
        compiled = _orig_compile(code, target, "exec")
        _orig_exec(compiled, g)
    except SystemExit:
        _rec("exit", reason="SystemExit")
    except PermissionError as e:
        # 被沙箱阻断
        _rec("blocked", msg=str(e))
    except Exception as e:
        _rec("runtime_error", msg=str(e)[:200], tb=traceback.format_exc(limit=2)[:300])
    _rec("end", count=len(_EVENTS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
