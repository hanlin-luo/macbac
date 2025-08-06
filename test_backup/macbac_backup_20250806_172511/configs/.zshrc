#!/usr/bin/env zsh
# 模块化的 Zsh 配置文件
# 主配置文件，负责加载各个功能模块

# Amazon Q pre block. Keep at the top of this file.
[[ -f "${HOME}/Library/Application Support/amazon-q/shell/zshrc.pre.zsh" ]] && builtin source "${HOME}/Library/Application Support/amazon-q/shell/zshrc.pre.zsh"

# 配置模块目录
ZSH_CONFIG_DIR="$HOME/.zsh"

# 加载配置模块的函数
load_zsh_module() {
  local module="$1"
  local module_file="$ZSH_CONFIG_DIR/$module.zsh"
  
  if [[ -f "$module_file" ]]; then
    source "$module_file"
  else
    echo "Warning: Zsh module '$module' not found at $module_file"
  fi
}

# 按顺序加载各个配置模块
# 1. 环境变量配置（优先级最高）
load_zsh_module "environment"

# 2. PATH 配置
load_zsh_module "path"

# 3. Oh My Zsh 配置
load_zsh_module "oh-my-zsh"

# 4. Node.js 相关配置
load_zsh_module "nodejs"

# 5. API 密钥配置
load_zsh_module "api-keys"

# 6. 别名配置
load_zsh_module "aliases"

# 7. 自定义函数
load_zsh_module "functions"

# 8. 代理配置
load_zsh_module "proxy"

# 9. 主题和提示符配置（最后加载）
load_zsh_module "theme"

# Amazon Q post block. Keep at the bottom of this file.
[[ -f "${HOME}/Library/Application Support/amazon-q/shell/zshrc.post.zsh" ]] && builtin source "${HOME}/Library/Application Support/amazon-q/shell/zshrc.post.zsh"

# 配置加载完成提示（可选，调试时启用）
# echo "✅ Zsh configuration loaded successfully"
