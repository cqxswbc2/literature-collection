# Literature Collection（文献搜集）

一个 Claude Code / Codex skill：端到端搜集学术文献，交付三样东西：**文献清单**、**按期刊归档好的全文文件夹**、**下载情况总结**。

流程按《文献检索、文献阅读与文献综述》课程的方法：确定主题 → 选库 → 布尔检索式 → 学术过滤器（期刊白名单）→ 先读综述再顺藤摸瓜（参考文献与施引文献）→ 分层获取全文 → 逐篇核对 → 归档 → 总结。

## 它做什么

- 写布尔检索式，跑 OpenAlex、Web of Science、出版社平台、CNKI。
- 用学校期刊目录做白名单：只保留指定档次的期刊（附西南财经大学 2025 目录中 business / management 类 A1 及以上的外文期刊）。
- 对种子论文做施引文献追踪，并标出清单里已有的条目。
- 分层获取全文：开放获取直链 → 机构仓储与作者版本（SSRN、作者主页）→ 用户浏览器 + 学校权限（CARSI）→ 文献传递。
- 每个 PDF 都按 DOI 或标题核对身份后再归档，命名为 `年份_第一作者_短标题.pdf`。
- 生成下载情况总结：哪些拿到了、走的哪条渠道、哪些还缺、怎么补。

## 合规原则

- 只走合法渠道：出版社开放获取、机构仓储、学校订阅、图书馆文献传递、作者邮件。不用 Sci-Hub、LibGen 之类。
- 不代做人机验证，不输入账号密码，不改浏览器的安全设置。需要时请用户自己操作。
- 扫描下载目录时只看匹配到的文献，不打印用户其他文件的名字。

## 目录结构

```text
.
├── SKILL.md                         # 触发说明 + 操作流程
├── agents/openai.yaml
├── references/
│   ├── databases.md                 # 数据库怎么选；CARSI 与学校订阅情况；各平台下载要点
│   └── query_templates.md           # 检索式语法与 URL 模板
├── scripts/
│   ├── openalex_search.py           # 关键词检索 + 施引追踪，按期刊白名单过滤
│   ├── oa_lookup.py                 # 查开放获取版本并下载（OpenAlex + Unpaywall）
│   ├── archive_pdfs.py              # 按 DOI / 标题核对 PDF 身份并归档
│   └── make_summary.py              # 生成下载情况总结
└── assets/
    ├── manifest_template.csv        # 文献清单模板
    └── swufe_2025_business_management_A1plus.csv   # 期刊白名单示例
```

## 安装

```bash
git clone https://github.com/cqxswbc2/literature-collection.git ~/.claude/skills/literature-collection
# Codex：~/.codex/skills/literature-collection
```

脚本只用 Python 标准库，另需 `pypdf`（`archive_pdfs.py` 读 PDF 文本时使用）：

```bash
pip install pypdf
```

## 使用

```text
帮我找 influencer 和 MCN 相关的论文，只要学校目录里 A1 及以上的 business/management 期刊。
```

```text
用学校权限把清单里缺全文的论文下载下来，下完核对并归档。
```

## 脚本示例

```bash
# 白名单检索 + 施引追踪
python scripts/openalex_search.py --whitelist assets/swufe_2025_business_management_A1plus.csv \
  --cites 10.1287/mnsc.2023.03479 --query "influencer" --query "content creator" \
  --manifest manifest.csv --email you@example.com --out candidates.csv

# 查开放获取版本并下载到暂存文件夹
python scripts/oa_lookup.py manifest.csv --email you@example.com --download staging

# 核对并归档（先演练，确认后加 --apply）
python scripts/archive_pdfs.py manifest.csv --src staging --dest 已下载论文 --since-hours 48

# 生成下载情况总结
python scripts/make_summary.py manifest.csv --dest 已下载论文
```

## 关于学校订阅信息

`references/databases.md` 里的 CARSI 与订阅情况是 2026 年 10 月对西南财经大学的实测记录，资源会调整（试用尤其变化快）。换学校或过一段时间请重新查。

## 配合使用

全文拿到后，可以用 [paper-summary-slides](https://github.com/cqxswbc2/paper-summary-slides) 逐篇做一页总结 PPT。

见 [DISCLAIMER](DISCLAIMER.md)。
