#!/bin/bash
# Skill 恢复脚本
# 用法: ./restore.sh [agent-name] [backup-file]

set -e

BACKUP_DIR="$HOME/skill-backups"

# 列出可用备份
list_backups() {
    local agent_name="$1"
    echo "可用备份:"
    ls -lh "$BACKUP_DIR"/${agent_name}_*.tar.gz 2>/dev/null || echo "  无备份"
}

# 恢复函数
restore_agent() {
    local agent_name="$1"
    local backup_file="$2"
    local target_dir="$3"
    
    if [ ! -f "$backup_file" ]; then
        echo "错误: 备份文件不存在: $backup_file"
        exit 1
    fi
    
    echo "恢复 $agent_name: $backup_file -> $target_dir"
    
    # 备份当前目录
    if [ -d "$target_dir" ]; then
        local current_backup="$BACKUP_DIR/${agent_name}_pre_restore_$(date +%Y%m%d_%H%M%S).tar.gz"
        echo "备份当前目录: $current_backup"
        tar -czf "$current_backup" -C "$(dirname "$target_dir")" "$(basename "$target_dir")"
    fi
    
    # 恢复
    mkdir -p "$(dirname "$target_dir")"
    tar -xzf "$backup_file" -C "$(dirname "$target_dir")"
    echo "✓ 恢复完成"
}

# 主函数
main() {
    local agent="${1:-}"
    local backup_file="${2:-}"
    
    if [ -z "$agent" ]; then
        echo "用法: $0 <agent-name> [backup-file]"
        echo ""
        echo "Agent 名称: hermes, claude, codex"
        echo ""
        echo "示例:"
        echo "  $0 hermes                    # 列出 Hermes 备份"
        echo "  $0 hermes /path/to/backup.tar.gz  # 恢复指定备份"
        exit 1
    fi
    
    # 如果没有指定备份文件，列出可用备份
    if [ -z "$backup_file" ]; then
        list_backups "$agent"
        exit 0
    fi
    
    # 恢复指定备份
    case "$agent" in
        hermes)
            restore_agent "hermes" "$backup_file" "$HOME/.hermes/skills"
            ;;
        claude)
            restore_agent "claude" "$backup_file" "$HOME/.claude/skills"
            ;;
        codex)
            restore_agent "codex" "$backup_file" "$HOME/.codex/skills"
            ;;
        *)
            echo "错误: 未知 agent: $agent"
            exit 1
            ;;
    esac
}

main "$@"
