#!/usr/bin/env python3
"""
三省六部 · 公共工具函数
避免 read_json / now_iso 等基础函数在多个脚本中重复定义
"""
import json, pathlib, datetime, os


def find_project_root() -> pathlib.Path:
    """查找项目根目录，优先级：环境变量 > .edict_env 配置 > 脚本相对路径

    这个函数确保无论脚本从哪里运行（项目目录或 agent workspace），
    都能找到正确的项目根目录和数据目录。
    """
    # 1. 环境变量 EDICT_DATA_DIR 直接指定数据目录
    env_data_dir = os.environ.get('EDICT_DATA_DIR')
    if env_data_dir:
        return pathlib.Path(env_data_dir).parent

    # 2. 从当前目录向上查找 .edict_env 文件
    cwd = pathlib.Path.cwd()
    for p in [cwd] + list(cwd.parents):
        env_file = p / '.edict_env'
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith('EDICT_DATA_DIR='):
                    data_dir = pathlib.Path(line.split('=', 1)[1].strip())
                    return data_dir.parent

    # 3. 脚本所在目录的上两级（项目 scripts/ 目录下运行）
    # 注意：这里使用调用者的 __file__，所以这个函数需要被导入使用
    # 如果直接运行此模块，使用当前文件的位置
    script_dir = pathlib.Path(__file__).resolve().parent
    if (script_dir.parent / 'data').exists() and (script_dir.parent / 'agents').exists():
        return script_dir.parent

    # 4. 默认：当前工作目录
    return cwd


def find_data_dir() -> pathlib.Path:
    """查找数据目录"""
    return find_project_root() / 'data'


def read_json(path, default=None):
    """安全读取 JSON 文件，失败返回 default"""
    try:
        return json.loads(pathlib.Path(path).read_text())
    except Exception:
        return default if default is not None else {}


def now_iso():
    """返回 UTC ISO 8601 时间字符串（末尾 Z）"""
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')


def today_str(fmt='%Y%m%d'):
    """返回今天日期字符串，默认 YYYYMMDD"""
    return datetime.date.today().strftime(fmt)


def safe_name(s: str) -> bool:
    """检查名称是否只含安全字符（字母、数字、下划线、连字符、中文）"""
    import re
    return bool(re.match(r'^[a-zA-Z0-9_\-\u4e00-\u9fff]+$', s))


def validate_url(url: str, allowed_schemes=('https',), allowed_domains=None) -> bool:
    """校验 URL 合法性，防 SSRF"""
    from urllib.parse import urlparse
    try:
        parsed = urlparse(url)
        if parsed.scheme not in allowed_schemes:
            return False
        if allowed_domains and parsed.hostname not in allowed_domains:
            return False
        if not parsed.hostname:
            return False
        # 禁止内网地址
        import ipaddress
        try:
            ip = ipaddress.ip_address(parsed.hostname)
            if ip.is_private or ip.is_loopback or ip.is_reserved:
                return False
        except ValueError:
            pass  # hostname 不是 IP，放行
        return True
    except Exception:
        return False
