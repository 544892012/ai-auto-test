---
id: form_httpbin_post
target: https://httpbin.org/forms/post
device: desktop
---

# httpbin 表单提交冒烟

## steps

1. 打开 target 表单页
2. 在 Customer name 或等价姓名输入框中输入 “AITest”
3. 在 Telephone 或等价电话输入框中输入 “13800138000”
4. 点击 Submit 提交按钮（或等价 submit）

## asserts

- 提交后 URL 或页面内容体现已进入处理结果页（例如包含 “httpbin” 与表单字段回显，或状态为 200 的响应页）
