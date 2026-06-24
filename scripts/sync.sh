#!/bin/bash
# 跨 Agent Skill 同步脚本 v2.0
# 用法: ./sync.sh [agent-name] [--dry-run] [--backup]

set -e

# 配置区
SKILL_REPO="$HOME/JY-agent-skills"
CONFIG_FILE="$SKILL_REPO/config.yaml"

# 默认 Agent 目录（可被 config.yaml 覆盖）
HERMES_SKILLS="${HERMES_SKILLS:-$HOME/.hermes/skills}"
CLAUDE_SKILLS="${CLAUDE_SKILLS:-$HOME/.claude/skills}"
CODEX_SKILLS="${CODEX_SKILLS:-$HOME/.codex/skills}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 显示帮助
show_help() {
    cat << EOF
跨 Agent Skill 同步脚本 v2.0

用法: $0 [选项] [agent-name]

选项:
    --dry-run       只显示将要执行的操作，不实际执行
    --backup        同步前先备份目标目录
    --force         强制覆盖已存在的符号链接
    --verbose       显示详细信息
    -h, --help      显示此帮助信息

Agent 名称:
    hermes          同步到 Hermes
    claude          同步到 Claude Code
    codex           同步到 Codex
    all             同步到所有 Agent（默认）

示例:
    $0 hermes                  # 同步到 Hermes
    $0 claude --dry-run        # 预览同步到 Claude Code
    $0 all --backup            # 备份后同步到所有 Agent
EOF
}

# 解析配置文件（简单YAML解析）
parse_config() {
    if [ -f "$CONFIG_FILE" ]; then
        log_info "读取配置文件: $CONFIG_FILE"
        # 这里可以添加更复杂的YAML解析
        # 目前使用环境变量覆盖
    fi
}

# 备份目录
backup_directory() {
    local target_dir="$1"
    local backup_dir="${target_dir}.backup.$(date +%Y%m%d_%H%M%S)"
    
    if [ -d "$target_dir" ]; then
        log_info "备份目录: $target_dir -> $backup_dir"
        cp -r "$target_dir" "$backup_dir"
        log_info "备份完成: $backup_dir"
    fi
}

# 同步单个 skill
sync_skill() {
    local skill_source="$1"
    local target_dir="$2"
    local skill_name=$(basename "$skill_source")
    local target_path="$target_dir/$skill_name"
    local dry_run="$3"
    local force="$4"
    
    # 检查源目录是否有效（包含SKILL.md）
    if [ ! -f "$skill_source/SKILL.md" ]; then
        log_warn "跳过 $skill_name: 缺少 SKILL.md"
        return 0
    fi
    
    # 检查目标是否已存在
    if [ -L "$target_path" ]; then
        if [ "$force" = "true" ]; then
            log_warn "覆盖已存在的符号链接: $skill_name"
            [ "$dry_run" = "false" ] && rm "$target_path"
        else
            log_info "跳过 $skill_name: 已存在"
            return 0
        fi
    elif [ -d "$target_path" ]; then
        log_warn "跳过 $skill_name: 目标是目录（非符号链接）"
        return 0
    fi
    
    # 执行同步
    if [ "$dry_run" = "true" ]; then
        log_info "[DRY-RUN] 将创建符号链接: $skill_name"
    else
        ln -s "$skill_source" "$target_path"
        log_info "✓ $skill_name"
    fi
}

# 同步到指定 Agent
sync_to_agent() {
    local agent_name="$1"
    local target_dir="$2"
    local source_type="$3"  # shared, hermes, claude-code, codex
    local dry_run="$4"
    local force="$5"
    
    log_info "同步 $source_type -> $agent_name ($target_dir)"
    
    # 确保目标目录存在
    if [ "$dry_run" = "false" ]; then
        mkdir -p "$target_dir"
    fi
    
    # 同步 shared 目录（所有 agent 都需要）
    # 支持两层结构: shared/category/skill-name/
    if [ "$source_type" = "shared" ] || [ "$source_type" = "all" ]; then
        for category in "$SKILL_REPO/shared"/*/; do
            [ -d "$category" ] || continue
            local cat_name=$(basename "$category")
            # 检查是否是分类目录（包含子目录且子目录有SKILL.md）
            local has_skills=false
            for sub in "$category"*/; do
                [ -f "$sub/SKILL.md" ] && has_skills=true && break
            done
            if [ "$has_skills" = "true" ]; then
                # 两层结构: category/skill
                local cat_target="$target_dir/$cat_name"
                [ "$dry_run" = "false" ] && mkdir -p "$cat_target"
                for skill in "$category"*/; do
                    [ -d "$skill" ] && sync_skill "$skill" "$cat_target" "$dry_run" "$force"
                done
            elif [ -f "$category/SKILL.md" ]; then
                # 一层结构: skill 直接在 shared 下
                sync_skill "$category" "$target_dir" "$dry_run" "$force"
            fi
        done
    fi
    
    # 同步 agent 专用目录
    if [ "$source_type" != "shared" ]; then
        local agent_dir="$SKILL_REPO/$source_type"
        if [ -d "$agent_dir" ]; then
            for skill in "$agent_dir"/*/; do
                [ -d "$skill" ] && sync_skill "$skill" "$target_dir" "$dry_run" "$force"
            done
        fi
    fi
}

# 主函数
main() {
    local agent="all"
    local dry_run="false"
    local backup="false"
    local force="false"
    local verbose="false"
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --dry-run)
                dry_run="true"
                shift
                ;;
            --backup)
                backup="true"
                shift
                ;;
            --force)
                force="true"
                shift
                ;;
            --verbose)
                verbose="true"
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            hermes|claude|codex|all)
                agent="$1"
                shift
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 检查仓库目录
    if [ ! -d "$SKILL_REPO" ]; then
        log_error "Skill 仓库不存在: $SKILL_REPO"
        exit 1
    fi
    
    # 解析配置
    parse_config
    
    # 执行同步
    log_info "开始同步 (agent: $agent, dry-run: $dry_run)"
    
    case "$agent" in
        hermes)
            [ "$backup" = "true" ] && backup_directory "$HERMES_SKILLS"
            sync_to_agent "hermes" "$HERMES_SKILLS" "all" "$dry_run" "$force"
            ;;
        claude)
            [ "$backup" = "true" ] && backup_directory "$CLAUDE_SKILLS"
            sync_to_agent "claude" "$CLAUDE_SKILLS" "all" "$dry_run" "$force"
            ;;
        codex)
            [ "$backup" = "true" ] && backup_directory "$CODEX_SKILLS"
            sync_to_agent "codex" "$CODEX_SKILLS" "all" "$dry_run" "$force"
            ;;
        all)
            [ "$backup" = "true" ] && {
                backup_directory "$HERMES_SKILLS"
                backup_directory "$CLAUDE_SKILLS"
                backup_directory "$CODEX_SKILLS"
            }
            sync_to_agent "hermes" "$HERMES_SKILLS" "all" "$dry_run" "$force"
            sync_to_agent "claude" "$CLAUDE_SKILLS" "all" "$dry_run" "$force"
            sync_to_agent "codex" "$CODEX_SKILLS" "all" "$dry_run" "$force"
            ;;
    esac
    
    log_info "同步完成！"
}

# 执行主函数
main "$@"
