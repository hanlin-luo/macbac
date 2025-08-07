#!/bin/bash
# SSH 和 Hosts 文件恢复脚本
# restore_ssh_hosts.sh

set -euo pipefail

# 配置变量
RESTORE_DIR_BASE="${HOME}/restore_ssh_hosts"
TIMESTAMP=$(date "+%Y%m%d_%H%M%S")

# 动态设置的目标路径
SSH_DIR=""
HOSTS_FILE=""
RESTORE_DIR="" # 将在 main 函数中设置
LOG_FILE="" # 将在 main 函数中设置
PRODUCTION_MODE=false

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >&2
}

# 错误处理函数
error_exit() {
    log "ERROR: $1"
    exit 1
}

# 显示帮助信息
show_help() {
    cat << EOF
SSH 和 Hosts 文件恢复脚本

用法: $0 <备份文件路径> [选项]

参数:
  备份文件路径    备份的 .tar.gz 文件路径

选项:
  -h, --help     显示帮助信息
  -f, --force    强制覆盖现有文件（默认会备份现有文件）
  -d, --dry-run  预览模式，显示将要执行的操作但不实际执行
  -s, --ssh-only 仅恢复 SSH 配置
  -H, --hosts-only 仅恢复 hosts 文件
  --production   执行实际恢复到系统目录（默认是测试模式）
  --test         执行测试恢复到备份文件所在目录（默认行为）

示例:
  $0 ~/backup_ssh_hosts/ssh_hosts_backup_20231201_143022.tar.gz
  $0 backup.tar.gz --dry-run
  $0 backup.tar.gz --ssh-only --force

EOF
}

# 解析命令行参数
parse_args() {
    BACKUP_FILE=""
    FORCE_OVERWRITE=false
    DRY_RUN=false
    SSH_ONLY=false
    HOSTS_ONLY=false
    TEST_MODE=true # 默认开启测试模式
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -f|--force)
                FORCE_OVERWRITE=true
                shift
                ;;
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -s|--ssh-only)
                SSH_ONLY=true
                shift
                ;;
            -H|--hosts-only)
                HOSTS_ONLY=true
                shift
                ;;
            --production)
                PRODUCTION_MODE=true
                TEST_MODE=false
                shift
                ;;
            --test)
                TEST_MODE=true
                PRODUCTION_MODE=false
                shift
                ;;
            -*)
                error_exit "未知选项: $1"
                ;;
            *)
                if [[ -z "${BACKUP_FILE}" ]]; then
                    BACKUP_FILE="$1"
                else
                    error_exit "只能指定一个备份文件"
                fi
                shift
                ;;
        esac
    done
    
    # 验证参数
    if [[ -z "${BACKUP_FILE}" ]]; then
        error_exit "请指定备份文件路径"
    fi
    
    if [[ "${SSH_ONLY}" == true && "${HOSTS_ONLY}" == true ]]; then
        error_exit "--ssh-only 和 --hosts-only 不能同时使用"
    fi
}

# 验证备份文件
validate_backup() {
    log "验证备份文件: ${BACKUP_FILE}"
    
    if [[ ! -f "${BACKUP_FILE}" ]]; then
        error_exit "备份文件不存在: ${BACKUP_FILE}"
    fi
    
    if [[ ! "${BACKUP_FILE}" =~ \.tar\.gz$ ]]; then
        log "警告: 备份文件扩展名不是 .tar.gz"
    fi
    
    # 测试解压
    if ! tar -tzf "${BACKUP_FILE}" >/dev/null 2>&1; then
        error_exit "备份文件损坏或格式不正确"
    fi
    
    log "备份文件验证通过"
}

# 解压备份文件
extract_backup() {
    log "解压备份文件..."
    
    local extract_dir="${RESTORE_DIR}/extracted_${TIMESTAMP}"
    mkdir -p "${extract_dir}"
    
    if ! tar -xzf "${BACKUP_FILE}" -C "${extract_dir}" --strip-components=1; then
        error_exit "解压备份文件失败。请检查文件是否有效以及是否包含预期的目录结构。"
    fi
    
    log "备份文件已解压到: ${extract_dir}"
    
    # 显示备份信息
    if [[ -f "${extract_dir}/backup_info.txt" ]]; then
        log "备份信息:"
        cat "${extract_dir}/backup_info.txt" >> "${LOG_FILE}"
    fi
    
    echo "${extract_dir}"
}

# 备份现有文件（仅在生产模式下）
backup_existing() {
    if [[ "${PRODUCTION_MODE}" != true ]]; then
        log "测试模式下跳过备份现有文件"
        return
    fi

    local backup_existing_dir="${RESTORE_DIR}/existing_backup_${TIMESTAMP}"
    mkdir -p "${backup_existing_dir}"
    
    log "备份现有文件到: ${backup_existing_dir}"
    
    # 备份现有 SSH 目录
    if [[ -d "${SSH_DIR}" && "${HOSTS_ONLY}" != true ]]; then
        cp -R "${SSH_DIR}" "${backup_existing_dir}/ssh"
        log "  ✓ 已备份现有 SSH 配置"
    fi
    
    # 备份现有 hosts 文件
    if [[ -f "${HOSTS_FILE}" && "${SSH_ONLY}" != true ]]; then
        cp "${HOSTS_FILE}" "${backup_existing_dir}/hosts"
        log "  ✓ 已备份现有 hosts 文件"
    fi
}

# 恢复 SSH 配置
restore_ssh() {
    local extract_dir="$1"

    log "[DEBUG] Contents of extract_dir (${extract_dir}):"
    ls -la "${extract_dir}" >> "${LOG_FILE}" 2>&1 || log "[DEBUG] ls command failed for ${extract_dir}, continuing..."

    local ssh_backup_dir="${extract_dir}/ssh"

    log "[DEBUG] Checking for main backup directory: ${ssh_backup_dir}"

    # 增加对旧格式 (.ssh) 的兼容性
    if [[ ! -d "${ssh_backup_dir}" && -d "${extract_dir}/.ssh" ]]; then
        log "信息: 检测到旧的备份格式 (.ssh)，将使用它进行恢复。"
        ssh_backup_dir="${extract_dir}/.ssh"
        log "[DEBUG] Now checking for legacy backup directory: ${ssh_backup_dir}"
    fi
    
    if [[ "${HOSTS_ONLY}" == true ]]; then
        return 0
    fi
    
    log "恢复 SSH 配置..."
    
    if [[ ! -d "${ssh_backup_dir}" ]]; then
        log "警告: 备份中未找到 SSH 配置目录"
        log "[DEBUG] Directory check failed for: ${ssh_backup_dir}"
        return 1
    fi
    
    if [[ "${DRY_RUN}" == true ]]; then
        log "[预览] 将恢复 SSH 配置到: ${SSH_DIR}"
        find "${ssh_backup_dir}" -type f -exec echo "  [预览] 恢复文件: {}" \;
        return 0
    fi
    
    # 创建 SSH 目录（如果不存在）
    mkdir -p "${SSH_DIR}"
    
    # 创建目标目录
    mkdir -p "${SSH_DIR}"

    # 恢复文件，-a 选项可以保留文件属性，包括权限
    cp -av "${ssh_backup_dir}/." "${SSH_DIR}/"
    
    # 显式设置关键目录和文件的权限以确保安全
    chmod 700 "${SSH_DIR}"
    find "${SSH_DIR}" -type f -name "id_*" ! -name "*.pub" -exec chmod 600 {} \;
    find "${SSH_DIR}" -type f -name "*.pub" -exec chmod 644 {} \;
    [[ -f "${SSH_DIR}/config" ]] && chmod 600 "${SSH_DIR}/config"
    [[ -f "${SSH_DIR}/known_hosts" ]] && chmod 644 "${SSH_DIR}/known_hosts"
    [[ -f "${SSH_DIR}/authorized_keys" ]] && chmod 600 "${SSH_DIR}/authorized_keys"

    log "  ✓ SSH 配置恢复完成"
    log "  ✓ 权限设置完成"
    
    # 显示恢复的文件
    log "恢复的 SSH 文件:"
    ls -la "${SSH_DIR}" | while read line; do
        log "    ${line}"
    done
}

# 恢复 hosts 文件
restore_hosts() {
    local extract_dir="$1"
    local hosts_backup_dir="${extract_dir}/hosts"
    
    if [[ "${SSH_ONLY}" == true ]]; then
        return 0
    fi
    
    log "恢复 hosts 文件..."
    
    if [[ ! -d "${hosts_backup_dir}" ]]; then
        log "警告: 备份中未找到 hosts 配置目录"
        return 1
    fi
    
    local hosts_backup_file="${hosts_backup_dir}/hosts"
    if [[ ! -f "${hosts_backup_file}" ]]; then
        log "警告: 备份中未找到 hosts 文件"
        return 1
    fi
    
    if [[ "${DRY_RUN}" == true ]]; then
        log "[预览] 将恢复 hosts 文件到: ${HOSTS_FILE}"
        log "[预览] 备份的 hosts 内容:"
        cat "${hosts_backup_file}" | head -10 | while read line; do
            log "    [预览] ${line}"
        done
        return 0
    fi
    
    # 恢复 hosts 文件
    if [[ "${PRODUCTION_MODE}" == true ]]; then
        log "需要管理员权限来恢复 hosts 文件..."
        sudo cp "${hosts_backup_file}" "${HOSTS_FILE}"
    else
        cp "${hosts_backup_file}" "${HOSTS_FILE}"
    fi
    
    log "  ✓ hosts 文件恢复完成"
    
    # 显示恢复后的 hosts 文件摘要
    log "恢复的 hosts 文件内容 (前10行):"
    head -10 "${HOSTS_FILE}" | while read line; do
        log "    ${line}"
    done
}

# 验证恢复结果
verify_restore() {
    log "验证恢复结果..."
    
    local success=true
    
    # 验证 SSH 配置
    if [[ "${HOSTS_ONLY}" != true ]]; then
        if [[ -d "${SSH_DIR}" ]]; then
            log "  ✓ SSH 目录存在: ${SSH_DIR}"
            
            if [[ "${PRODUCTION_MODE}" == true ]]; then
                # 检查权限（使用 stat -f 在 macOS 上更可靠）
                local ssh_perm=$(stat -f "%Lp" "${SSH_DIR}")
                if [[ "${ssh_perm}" == "700" ]]; then
                    log "  ✓ SSH 目录权限正确: ${ssh_perm}"
                else
                    log "  ⚠ SSH 目录权限可能不正确: ${ssh_perm} (应为 700)"
                fi
            fi
        else
            log "  ✗ SSH 目录不存在"
            success=false
        fi
    fi
    
    # 验证 hosts 文件
    if [[ "${SSH_ONLY}" != true ]]; then
        if [[ -f "${HOSTS_FILE}" ]]; then
            log "  ✓ hosts 文件存在: ${HOSTS_FILE}"
        else
            log "  ✗ hosts 文件不存在"
            success=false
        fi
    fi
    
    if [[ "${success}" == true ]]; then
        log "✅ 恢复验证成功"
    else
        log "❌ 恢复验证失败"
        return 1
    fi
}

# 清理临时文件
cleanup() {
    if [[ -n "${extract_dir:-}" && -d "${extract_dir}" && "${PRODUCTION_MODE}" == true ]]; then
        rm -rf "${extract_dir}"
        log "清理临时文件完成"
    elif [[ -n "${extract_dir:-}" && -d "${extract_dir}" ]]; then
        log "测试模式下保留解压目录: ${extract_dir}"
    fi
}

# 主函数
main() {
    # 解析参数，但不立即记录日志
    parse_args "$@"

    # 根据模式设置路径
    if [[ "${PRODUCTION_MODE}" == true ]]; then
        RESTORE_DIR="${RESTORE_DIR_BASE}"
        SSH_DIR="${HOME}/.ssh"
        HOSTS_FILE="/etc/hosts"
    else # 测试模式
        local backup_dir
        backup_dir=$(dirname "${BACKUP_FILE}")
        RESTORE_DIR="${backup_dir}/restore_test_${TIMESTAMP}"
        SSH_DIR="${RESTORE_DIR}/ssh"
        HOSTS_FILE="${RESTORE_DIR}/hosts"
    fi

    # 现在设置日志文件并创建目录
    mkdir -p "${RESTORE_DIR}"
    LOG_FILE="${RESTORE_DIR}/restore_${TIMESTAMP}.log"

    # 将所有输出重定向到日志文件
    exec > >(tee -a "${LOG_FILE}") 2>&1

    log "=== SSH 和 Hosts 恢复开始 ==="
    
    # 显示配置
    log "恢复配置:"
    log "  备份文件: ${BACKUP_FILE}"
    log "  强制覆盖: ${FORCE_OVERWRITE}"
    log "  预览模式: ${DRY_RUN}"
    log "  仅 SSH: ${SSH_ONLY}"
    log "  仅 Hosts: ${HOSTS_ONLY}"
    log "  生产模式: ${PRODUCTION_MODE}"
    
    # 验证备份文件
    validate_backup
    
    # 解压备份
    local extract_dir
    extract_dir=$(extract_backup)
    
    # 备份现有文件（如果需要）
    if [[ "${FORCE_OVERWRITE}" != true && "${DRY_RUN}" != true ]]; then
        backup_existing
    fi
    
    # 执行恢复
    restore_ssh "${extract_dir}"
    restore_hosts "${extract_dir}"
    
    # 验证恢复结果
    if [[ "${DRY_RUN}" != true ]]; then
        verify_restore
    fi
    
    # 清理
    cleanup
    
    log "=== 恢复完成 ==="
    
    # 显示完成摘要
    if [[ "${DRY_RUN}" == true ]]; then
        echo ""
        echo "🔍 预览模式完成!"
        echo "📋 日志文件: ${LOG_FILE}"
        echo ""
        echo "💡 要执行实际恢复，请移除 --dry-run 参数，并使用 --production 参数。"
    elif [[ "${PRODUCTION_MODE}" != true ]]; then
        echo ""
        echo "✅ 测试恢复成功完成!"
        echo "恢复的文件位于: ${RESTORE_DIR}"
        echo "📋 日志文件: ${LOG_FILE}"
        echo ""
        echo "💡 要执行到系统的实际恢复，请使用 --production 参数。"
    else
        echo ""
        echo "🎉 生产恢复成功完成!"
        echo "📋 日志文件: ${LOG_FILE}"
        echo ""
        echo "⚠️  重要提醒:"
        if [[ "${HOSTS_ONLY}" != true ]]; then
            echo "   • SSH 密钥已恢复，请验证连接是否正常"
            echo "   • 检查 ~/.ssh/config 中的主机配置"
        fi
        if [[ "${SSH_ONLY}" != true ]]; then
            echo "   • hosts 文件已更新，可能需要清除 DNS 缓存"
            echo "   • 命令: sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder"
        fi
        echo ""
        echo "📁 现有文件已备份到: ${RESTORE_DIR_BASE}/existing_backup_${TIMESTAMP}"
    fi
}

# 设置陷阱以确保清理
trap cleanup EXIT ERR

# 运行主函数
main "$@"