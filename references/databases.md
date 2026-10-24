# 数据库与渠道选择

依据课程《文献检索、文献阅读与文献综述》第 2 节（数据库），再结合实际使用效果排了优先级。

## 一、英文检索

| 优先级 | 渠道 | 适合干什么 | 注意 |
|---|---|---|---|
| ★★★ | **Web of Science 核心合集** | 全面检索、按被引排序、**施引文献追踪**（顺藤摸瓜的主要工具） | 要学校订阅，通常校园网或机构登录就能用 |
| ★★★ | **ScienceDirect**（Elsevier） | Energy Economics、Energy Policy、Applied Energy、ERSS、RSER 等能源类主力期刊；可以按期刊限定检索 | 检索页不用登录；下载 PDF 会被反爬拦，看 SKILL.md 第 4 节 |
| ★★ | **OpenAlex**（api.openalex.org） | 免费跨出版社书目库，补 Elsevier 以外的期刊；能查 DOI、年份、被引数和 OA 状态 | 期刊过滤要用 source ID，猜 ID 容易错。更稳的做法是关键词检索后按 `primary_location.source.display_name` 过滤 |
| ★★ | **Unpaywall**（api.unpaywall.org） | 按 DOI 查合法的开放副本（出版社 OA 或机构仓储） | 仓储页面可能挂错文件，下载后必须核对 |
| ★★ | Scopus | 和 WoS 类似，经济管理类期刊覆盖广 | 要订阅 |
| ★ | EconLit | 只收经济学文献，用来补能源经济视角 | 要订阅 |
| ★ | SSRN、NBER Working Papers | 还没正式发表的前沿研究、正式论文的工作论文版 | 引用时注意版本 |
| ★ | Wiley、Springer、Taylor & Francis、SAGE、OUP、Cambridge、AEA、JSTOR | 对应出版社的期刊；JSTOR 适合找早几年的经济学期刊 | AEA 官网要会员或机构订阅，订不到可以试 JSTOR |
| — | Semantic Scholar、Google Scholar | 快速摸底 | 国内网络常打不开或加载不出来，不要依赖 |

## 二、中文检索

| 优先级 | 渠道 | 适合干什么 | 注意 |
|---|---|---|---|
| ★★★ | **CNKI 中国知网** | 期刊 + 硕博论文；左侧有来源类别、学科分组 | 首次访问常弹滑块（交给用户）；下载必须从文章页点（校验来源页） |
| ★★ | 万方（含学位论文库 CDDB） | 补硕博论文，尤其是博士论文 | 和 CNKI 有重复 |
| ★ | 维普 | 补充 | 和 CNKI 重复度高，一般不必单独跑 |
| ★ | 国家图书馆 | 中文学位论文 | |

## 三、研究报告、政策、数据（写背景和做实证用）

| 类型 | 渠道 |
|---|---|
| 国际报告 | IEA、ACEEE、IPCC |
| 国内报告 | 行业协会、电网和能源研究院、研报客（yanbaoke.com） |
| 政策文件 | 相关部委官网 |
| 宏观数据 | 国家统计局（data.stats.gov.cn）、中经网（db.cei.cn）、国研网、Wind、国泰安 |
| 微观问卷数据 | 例如：CHFS 中国家庭金融调查（西南财经大学）、CRECS 中国居民能源消费调查、CFPS、CGSS。按课题选，申请流程以各数据库官网为准 |

## 四、学位论文

| 地区 | 渠道 |
|---|---|
| 中国 | CNKI 硕博库、万方 CDDB、国家图书馆 |
| 美国 | ProQuest Dissertations & Theses（PQDT） |
| 英国 | EThOS |
| 其他 | 各大学自建的学位论文库；英美可以搜"学校名 + dissertation/thesis" |

## 五、拿不到全文时

1. Unpaywall 查仓储副本（接受稿也能用，引用时按正式出处）。
2. 学校图书馆**文献传递 / 馆际互借**（CALIS、NSTL）：一般 1–2 个工作日，通常免费。
3. 给通讯作者发邮件索取。
4. 找同一研究的工作论文版（NBER、SSRN、作者主页）。

## 六、CARSI 机构登录与学校可用资源（以西南财经大学为例，2026-10-21 查询）

### 1. 怎么用

- **统一入口**：https://ds.carsi.edu.cn/login/index.html → 选自己的学校 → 学校统一身份认证（**账号密码由用户自己输**）。
- **查学校订了什么**：登录后进「应用资源」页（https://ds.carsi.edu.cn/resource/resource.php），勾选「只显示本校可用资源」，可以按名称搜索。标签含义：**校购**是长期可用；**免费**是公共资源；**试用**是临时开通，随时会变（西财当时有 151 条试用）。
- **登录后怎么进出版社**：在出版社文章页点 "Access through your institution"，搜学校名并选择，会经 CARSI 单点登录跳回，**不用再输密码**。如果文章页出现 "Brought to you by / Access provided by <学校>"，或者有了全文下载按钮，就说明生效了。
  - Springer Nature 的机构选择页（wayf.springernature.com）上，模拟键盘输入经常打不进搜索框。可以用脚本给 `#autocomplete-input` 赋值并触发 input 事件，再点下拉里的学校、提交。
- **注意**：CARSI 列表只包括支持 CARSI 单点登录的库，**不等于图书馆的全部订购**。有些库只认校园 IP（比如 CNKI 在校园网下直接可用）。不确定时再查图书馆主页的「数据库导航」。
- **校购也不等于全刊都订了**：ScienceDirect 是校购，但 Applied Energy 登录后仍然只给摘要，说明学校的订购包里不含这本刊。

### 2. 西财校购资源里对查论文有用的（34 条校购资源按用途整理）

| 用途 | 资源 | 说明 |
|---|---|---|
| **英文检索 / 引文分析** | **Web of Science**（核心合集） | 课件第一推荐；按被引排序、看施引文献，顺藤摸瓜的主要工具 |
| | 期刊引用报告（JCR）、基本科学指标（ESI）、InCites | 查期刊影响因子、分区、高被引 / 热点论文 |
| | EBSCO | 文摘 + 全文，含商业和经济类库 |
| | ProQuest 学术平台 | 综合库、过刊 |
| **英文全文（出版社平台）** | ScienceDirect（Elsevier） | Energy Economics、Energy Policy、ERSS、RSER 等；**部分刊未订，如 Applied Energy** |
| | Springer Link | Springer 和 Palgrave 的期刊；**不含 nature.com 上的 Nature 子刊** |
| | Wiley Online Library | |
| | Taylor & Francis | |
| | Oxford Journals（OUP） | 含 Review of Economic Studies、QJE 等经济学期刊 |
| | Emerald Insight | 管理类 |
| | University Press Scholarship Online | 学术专著 |
| | Cochrane Library | 系统评价（偏医学） |
| **学位论文** | 中科进出口 PQDT 学位论文全文检索平台 | 国外博硕士论文 |
| | 中国学位论文全文数据库（万方） | 搜"万方"能找到 |
| | 中国知网（CNKI） | 期刊 + 学位论文 + 报纸 |
| | 华艺学术文献数据库 | 台湾期刊和学位论文 |
| **中文期刊 / 检索** | 中国知网、维普中文期刊服务平台、人大复印报刊资料 | 人大复印报刊资料是社科精选转载，可用来判断"重要文献" |
| | 经纶知识服务平台（维普） | 期刊、会议、学位论文的统一检索 |
| | 超星发现、百链、读秀 | 跨库发现、文献传递、图书章节检索 |
| **报告 / 数据**（写背景、做实证） | 皮书数据库 | 各行业蓝皮书、研究报告 |
| | EPS 数据平台 | 宏观、行业统计数据 |
| | RESSET 金融研究数据库 | 金融数据 |
| | 全球案例发现系统 | 商业案例 |
| **法律** | 北大法宝、Thomson Reuters Westlaw | 政策法规原文 |

### 3. 这次实际查过、CARSI 里没有的（拿不到全文时直接走第五节的办法）

| 资源 | 结果 | 影响 |
|---|---|---|
| **Nature（nature.com）** | 无 | Nature Energy、Nature Climate Change 的订阅文章打不开；Nature Communications 本身是 OA，可以直接下 |
| JSTOR | 无 | AER 等经济学过刊只能找 NBER 工作论文版或文献传递 |
| AEA（aeaweb.org） | 无 | 同上 |
| Scopus | 无 | 用 Web of Science 代替 |
| IEEE Xplore | 无 | 电力工程方向的需求响应论文要注意，可能需要文献传递 |
| Cambridge、Annual Reviews | 无 | |
| SAGE | 仅试用 | 试用期内可用。SAGE 出版 Journal of Marketing、Journal of Marketing Research、ASQ，以及 2026 年起的 Production and Operations Management |
| INFORMS（pubsonline.informs.org） | 无 | Management Science、Marketing Science、M&SOM、ISR、Operations Research 都在这里，**西财没有订**。OA 查不到时只能找作者主页/SSRN 版本或走文献传递 |
| Academy of Management（AMJ、AMR） | CARSI 列表里没有 | 可以试 EBSCO 的商业库，没有再走文献传递 |

### 4. 商科/管理类期刊在哪个平台（按西财 2025 目录 A1 及以上整理）

| 平台 | 期刊 | 西财 |
|---|---|---|
| INFORMS | Management Science、Marketing Science、M&SOM、Operations Research、ISR | 未订 |
| SAGE | Journal of Marketing、JMR、ASQ、POM（2026 年起） | 试用 |
| Springer | Journal of the Academy of Marketing Science | 校购 |
| OUP | Journal of Consumer Research | 校购 |
| Wiley | Strategic Management Journal、Naval Research Logistics、Journal of Consumer Psychology、POM（2025 年及以前） | 校购 |
| Elsevier | European Journal of Operational Research、Journal of Business Venturing | 校购（具体刊以登录后能否下载为准） |
| AOM | AMJ、AMR | CARSI 未列，试 EBSCO |
| MISQ（AIS） | MIS Quarterly | CARSI 未列，试 EBSCO |

> 换学校或过了一段时间要重新查：资源会调整，试用尤其变化快。
