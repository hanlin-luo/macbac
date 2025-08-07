#!/bin/bash
# SSH 和 Hosts 文件备份脚本
# backup_ssh_hosts.sh

set -euo pipefail

# 配置变量
BACKUP_DIR="${HOME}/os_backups/ssh_hosts"
TIMESTAMP=$(date "+%Y%m%d_%H%M%S")
BACKUP_ARCHIVE="${BACKUP_DIR}/ssh_hosts_backup_${TIMESTAMP}.tar.gz"
LOG_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.log"

# 源路径
SSH_DIR="${HOME}/.ssh"
HOSTS_FILE="/etc/hosts"
BACKUP_HOSTS_FILE="/etc/hosts.backup"

# 创建备份目录
mkdir -p "${BACKUP_DIR}"

# 日志函数
log() {
    # 将日志同时输出到 stderr 和日志文件，避免干扰 stdout
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}" >&2
}

# 错误处理函数
error_exit() {
    log "ERROR: $1"
    exit 1
}

# 检查权限函数
check_permissions() {
    if [[ ! -r "${SSH_DIR}" ]]; then
        error_exit "无法读取 SSH 目录: ${SSH_DIR}"
    fi
    
    if [[ ! -r "${HOSTS_FILE}" ]]; then
        error_exit "无法读取 hosts 文件: ${HOSTS_FILE}"
    fi
}

# 备份 SSH 配置
backup_ssh() {
    log "开始备份 SSH 配置..."
    
    local temp_dir="$1"
    if [[ -z "${temp_dir}" ]]; then
        error_exit "backup_ssh 需要一个临时目录作为参数"
    fi

    if [[ ! -d "${SSH_DIR}" ]]; then
        log "警告: SSH 目录不存在: ${SSH_DIR}"
        return 1 # 返回非零表示有警告，但不一定是致命错误
    fi
    
    # 在临时目录中创建 ssh 目录
    local ssh_backup_target_dir="${temp_dir}/ssh"
    mkdir -p "${ssh_backup_target_dir}"
    
    # 复制 SSH 目录内容
    # 使用 cp -a 来保留权限和属性，-v 用于日志记录（可选）
    cp -a "${SSH_DIR}/." "${ssh_backup_target_dir}/"
    
    # 生成 SSH 文件清单
    find "${ssh_backup_target_dir}" -type f -exec ls -la {} \; > "${temp_dir}/ssh_file_list.txt"
    
    # 检查关键文件
    local key_files=("config" "known_hosts" "authorized_keys")
    for file in "${key_files[@]}"; do
        if [[ -f "${ssh_backup_target_dir}/${file}" ]]; then
            log "  ✓ 发现并备份: ${file}"
        else
            log "  - 未发现: ${file}"
        fi
    done
    
    # 检查私钥文件（通常没有扩展名或 .pem）
    local key_count=0
    while IFS= read -r -d '' file; do
        # 排除公钥和其他非密钥文件
        if [[ ! "$file" =~ \.pub$ && $(basename "$file") != "known_hosts" && $(basename "$file") != "authorized_keys" && $(basename "$file") != "config" ]]; then
            ((key_count++))
            log "  ✓ 发现私钥文件: $(basename "$file")"
        fi
    done < <(find "${ssh_backup_target_dir}" -type f -print0)
    
    log "SSH 备份完成 - 共发现 ${key_count} 个可能的私钥文件"
    
    return 0
}

# 备份 hosts 文件
backup_hosts() {
    log "开始备份 hosts 文件..."
    
    local temp_dir="$1"
    local hosts_backup_dir="${temp_dir}/hosts"
    mkdir -p "${hosts_backup_dir}"
    
    # 备份主 hosts 文件
    cp "${HOSTS_FILE}" "${hosts_backup_dir}/hosts"
    log "  ✓ 备份主 hosts 文件"
    
    # 备份可能存在的备份文件
    if [[ -f "${BACKUP_HOSTS_FILE}" ]]; then
        cp "${BACKUP_HOSTS_FILE}" "${hosts_backup_dir}/hosts.backup"
        log "  ✓ 备份 hosts.backup 文件"
    fi
    
    # 生成 hosts 文件信息
    {
        echo "=== Hosts 文件信息 ==="
        echo "文件路径: ${HOSTS_FILE}"
        echo "文件大小: $(ls -lh "${HOSTS_FILE}" | awk '{print $5}')"
        echo "修改时间: $(ls -l "${HOSTS_FILE}" | awk '{print $6, $7, $8}')"
        echo ""
        echo "=== 自定义条目 (非默认系统条目) ==="
        grep -v "^#" "${HOSTS_FILE}" | grep -v "^$" | grep -v "127.0.0.1.*localhost" | grep -v "::1.*localhost" | grep -v "255.255.255.255.*broadcasthost"
    } > "${hosts_backup_dir}/hosts_info.txt"
    
    log "Hosts 文件备份完成"
}

# 创建备份压缩包
create_archive() {
    local temp_dir="$1"
    log "创建备份压缩包..."
    
    # 创建备份信息文件
    {
        echo "=== SSH 和 Hosts 备份信息 ==="
        echo "备份时间: $(date)"
        echo "主机名: $(hostname)"
        echo "用户: $(whoami)"
        echo "系统: $(uname -a)"
        echo ""
        echo "=== 备份内容 ==="
        echo "- SSH 配置目录: ${SSH_DIR}"
        echo "- Hosts 文件: ${HOSTS_FILE}"
        echo ""
        echo "=== 文件清单 ==="
        find "${temp_dir}" -type f -exec ls -la {} \;
    } > "${temp_dir}/backup_info.txt"
    
    # 创建压缩包，直接输出到目标路径
    tar -czf "${BACKUP_ARCHIVE}" -C "${temp_dir}" .
    
    log "备份压缩包已创建: ${BACKUP_ARCHIVE}"
    log "压缩包大小: $(ls -lh "${BACKUP_ARCHIVE}" | awk '{print $5}')"
}

# 声明一个全局变量来持有临时目录的路径
declare temp_dir=""

# 清理临时文件
cleanup() {
    if [[ -n "${temp_dir:-}" && -d "${temp_dir}" ]]; then
        rm -rf "${temp_dir}"
        log "清理临时文件完成"
    fi
}

# 设置陷阱以确保清理
# trap cleanup EXIT ERR 应该在 temp_dir 创建后设置，以避免意外删除

# 主函数
main() {
    # 在脚本开始时就设置陷阱，但 cleanup 函数会检查 temp_dir 是否存在
    trap cleanup EXIT ERR

    log "=== SSH 和 Hosts 备份开始 ==="
    log "备份目录: ${BACKUP_DIR}"
    
    # 检查权限
    check_permissions
    
    # 创建临时目录并赋值给全局变量
    temp_dir=$(mktemp -d)

    # 执行备份
    backup_ssh "${temp_dir}"
    backup_hosts "${temp_dir}"
    create_archive "${temp_dir}" || error_exit "备份过程失败"

    
    log "=== 备份完成 ==="
    log "备份文件: ${BACKUP_ARCHIVE}"
    log "日志文件: ${LOG_FILE}"
    
    # 显示备份摘要
    echo ""
    echo "🎉 备份成功完成!"
    echo "📁 备份文件: ${BACKUP_ARCHIVE}"
    echo "📋 日志文件: ${LOG_FILE}"
    echo "💾 压缩包大小: $(ls -lh "${BACKUP_ARCHIVE}" | awk '{print $5}')"
    echo ""
    echo "💡 恢复命令:"
    echo "   bash 2_ssh_hosts_restore.sh \"${BACKUP_ARCHIVE}\""
}

# 运行主函数
main "$@"