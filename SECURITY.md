# Security

不要把账号密码、API key、学校统一身份认证信息、浏览器 cookie、未公开的稿件或私人批注提交到这个仓库。

推送到远程仓库前，先检查：

```bash
find . -type f \( -iname ".env*" -o -iname "*secret*" -o -iname "*token*" -o -iname "*key*" \)
grep -rnI -E "(api[_-]?key|secret|password|BEGIN RSA|BEGIN OPENSSH|github_pat|ghp_|gho_)" .
```

匹配结果需要人工确认：文档里讨论 "token" 或 "password" 这些词不一定是泄露。

技能里的脚本只读写你指定的文件夹。运行前请先阅读 `SKILL.md` 和 `scripts/` 中会被调用的脚本，确认读取、修改和上传的文件范围；skill 文件本身不授予任何额外权限。
