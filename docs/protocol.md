# WebSocket protocol

Web 与微信小程序使用同一协议：`/ws` 与 `/ws/miniapp`。

## Client → Server

| type | 关键字段 | 说明 |
| --- | --- | --- |
| `start_story` | `story_id` | 创建新会话 |
| `sentence_complete` | — | 客户端已播放完当前句 |
| `interrupt_intent` | — | 用户在当前句主动打断 |
| `user_message` | `text` | ASR 结果或公开 Demo 的文字输入 |
| `answer_complete` | — | 客户端已播放完 AI 回答 |

## Server → Client

| type | 说明 |
| --- | --- |
| `session_started` | 返回会话 ID |
| `story_sentence` | 当前句、游标和进度 |
| `story_paused` | 确认已保留打断位置 |
| `interaction_prompt` | 故事预设的引导问题 |
| `assistant_answer` | provider 返回的语境回答 |
| `story_resumed` | 即将回到被打断的原句 |
| `story_end` | 故事完成，可读取报告 |
| `error` | 不支持的消息或非法状态转换 |

## 示例

```json
{"type":"start_story","story_id":"lost-starlight"}
```

```json
{"type":"story_sentence","node_id":"forest-night","sentence_index":0,"text":"夜里，森林像一张深蓝色的毯子……","progress":0}
```
