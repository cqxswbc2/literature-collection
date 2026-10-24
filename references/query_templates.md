# 检索式与 URL 模板

## 一、构造检索式的套路

```
(概念A 的同义词们) AND (概念B 的同义词们) AND (约束C，比如数据类型)
```

以"居民需求响应 + 问卷数据"为例：

| 概念 | 英文 | 中文 |
|---|---|---|
| A 主题 | "demand response" OR "demand-side management" OR "demand flexibility" OR "load shifting" | '需求响应' + '需求侧管理' + '负荷调节' |
| B 对象 | residential OR household* OR consumer* | '居民' + '家庭' |
| C 数据/方法 | survey OR questionnaire OR "choice experiment" OR "stated preference" OR "willingness to pay" OR "willingness to accept" | '问卷' + '意愿' + '选择实验' + '支付意愿' |
| D 领域限定（消歧义） | — | '用电' + '电价' + '电力' |

**迭代原则**：先宽后窄。噪声大就看结果里混进了什么，再针对性地加限定词或删掉宽泛词。实际例子（CNKI）：

| 轮次 | 改动 | 命中 | 问题 |
|---|---|---|---|
| 1 | A × B（含'用户'）× C（含'调查'） | 335 | '调查'和'用户'把公共服务类硕士论文全拉进来了 |
| 2 | 去掉'调查'、'用户' | 98 | 混进了"需求响应式公交"（交通运输领域的同名概念） |
| 3 | 再加 D（用电/电价/电力） | 44 | ✅ 全部对题 |

## 二、Web of Science / Scopus

```
TS=(("demand response" OR "demand-side management" OR "demand flexibility" OR "load shifting")
    AND (residential OR household* OR consumer*)
    AND (survey OR questionnaire OR "choice experiment" OR "stated preference"
         OR "willingness to pay" OR "willingness to accept"))
AND PY=2016-2026
AND SO=("ENERGY ECONOMICS" OR "ENERGY POLICY" OR "APPLIED ENERGY"
        OR "ENERGY RESEARCH & SOCIAL SCIENCE" OR "NATURE ENERGY" OR "THE ENERGY JOURNAL")
```
- 结果按"被引频次"排序，先看近 5 年。
- 对 3 篇左右的核心综述点"施引文献"，往后追新文献。

## 三、ScienceDirect（不用登录就能检索）

```
https://www.sciencedirect.com/search?qs=<URL编码的布尔式>&pub=<期刊名URL编码>&date=2016-2026&show=50
```
- 示例：`qs=%22demand%20response%22%20AND%20%28residential%20OR%20household%29&pub=Energy%20Policy`
- 结果是 JS 渲染的，打开后要等 3–5 秒再读页面文字。
- 一页最多 50 条；结果卡片上会标 "Open access" / "View PDF"。

## 四、OpenAlex API（免费，加上 mailto 参数更稳定）

```
# 关键词检索
https://api.openalex.org/works?search=<关键词>&filter=publication_year:>2013,type:article&per_page=40&mailto=<邮箱>
# 按 DOI 取单篇
https://api.openalex.org/works/https://doi.org/<DOI>?mailto=<邮箱>
```
- 有用字段：`doi`、`publication_year`、`primary_location.source.display_name`（期刊名）、`cited_by_count`、`open_access.is_oa`、`best_oa_location.pdf_url`、`locations[]`。
- **坑**：
  - `search=` 的值里有 `?` `:` `—` 这类符号会报 400，先把标点替换成空格。
  - 期刊过滤的 source ID 别靠猜，猜错会返回一堆无关结果。
  - 加 `cited_by_count:>30` 再按被引排序，会把关键词相关性冲掉，变成"全领域高被引"。
  - 同一篇论文可能有 NBER、RePEc、ICPSR 等多个条目，要过滤掉，挑正式期刊那条。

## 五、Unpaywall

```
https://api.unpaywall.org/v2/<DOI>?email=<邮箱>
```
- 看 `oa_locations[]`：`host_type`（publisher 或 repository）、`version`（publishedVersion / acceptedVersion / submittedVersion）、`url_for_pdf`、`url`。
- `submittedVersion` 是投稿稿，可能和正式版差别较大，尽量用 accepted 或 published 版本。

## 六、CNKI

**高级检索框**（主题 SU）：
```
('需求响应'+'需求侧管理')*('居民'+'家庭')*('用电'+'电价'+'电力')*('问卷'+'意愿'+'选择实验')
```
- 运算符：`*` 是与，`+` 是或，`-` 是非，用英文半角括号控制优先级；检索词含空格或特殊符号时要加引号；**整个式子不能超过 120 个字符**。

**直达结果页的 URL**（不用在页面上填表单）：
```
# 主题检索
https://kns.cnki.net/kns8s/defaultresult/index?korder=SU&kw=<URL编码的检索式>
# 篇名检索（下载时定位单篇用）
https://kns.cnki.net/kns8s/defaultresult/index?korder=TI&kw=<URL编码的篇名或篇名片段>
```

**操作要点**：
- 左侧的"来源类别"（北大核心、CSSCI、CSCD）、"学科"分组可以点选过滤。**用 JS 的 click() 点不生效，要用真实鼠标点击**（先取坐标再点）。
- 从结果表格里取数据：`table tr` 的各个 `td` 依次是 序号 | 题名 | 作者 | 来源 | 时间 | 库 | 被引 | 下载。
- 篇名检索太长可能搜不到，或者因为请求太频繁返回空结果。换短一点的独特片段（比如"MRDE模型初探"），等几秒再试。

## 七、把检索过程记进清单

每次检索都记一行：检索式 | 数据库 | 命中数 | 处理（保留 / 收紧 / 放弃）。
最后在清单里写一段"结构性发现"，例如某主题在中文 CSSCI 期刊里只有十几篇、几乎都集中在工程类期刊。这一段可以直接用作研究空白的论据（课件第 40 页的思路）。
