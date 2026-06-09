#!/bin/bash
# Skills 更新脚本
# 根据 SOURCES.md 中记录的仓库，自动更新 skills

set -e

REPO_DIR="$HOME/JY-agent-skills"
SOURCES_FILE="$REPO_DIR/SOURCES.md"
TEMP_DIR="/tmp/skill-update-$$"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 显示帮助
show_help() {
    cat << EOF
Skills 更新脚本

用法: $0 [选项] [repo-name]

选项:
    --dry-run       只显示将要执行的操作
    --force         强制覆盖（即使没有变化）
    -h, --help      显示帮助信息

参数:
    repo-name       指定要更新的仓库（默认更新所有）

示例:
    $0                          # 更新所有仓库
    $0 sugarforever/01coder-agent-skills  # 更新指定仓库
    $0 --dry-run                # 预览更新
EOF
}

# 解析 SOURCES.md 获取仓库列表
parse_sources() {
    # 提取仓库信息（跳过表头）
    grep -E "^\| [^|]+ \| https://" "$SOURCES_FILE" | while IFS='|' read -r _ repo url _ _; do
        repo=$(echo "$repo" | xargs)
        url=$(echo "$url" | xargs)
        if [ -n "$repo" ] && [ -n "$url" ]; then
            echo "$repo|$url"
        fi
    done
}

# 克隆或更新仓库
update_repo() {
    local repo_name="$1"
    local repo_url="$2"
    local temp_repo="$TEMP_DIR/$repo_name"
    
    log_info "处理仓库: $repo_name"
    
    # 克隆或拉取
    if [ -d "$temp_repo" ]; then
        log_info "  更新已有仓库..."
        cd "$temp_repo"
        git pull --quiet
    else
        log_info "  克隆仓库..."
        mkdir -p "$(dirname "$temp_repo")"
        git clone --quiet "$repo_url" "$temp_repo"
    fi
    
    # 检查 skills 目录
    if [ ! -d "$temp_repo/skills" ]; then
        log_warn "  跳过: 未找到 skills/ 目录"
        return 0
    fi
    
    # 统计 skills
    local skill_count=$(ls -d "$temp_repo/skills"/*/ 2>/dev/null | wc -l)
    log_info "  发现 $skill_count 个 skills"
    
    echo "$temp_repo"
}

# 分析 skill 类型
classify_skill() {
    local skill_dir="$1"
    local skill_md="$skill_dir/SKILL.md"
    
    if [ ! -f "$skill_md" ]; then
        echo "unknown"
        return
    fi
    
    # 提取 description
    local desc=$(grep -A 5 "^description:" "$skill_md" | head -1)
    
    # Claude Code 专用关键词
    local claude_keywords="claude code|claude-code|claude session|~/.claude|codex session|codex cli|~/.codex|codex-session|mining session|interactive-input"
    
    if echo "$desc" | grep -qiE "$claude_keywords"; then
        echo "claude-code"
    else
        echo "shared"
    fi
}

# 同步 skills
sync_skills() {
    local source_dir="$1"
    local repo_name="$2"
    local dry_run="$3"
    local force="$4"
    
    local updated=0
    local added=0
    local skipped=0
    
    for skill_dir in "$source_dir"/skills/*/; do
        [ -d "$skill_dir" ] || continue
        
        local skill_name=$(basename "$skill_dir")
        local skill_type=$(classify_skill "$skill_dir")
        local target_dir="$REPO_DIR/$skill_type/$skill_name"
        
        # 检查是否有变化
        if [ -d "$target_dir" ] && [ "$force" != "true" ]; then
            # 比较 SKILL.md 是否有变化
            if diff -q "$skill_dir/SKILL.md" "$target_dir/SKILL.md" > /dev/null 2>&1; then
                skipped=$((skipped + 1))
                continue
            fi
        fi
        
        if [ "$dry_run" = "true" ]; then
            if [ -d "$target_dir" ]; then
                log_info "  [DRY-RUN] 更新: $skill_name -> $skill_type/"
            else
                log_info "  [DRY-RUN] 新增: $skill_name -> $skill_type/"
            fi
        else
            if [ -d "$target_dir" ]; then
                log_info "  更新: $skill_name -> $skill_type/"
                rm -rf "$target_dir"
                updated=$((updated + 1))
            else
                log_info "  新增: $skill_name -> $skill_type/"
                added=$((added + 1))
            fi
            cp -r "$skill_dir" "$target_dir"
        fi
    done
    
    echo "  统计: 新增=$added, 更新=$updated, 跳过=$skipped"
}

# 主函数
main() {
    local dry_run="false"
    local force="false"
    local target_repo=""
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --dry-run)
                dry_run="true"
                shift
                ;;
            --force)
                force="true"
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                target_repo="$1"
                shift
                ;;
        esac
    done
    
    # 检查仓库目录
    if [ ! -d "$REPO_DIR" ]; then
        log_error "仓库目录不存在: $REPO_DIR"
        exit 1
    fi
    
    # 检查 SOURCES.md
    if [ ! -f "$SOURCES_FILE" ]; then
        log_error "SOURCES.md 不存在"
        exit 1
    fi
    
    # 创建临时目录
    mkdir -p "$TEMP_DIR"
    trap "rm -rf $TEMP_DIR" EXIT
    
    log_info "开始更新 skills..."
    
    # 解析仓库列表
    local repos=$(parse_sources)
    
    if [ -z "$repos" ]; then
        log_warn "未找到任何仓库"
        exit 0
    fi
    
    # 遍历仓库
    echo "$repos" | while IFS='|' read -r repo_name repo_url; do
        # 如果指定了仓库，只更新该仓库
        if [ -n "$target_repo" ] && [ "$repo_name" != "$target_repo" ]; then
            continue
        fi
        
        # 克隆/更新仓库
        local temp_repo=$(update_repo "$repo_name" "$repo_url")
        
        if [ -n "$temp_repo" ] && [ -d "$temp_repo/skills" ]; then
            # 同步 skills
            sync_skills "$temp_repo" "$repo_name" "$dry_run" "$force"
        fi
    done
    
    if [ "$dry_run" = "true" ]; then
        log_info "预览完成（未实际修改）"
    else
        log_info "更新完成！"
        log_info "请手动提交变更:"
        echo "  cd $REPO_DIR"
        echo "  git add ."
        echo "  git commit -m \"更新 skills\""
        echo "  git push"
    fi
}

main "$@"
