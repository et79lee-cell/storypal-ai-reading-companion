# WebSocket protocol

Web 与微信小程序使用同一协议：`/ws` 与 `/ws/miniapp`。协议显式区分 `ai_proactive_question` 和 `user_interrupt_question`。

## Client → Server

| type | 关键字段 | 合法状态 | 说明 |
| --- | --- | --- | --- |
| `start_story` | `story_id` | 未创建 session | 创建新会话与 session memory |
| `sentence_complete` | — | `playing` | 客户端已播放完当前故事句 |
| `interrupt_intent` | — | `playing + story node` | 用户在当前句主动打断 |
| `user_message` | `text` | `awaiting_input` | ASR 结果或公开 Demo 的文字输入 |
| `skip_proactive_question` | — | `awaiting_input + proactive question` | 略过本次 AI 主动问题 |
| `answer_complete` | — | `answering` | 客户端已播放完 AI 回答 |

## Server → Client

| type | 关键字段 | 说明 |
| --- | --- | --- |
| `session_started` | `session_id` | 返回会话 ID |
| `story_sentence` | `node_id`、`sentence_index`、`progress` | 当前故事句与权威游标 |
| `proactive_question` | `question_design`、`dimension_labels` | Question Planner 选中的教育问题 |
| `proactive_question_skipped` | — | 确认略过主动问题 |
| `story_paused` | `interaction_module=user_interrupt_question` | 确认已保留打断位置 |
| `assistant_answer` | `interaction_module`、`dimension_labels` | Provider 回答及本轮维度 |
| `story_resumed` | — | 即将回到被打断的原句 |
| `story_end` | `session_id`、`progress` | 故事完成，可读取报告 |
| `error` | `message` | 不支持的消息或非法状态转换 |

## 主动问题示例

```json
{
  "type": "proactive_question",
  "interaction_module": "ai_proactive_question",
  "node_id": "first-thought",
  "text": "如果你是米粒，你会先问小星星什么？",
  "dimension_labels": ["想象力", "语言表达"],
  "skip_allowed": true,
  "question_design": {
    "question_type": "perspective_taking",
    "learning_goal": "从角色视角生成问题，并用完整语言表达。",
    "trigger_reason": "发现迷路的小星星后的剧情自然停顿。",
    "selection_reason": "优先覆盖本次会话尚未出现的想象力维度"
  }
}
```

## 打断恢复示例

```text
story_sentence(node=forest-night, sentence=0)
→ interrupt_intent
→ story_paused(module=user_interrupt_question)
→ user_message
→ assistant_answer(module=user_interrupt_question)
→ answer_complete
→ story_resumed
→ story_sentence(node=forest-night, sentence=0)
```

## REST report 与删除

- `GET /api/reports/{session_id}`：读取双模块次数、教育维度覆盖与互动记忆时间线；
- `DELETE /api/sessions/{session_id}`：立即删除公开 Demo 的 session 与 memory。
