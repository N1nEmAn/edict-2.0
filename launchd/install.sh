#!/bin/bash
# ══════════════════════════════════════════════════════════════
# 三省六部 · macOS 服务安装脚本
# ══════════════════════════════════════════════════════════════

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LAUNCHD_SRC="$REPO_DIR/launchd"
LAUNCHD_DST="$HOME/Library/LaunchAgents"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# 更新 plist 文件中的路径占位符
update_plists() {
    info "更新配置文件路径..."
    for plist in "$LAUNCHD_SRC"/*.plist; do
        if [ -f "$plist" ]; then
            sed -i.bak "s|__REPO_DIR__|$REPO_DIR|g" "$plist"
            rm -f "${plist}.bak"
        fi
    done
}

# 安装服务
install_services() {
    mkdir -p "$LAUNCHD_DST"

    for plist in "$LAUNCHD_SRC"/*.plist; do
        if [ -f "$plist" ]; then
            name=$(basename "$plist")
            cp "$plist" "$LAUNCHD_DST/$name"
            log "已安装: $name"
        fi
    done

    log "服务配置已安装到: $LAUNCHD_DST"
}

# 启动服务
start_services() {
    for plist in "$LAUNCHD_DST"/com.edict.*.plist; do
        if [ -f "$plist" ]; then
            launchctl load "$plist" 2>/dev/null || true
        fi
    done
    log "服务已启动"
}

# 停止服务
stop_services() {
    for plist in "$LAUNCHD_DST"/com.edict.*.plist; do
        if [ -f "$plist" ]; then
            launchctl unload "$plist" 2>/dev/null || true
        fi
    done
    log "服务已停止"
}

# 查看状态
status() {
    echo ""
    echo "=== 三省六部服务状态 ==="
    launchctl list | grep com.edict || echo "无运行中的服务"
    echo ""
    echo "日志位置:"
    echo "  /tmp/edict-refresh.log"
    echo "  /tmp/edict-dashboard.log"
}

# 卸载服务
uninstall_services() {
    stop_services
    rm -f "$LAUNCHD_DST"/com.edict.*.plist
    log "服务已卸载"
}

case "${1:-install}" in
    install)
        update_plists
        install_services
        start_services
        status
        ;;
    start)
        start_services
        status
        ;;
    stop)
        stop_services
        ;;
    status)
        status
        ;;
    uninstall)
        uninstall_services
        ;;
    update)
        update_plists
        log "配置已更新，请运行 '$0 stop && $0 start' 重启服务"
        ;;
    *)
        cat << 'EOF'
三省六部 · macOS 服务管理

用法:
  ./launchd/install.sh install    安装并启动服务
  ./launchd/install.sh start      启动服务
  ./launchd/install.sh stop       停止服务
  ./launchd/install.sh status     查看状态
  ./launchd/install.sh uninstall  卸载服务
  ./launchd/install.sh update     更新配置（仓库路径变化后执行）

服务列表:
  com.edict.refresh   - 数据刷新循环（每15秒）
  com.edict.dashboard - 看板服务器（端口7891）

日志位置:
  /tmp/edict-refresh.log
  /tmp/edict-dashboard.log
EOF
        ;;
esac
