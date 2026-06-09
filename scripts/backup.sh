#!/bin/bash
# Skill 备份脚本
# 用法: ./backup.sh [agent-name]

set -e

BACKUP_DIR="$HOME/skill-backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 备份函数
backup_agent() {
    local agent_name="$1"
    local skill_dir="$2"
    local backup_file="$BACKUP_DIR/${agent_name}_${TIMESTAMP}.tar.gz"
    
    if [ -d "$skill_dir" ]; then
        echo "备份 $agent_name: $skill_dir -> $backup_file"
        tar -czf "$backup_file" -C "$(dirname "$skill_dir")" "$(basename "$skill_dir")"
        echo "✓ 备份完成: $backup_file"
    else
        echo "⚠ 跳过 $agent_name: 目录不存在"
    fi
}

# 清理旧备份
cleanup_old_backups() {
    local max_backups=${1:-5}
    local agent_name="$2"
    
    echo "清理旧备份 (保留最近 $max_backups 个)..."
    ls -t "$BACKUP_DIR"/${agent_name}_*.tar.gz 2>/dev/null | tail -n +$((max_backups + 1)) | xargs -r rm -v
}

# 主函数
main() {
    local agent="${1:-all}"
    
    case "$agent" in
        hermes)
            backup_agent "hermes" "$HOME/.hermes/skills"
            cleanup_old_backups 5 "hermes"
            ;;
        claude)
            backup_agent "claude" "$HOME/.claude/skills"
            cleanup_old_backups 5 "claude"
            ;;
        codex)
            backup_agent "codex" "$HOME/.codex/skills"
            cleanup_old_backups 5 "codex"
            ;;
        all)
            backup_agent "hermes" "$HOME/.hermes/skills"
            backup_agent "claude" "$HOME/.claude/skills"
            backup_agent "codex" "$HOME/.codex/skills"
            cleanup_old_backups 5 "hermes"
            cleanup_old_backups 5 "claude"
            cleanup_old_backups 5 "codex"
            ;;
        *)
            echo "用法: $0 [hermes|claude|codex|all]"
            exit 1
            ;;
    esac
    
    echo "备份完成！"
}

main "$@"
