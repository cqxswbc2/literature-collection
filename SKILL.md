---
name: "literature-collection"
description: "端到端搜集学术文献：按课程方法（确定主题→选库→布尔检索式→学术过滤器→先读综述再顺藤摸瓜）检索中英文文献，筛选好期刊和高被引，整理成文献清单，再分层获取全文（OA直链→机构仓储副本→用户浏览器+学校权限→文献传递），逐篇核对DOI和标题后按「年份_作者_短标题」归档，最后生成下载情况总结。Use when the user asks to find/collect/download papers for a thesis, literature review, or a supervisor's request (e.g. 帮我查文献、找某主题的论文、下载某期刊的文章、用学校数据库下文献、整理文献清单、问卷数据相关文献). Covers ScienceDirect, OpenAlex, Unpaywall, Web of Science, CNKI. Do not use for writing the literature review itself or for citation formatting only."
---

# 文献搜集 Skill（检索 → 筛选 → 获取 → 核对 → 归档 → 总结）

这套流程来自一次真实的「居民需求响应 + 问卷数据」文献搜集，方法依据是课程《文献检索、文献阅读与文献综述》。
目标是交付三样东西：**文献清单**、**按期刊归档好的全文文件夹**，以及**下载情况总结**。

## 0. 硬性规则（先读）

- **不代做人机验证**：滑块、"Are you a robot?"、Security verification、Cloudflare 一律停下，请用户自己完成。
- **不输入账号密码**：学校统一身份认证、CARSI 机构登录、个人登录都由用户自己操作。
- **不改浏览器的安全或站点设置**：比如"允许自动下载多个文件"、"PDF 直接下载"。给用户具体步骤，让用户自己改。
- **只走合法渠道**：出版社开放获取、机构仓储、学校订阅、图书馆文献传递、作者邮件。**不用** Sci-Hub、LibGen、Z-Library 之类。
- **不删用户文件**：误下的、重复的文件移进回收站（可还原）；和任务无关的文件一律不碰。
- **隐私**：扫描下载目录时只报告匹配到的文献，**不要把用户其他文件的文件名打印或复述出来**。
- **每篇都要核对**：出版社返回的可能是 HTML 跳转页，仓储页面也可能挂错文件。没核对过的不能算"下好了"。

## 1. 明确需求（开工前问清或自行判断）

| 要确认的 | 默认值 |
|---|---|
| 主题和关键词（中英文） | 从用户原话里提取，再补上同义词 |
| 期刊档次 | 领域顶刊加能源/经济类好期刊；中文看 CSSCI、北大核心、CSCD。**老师给了学校期刊目录时，以目录为准，先把符合要求的期刊做成白名单 CSV（期刊名、ISSN、级别），后面检索只保留白名单内的结果**。西财 2025 目录里 business/management 类 A1 及以上的外文期刊已整理在 `assets/swufe_2025_business_management_A1plus.csv`（按目录的"学科"列筛选：BUSINESS、BUSINESS，FINANCE、MANAGEMENT、OPERATIONS RESEARCH & MANAGEMENT SCIENCE；不含 MIS、COMMUNICATION、ECONOMICS 类） |
| 年份 | 近 10 年为主，经典高被引文献不限 |
| 特殊要求 | 例如"要有问卷数据"→ 加上 survey / questionnaire / choice experiment / stated preference / willingness to pay 这类词 |
| 交付位置 | 当前工作目录下建 `已下载论文/英文/<期刊>/`、`已下载论文/中文/期刊论文|学位论文/` |
| 数量 | 硕士论文要求不少于 50 篇，英文至少占三分之一，并且要有近一两年的文献 |

## 2. 检索（按课件方法）

详细的检索式语法和 URL 模板见 `references/query_templates.md`，数据库怎么选见 `references/databases.md`。

1. **写布尔检索式**：概念 A（同义词 OR 连起来）AND 概念 B AND 概念 C。英文先用中等宽度跑一遍，噪声大就加限定词。
2. **先抓综述**：Review、meta-analysis、systematic review 各找 3–6 篇。这是后面顺藤摸瓜的种子。
3. **按期刊过滤检索**（学术过滤器）：在出版社平台上用期刊限定 URL 逐本期刊跑，比如 ScienceDirect 的 `&pub=Energy%20Economics`。
4. **跨出版社补漏**：用 OpenAlex API 查 Elsevier 以外的期刊（Nature Energy、The Energy Journal、Springer、AEA、OUP 等）。有期刊白名单时用 `scripts/openalex_search.py`：关键词检索（`--query`）和施引文献追踪（`--cites DOI`）都只保留白名单期刊，并标出 manifest 里已有的条目，只需筛新的。学校有 Web of Science 的话也可以用它看施引文献（西财可以通过 CARSI 使用 WoS，见 `references/databases.md` 第六节）。
   - OpenAlex 的检索**一定会做词干化**："influencer" 会匹配到 "influence"，噪声极大，API 没有关闭的办法（`.no_stem` 在 title_and_abstract 上会报 400）。脚本已改为取回后再要求每个检索词在标题或摘要里按词首原样出现。
   - OpenAlex 的 cursor 翻页在第二页起会返回 401（没有 API key 时），脚本改用 `page=` 翻页。
5. **中文用 CNKI**：主题检索（SU），运算符是 `*`（与）、`+`（或）、`-`（非），检索框最多 120 个字符。
   - **注意同名不同义**：例如"需求响应"同时指电力需求响应和"需求响应式公交"。必须加一组领域限定词，比如 `*('用电'+'电价'+'电力')`。
   - 看左侧"来源类别/学科"的分组数字。比如"CSSCI 只有 16 篇、电力工业 877 篇"，这种结构差距本身就能写进"研究空白"。
6. **顺藤摸瓜**：读综述的参考文献往前追，看施引文献往后追。老师给了种子论文时，对每篇都跑一次 `openalex_search.py --cites <DOI>`；很新的论文（当年发表）施引文献可能是 0，属正常。
7. **研究报告和政策**（写背景时用）：IEA、行业协会、研究院报告，相关部委的政策文件。
8. **筛选分层**：先按标题粗筛，再读摘要，把候选分成 core（直接回答研究问题，要精读、做总结）和 backup（相关但不直接，只列清单）。manifest 里加 `tier`、`topic`、`level` 三列记录结果。

## 3. 筛选并写文献清单

- 标准：权威期刊、高被引、近期、和研究问题直接相关；"直接对标"的 1–3 篇要特别标出来。
- 标记：`★` 表示精读，`【OA】` 表示开放获取（补充材料里常常附有完整问卷）。
- 清单写成 Markdown，按「综述 / 能源经济顶刊 / 各期刊 / 中文 / 经济学必引基石」分节，每条写上 作者—题目—期刊年份—数据与方法。
- 同时把要下载的文献写进 `manifest.csv`（模板在 `assets/manifest_template.csv`），后面所有脚本都靠它。

## 4. 分层获取全文（从易到难）

| 层级 | 渠道 | 怎么做 | 常见坑 |
|---|---|---|---|
| 1 | 出版社 OA 直链 | `oa_lookup.py --download` | ScienceDirect、Elsevier 对脚本请求返回 403，脚本会自动跳过 |
| 2 | 机构仓储副本（Unpaywall 查 repository） | 同上，脚本会去仓储页面里找 PDF | **仓储页面可能挂着别的文件**（实际遇到过西语硕士论文、RMI 行业报告被当成目标文献），必须核对；**Research Square 等预印本平台的版本标题和内容可能和正式版不同**，脚本已跳过，不要当全文用 |
| 3 | 用户的真实浏览器加学校权限 | **先查 `references/databases.md` 第六节，确认学校订没订这个平台**。机构登录统一走 CARSI：https://ds.carsi.edu.cn/login/index.html（用户自己登录）。然后用浏览器自动化（如 playwright skill、Chrome 扩展）打开 DOI → 点 View PDF / PDF下载 | 学校没订的平台（如 Nature、JSTOR、IEEE）不要反复试，直接走第 4 层；见下方「浏览器下载要点」 |
| 4 | 学校没订的 | 图书馆文献传递或馆际互借（CALIS、NSTL）、给通讯作者发邮件、找 JSTOR / NBER / SSRN 上的版本 | 写进总结的"还没下载"一节 |

### 浏览器下载要点（实际踩过的坑）

- **先确认学校权限真的生效**：文章页出现 "Brought to you by: <学校>" 才算登录上。登录后仍然跳到 `/abs/`（只有摘要），说明**学校没订这本期刊**，不要反复重试。
- **出口 IP 问题**：用户开着境外代理时，出版社看不到校园 IP（例如验证页上的 IP 不是学校的、下载链接里带 `cc=us`）。解决办法是让用户点 "Access through your organization" 搜学校做机构登录，或者把出版社域名设成直连。
- **Elsevier 的人机校验**：脚本或自动化去点 PDF，很容易落到 `crasolve` 或 "Security verification" 页。先只自动打开文章页、核对有没有权限；**真正点 View PDF 交给用户**最快。用户点完、文件进了下载目录，再交给 `archive_pdfs.py`。
- **Nature 系列（nature.com）同样拦脚本**：对脚本只返回 2KB 的 HTML。Nature Communications 全部开放获取、Nature Energy 部分开放获取，但都要用浏览器下载。实测**在浏览器里直接打开 `https://www.nature.com/articles/<文章编号>.pdf` 就会下载**，点页面上的按钮反而没反应；老文章的编号要去掉点号（`nenergy.2017.73` → `nenergy201773`）。地址跳回文章页就说明没权限。页面上的 "Supplementary Information (download PDF)" 是补充材料，不是正文，别点错。OpenAlex 标成 OA 的 Nature 文章，可能只是 Research Square 上有预印本，nature.com 上照样要订阅。注意 Nature 子刊属于 Springer Nature，**ScienceDirect 里搜不到**，要单独用 OpenAlex（先查正确的期刊 ID：`/sources?search=Nature Energy`）或 Web of Science 检索。
- **Chrome 默认在浏览器里打开 PDF**，自动化工具进不去这个阅读器页面。请用户把 `chrome://settings/content/pdfDocuments` 改成"下载 PDF 文件"。
- **CNKI**：
  - 下载链接（`bar.cnki.net/bar/download/order?...`）会校验来源页，**直接打开会报"来源应用不正确"**，必须从文章页点。
  - 链接默认 `target=_blank`，弹窗容易被拦。可以先去掉 target 再点。
  - 检索结果页的"下载"默认给 **CAJ**；要 PDF，进**文章详情页**点「PDF下载」。
  - 按篇名定位用 `https://kns.cnki.net/kns8s/defaultresult/index?korder=TI&kw=<篇名>`。结果第一条不一定是目标，**用标题关键词匹配后再点**。标题很像的文章不少，比如"……诉求研究"和"……诉求分析"是两篇不同的。
  - 连续批量下载会触发 Chrome 的"阻止多个自动下载"，请用户在 `chrome://settings/content/automaticDownloads` 里允许 `[*.]cnki.net`。
  - 请求太频繁时结果区会显示为空，等几秒、换更短的关键词再试。
- **CARSI 登录了不等于出版社认得你**：每个出版社要在文章页走一次机构登录，之后同一平台的其他文章就都能用了。
  - **Springer**：文章页点 "Log in via an institution" → wayf 页用脚本给 `#autocomplete-input` 赋值并触发 input 事件 → 选学校 → 点 "Access through your institution"，回到文章页显示 "Access provided by <学校>"。下载用页面内 `fetch('https://link.springer.com/content/pdf/<DOI>.pdf',{credentials:'include'})` 取 blob，再用带 `download` 属性的链接存盘，**不经过 PDF 阅读器，最稳**。OA 文章可以直接 curl 同一地址。
  - **OUP（academic.oup.com）**：右上角 "Sign in through your institution" → Shibboleth 发现页用脚本给 `#idpFilterSubstring` 赋值，点学校。PDF 链接（`/article-pdf/...pdf`）会跳到 silverchair CDN，页面内 fetch 被跨域拦截；**直接在标签页打开这个链接就会下载**。
  - **Wiley**：先看是否 Open Access；PDF 用 `https://<子域>.onlinelibrary.wiley.com/doi/pdfdirect/<DOI>?download=true` 打开即下载。文章页会先出现"请稍候…"（Cloudflare），等 10 秒左右。
  - **SAGE**：OA 文章用 `https://journals.sagepub.com/doi/pdf/<DOI>?download=true`。西财的 Sage 在 CARSI 上是"试用(待申请)"，机构列表里也搜不到学校，**订阅文章下不了**，直接走作者版本或文献传递。
  - **EBSCO**：从 CARSI 资源页进入时报 "Authentication Error Code 103"，EBSCO 自己的机构搜索里也找不到西财，暂时不能用来补 AMJ、MISQ。
- **找作者版本**（学校没订、OA 也没有时）：
  - Semantic Scholar API `https://api.semanticscholar.org/graph/v1/paper/DOI:<DOI>?fields=openAccessPdf` 常能给出 OpenAlex 没收录的 SSRN 链接。
  - Google Scholar 每条结果右侧的 "[PDF]" 链接常指向作者主页或 SSRN。在 scholar.google.com 页面里用 fetch 逐条查（间隔几秒），出现 "unusual traffic" 就立刻停。单次 JS 执行有约 45 秒上限，批量查询要放后台、把结果存在 `window` 变量里再读。
  - SSRN 下载：摘要页的 "Download This Paper" 有时点了没反应，可以直接打开它的 `Delivery.cfm?abstractid=<编号>` 地址。连续下第二篇起会被 Chrome 的"阻止多个自动下载"拦住，请用户在 `chrome://settings/content/automaticDownloads` 里允许 `[*.]ssrn.com`。SSRN 版本是工作论文，**在 manifest 的 note 里注明"工作论文版，引用以正式版为准"**。SSRN 页面先出现"请稍候…"（Cloudflare），要等 15–20 秒再找下载链接；大文件（100 多页）可能要过一两分钟才出现在下载目录，别急着判定失败。
- **扫描下载目录时只列最近几分钟的 PDF**（如 `find <下载目录> -name "*.pdf" -mmin -10`），不要 `ls` 整个目录，避免把用户其他文件名打印出来。
- **下载目录不一定在 C 盘**：Windows 的「下载」可能被改到别的盘。用注册表查实际位置：`HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders` 里的 `{374DE290-123F-4565-9164-39C4925E467B}`。
- **浏览器给文件起的名字不可靠**：可能是 `main.pdf`、`1-s2.0-<PII>-main.pdf`，或者完整标题。不要靠文件名判断是哪一篇。

## 5. 核对与归档

```bash
# 先演练，不移动任何文件
python scripts/archive_pdfs.py manifest.csv --src "<下载目录>" --dest "已下载论文" --since-hours 48
# 确认无误后真正移动，并把状态写回 manifest
python scripts/archive_pdfs.py manifest.csv --src "<下载目录>" --dest "已下载论文" --since-hours 48 --apply
```

核对逻辑（脚本里已经实现）：
1. 文件头必须是 `%PDF`。约 50KB 的"PDF"往往是 HTML 跳转页。
2. 身份识别按优先级：XMP 元数据里的 `prism:doi` → 前两页文字里出现 manifest 中的 DOI → 前两页出现 `match_phrase`（标题短语，去掉空格和标点后匹配）。
   - **不能拿文件里第一个出现的 DOI 当本文 DOI**，那常常是参考文献的。
3. 目标路径已存在就当作重复件，不移动。
4. 命名规则：`年份_第一作者_短标题.pdf`；中文学位论文在标题后加「（硕士）」或「（博士）」。

## 6. 生成下载情况总结

```bash
python scripts/make_summary.py manifest.csv --dest "已下载论文"
```

脚本会生成 `已下载论文/下载情况.md`，内容包括：总览（篇数和大小）、目录结构、按期刊分组的文献表（附获取途径）、获取途径统计、还没下载的文献及补救办法。之后手动补两段：
- **引用提醒**：仓储来的版本可能是作者接受稿，引用时按 DOI 的正式出处标注，不要用 PDF 上的页码。
- **遗留文件**：下载目录里的误下文件、重复件分别怎么处理的。

## 7. 收尾时向用户汇报

- 用过哪些渠道、各拿到多少篇，还缺哪些、为什么缺、怎么补。
- 对照课件的要求检查：总数是否够 50 篇、英文是否至少三分之一、有没有近期文献、有没有 1–3 篇直接对标的文献。
- 提醒用户把为批量下载改过的浏览器设置改回去。
