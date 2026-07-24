# Security and child-data boundaries

## 公开版默认值

- Backend 默认监听 `127.0.0.1`，不对局域网或公网开放；
- 无 API Key，无真实 AppID，无供应商配置；
- 不接收和保存录音，文字输入只在当前 Python 进程内保存；
- Memory、会话和报告只存在于当前进程，服务重启后清空；
- `DELETE /api/sessions/{session_id}` 可立即删除本次会话；
- 记忆只保存互动事实，不创建儿童能力或心理标签；
- 不包含第三方故事、图片、音频、模型或训练数据。

## Credential controls

- `.env*`、本地配置、密钥文件、真实 AppID 和 private config 默认忽略；
- `.env.example` 只允许占位符；
- 发布前运行 `python scripts/check_secrets.py`；
- 扫描结果只输出文件、行号和风险类型，不打印疑似密钥值；
- 即使密钥已经从当前文件删除，也需要检查 Git 历史并在必要时轮换密钥。

## 不应直接用于生产环境

当前版本没有账户认证、访问控制、限流、传输层配置、监护人同意流程、跨会话记忆治理或完整内容审核。请勿将它直接暴露到公网，也不要处理真实儿童数据。

## 报告问题

请不要在公开 Issue 中粘贴密钥或儿童数据。安全问题可通过仓库维护者的 GitHub 主页私下联系。
