# examples/sdk — 第三方 SDK 示例

本目录提供可独立编译的真实 SDK 调用示例。示例不会把密钥写进源码，运行时从命令行参数读取。

## 京东 JOS

`jd_open_api.zan` 演示：

- `JdClient` 配置 appKey、appSecret 和 OAuth access token；
- `JdAreaApi` 模块客户端与强类型 Request/Response；
- SDK 自动完成参数 JSON、时间戳、签名、HTTP 请求、响应信封解包和实体反序列化；
- `JdException` 错误处理。

```powershell
build/zanc.exe examples/sdk/jd_open_api.zan --auto-stdlib -o build/jd_open_api.exe
build/jd_open_api.exe <appKey> <appSecret> <accessToken|->
```

## 微信公众号

`wechat_mp.zan` 演示：

- `WechatClient` 自动获取和缓存 access token；
- `WechatMpUserApiInfoRequest` 强类型请求；
- `WechatMpUserApiInfoResponse` 及共享用户实体字段；
- `WechatException` 错误处理。

```powershell
build/zanc.exe examples/sdk/wechat_mp.zan --auto-stdlib -o build/wechat_mp.exe
build/wechat_mp.exe <appId> <appSecret> <openId>
```

## Steam Web API

`steam_webapi.zan` 演示：

- `SteamClient` 配置 Web API key 与 AppId；
- 六个封装接口：GetNumberOfCurrentPlayers、GetPlayerSummaries、
  AuthenticateUserTicket、GetSchemaForGame、SetUserStatsForGame、GetOwnedGames；
- `SteamPlayerSummary` / `SteamTicketResult` / `SteamAchievement` / `SteamOwnedGame`
  强类型结果与 `SteamResponse` 点分路径取值；
- `SteamException` 错误处理（HTTP 403 → `http.403`，票据拒绝 → `auth.<EResult>`）。

不带参数运行是**离线自测**：内置一个回放官方 JSON 形态的假 Steam 网关
（`HttpServer`），不需要 Steam 客户端和 key 就能闭环验证 SDK 全部接口与
错误路径（`PlainHttpMode()` + `ExternalCallPolicy.Default().AllowLocalHttp()`
是跑本地假网关的固定搭配）：

```powershell
build/zanc.exe examples/sdk/steam_webapi.zan --auto-stdlib -o build/steam_webapi.exe
build/steam_webapi.exe
```

带 `<webApiKey> <appId>` 参数时追加**真网 smoke**（正式网关
api.steampowered.com）：在线人数查询无需 key，玩家资料查询需要有效 key
（key 无效时验证 403 → `SteamException` 的映射）：

```powershell
build/steam_webapi.exe <webApiKey> <appId>
```

## 密钥

所有示例都不会把密钥写进源码，运行时从命令行参数读取。请使用有效的测试
应用凭据，不要把密钥提交到仓库。
