#!/usr/bin/env python3
"""
抓取 GitHub Wiki 中的 Bash 代码段
排除以指定前缀开头的代码段
"""

import json
import os
import re
import requests
from datetime import datetime
from pathlib import Path


def load_config(config_path="wiki_sources.json"):
    """加载配置文件"""
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_wiki_page(repo: str, page: str, token: str = None) -> str:
    """
    获取 GitLab Wiki 页面的原始 Markdown 内容
    
    GitLab Wiki API 格式:
    https://gitlab.com/api/v4/projects/{project_id}/wikis/{slug}
    
    或直接访问 raw 内容:
    https://gitlab.com/{namespace}/{project}/-/wikis/{page}/raw
    """
    # URL 编码项目路径 (namespace/project -> namespace%2Fproject)
    encoded_repo = repo.replace("/", "%2F")
    
    # 处理页面名称（空格转换为连字符或保持原样）
    page_slug = page.replace(" ", "-")
    
    headers = {}
    if token:
        headers["PRIVATE-TOKEN"] = token
    
    # 尝试多种 URL 格式
    urls = [
        # GitLab API 方式
        f"https://gitlab.com/api/v4/projects/{encoded_repo}/wikis/{page_slug}",
        f"https://gitlab.com/api/v4/projects/{encoded_repo}/wikis/{page}",
        # Raw 内容方式
        f"https://gitlab.com/{repo}/-/wikis/{page_slug}/raw",
        f"https://gitlab.com/{repo}/-/wikis/{page}/raw",
    ]
    
    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                print(f"✓ 成功获取: {repo}/wiki/{page}")
                
                # API 返回 JSON，需要提取 content 字段
                if "/api/v4/" in url:
                    data = response.json()
                    return data.get("content", "")
                else:
                    return response.text
        except requests.RequestException as e:
            print(f"✗ 请求失败 {url}: {e}")
            continue
    
    print(f"✗ 无法获取: {repo}/wiki/{page}")
    return None


def extract_bash_code_blocks(markdown_content: str, exclude_prefixes: list) -> list:
    """
    从 Markdown 内容中提取 Bash 代码段
    排除以指定前缀开头的代码段
    
    支持的格式:
    ```bash
    code here
    ```
    
    ```sh
    code here
    ```
    
    ```shell
    code here
    ```
    """
    # 匹配 bash/sh/shell 代码块
    pattern = r'```(?:bash|sh|shell)\s*\n(.*?)```'
    matches = re.findall(pattern, markdown_content, re.DOTALL | re.IGNORECASE)
    
    filtered_blocks = []
    for block in matches:
        block = block.strip()
        
        # 检查是否以排除的前缀开头
        should_exclude = False
        for prefix in exclude_prefixes:
            if block.lower().startswith(prefix.lower()):
                should_exclude = True
                print(f"  ⊘ 排除以 '{prefix}' 开头的代码段")
                break
        
        if not should_exclude and block:
            filtered_blocks.append(block)
    
    return filtered_blocks


def save_results(results: dict, output_dir: str):
    """保存抓取结果"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # 保存汇总文件
    # summary_file = output_path / "bash_codes_summary.md"
    # with open(summary_file, "w", encoding="utf-8") as f:
        # f.write(f"# Wiki Bash 代码段汇总\n\n")
        # f.write(f"**更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        # f.write("---\n\n")
        
        # for repo, pages in results.items():
            # f.write(f"## 📦 {repo}\n\n")
            # for page, codes in pages.items():
                # f.write(f"### 📄 {page}\n\n")
                # if codes:
                    # for i, code in enumerate(codes, 1):
                        # f.write(f"**代码段 {i}:**\n\n")
                        # f.write(f"```bash\n{code}\n```\n\n")
                # else:
                    # f.write("*没有找到 Bash 代码段*\n\n")
            # f.write("---\n\n")
    
    # print(f"\n✓ 汇总文件已保存: {summary_file}")
    
    # 保存 JSON 格式（便于程序处理）
    # json_file = output_path / "bash_codes.json"
    # with open(json_file, "w", encoding="utf-8") as f:
        # json.dump({
            # "updated_at": datetime.now().isoformat(),
            # "data": results
        # }, f, ensure_ascii=False, indent=2)
    
    # print(f"✓ JSON 文件已保存: {json_file}")
    
    # 保存纯代码文件（每个仓库一个文件）
    for repo, pages in results.items():
        repo_filename = repo.replace("/", "_") + "_bash.sh"
        repo_file = output_path / repo_filename
        
        with open(repo_file, "w", encoding="utf-8") as f:
            # f.write(f"#!/bin/bash\n")
            # f.write(f"# Source: {repo}\n")
            # f.write(f"# Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            # f.write(f"# Auto-generated - DO NOT EDIT\n\n")
            
            for page, codes in pages.items():
                if codes:
                    # f.write(f"# === {page} ===\n\n")
                    for code in codes:
                        f.write(f"{code}\n")
        
        print(f"✓ 仓库代码文件已保存: {repo_file}")


def main():
    """主函数"""
    print("=" * 50)
    print("GitHub Wiki Bash 代码抓取器")
    print("=" * 50 + "\n")
    
    # 加载配置
    config = load_config()
    wiki_pages = config.get("wiki_pages", [])
    exclude_prefixes = config.get("exclude_prefix", ["ssr"])
    output_dir = config.get("output_dir", "output")
    
    # 获取 GitHub Token（可选，用于访问私有仓库）
    token = os.environ.get("GITHUB_TOKEN")
    
    print(f"排除前缀: {exclude_prefixes}")
    print(f"输出目录: {output_dir}\n")
    
    results = {}
    
    for wiki_config in wiki_pages:
        repo = wiki_config["repo"]
        pages = wiki_config["pages"]
        
        print(f"\n📦 处理仓库: {repo}")
        print("-" * 40)
        
        results[repo] = {}
        
        for page in pages:
            print(f"\n  📄 页面: {page}")
            
            # 获取 Wiki 页面内容
            content = fetch_wiki_page(repo, page, token)
            
            if content:
                # 提取 Bash 代码段
                bash_codes = extract_bash_code_blocks(content, exclude_prefixes)
                results[repo][page] = bash_codes
                print(f"     找到 {len(bash_codes)} 个 Bash 代码段")
            else:
                results[repo][page] = []
    
    # 保存结果
    print("\n" + "=" * 50)
    print("保存结果")
    print("=" * 50)
    save_results(results, output_dir)
    
    print("\n✅ 完成!")


if __name__ == "__main__":
    main()
