# 音频示例

`audio_demo.zan` 演示 `System.Audio` 的原生音频播放（zan_audio 运行时，
零外部依赖，Windows 上走 WASAPI）：

- `Audio.Open()` / `SetVolume()` / `Close()`：打开默认播放设备与主音量，
  `DriverName()` 看原生后端名（Windows 上是 `wasapi`）；
- `AudioClip.LoadWav(path)` / `LoadWavFromMem(data, len)`：把 WAV 解码进
  内存（支持 PCM 8/16/24/32 位与 32 位浮点、WAVE_FORMAT_EXTENSIBLE），
  `Frequency()` / `Channels()` / `DurationMs()` 读取格式；内存路径用于
  加密资源包（解密字节直接加载，全程不落盘）；
- `AudioClip.LoadOgg(path)` / `LoadOggFromMem(data, len)`：OGG Vorbis
  背景音乐；
- `clip.Play()`、`clip.Play(gain, loop)`、`clip.PlayLooping(gain)`：
  同一个 clip 可以叠加播放，每次返回一个 `AudioVoice`；
- `voice.IsPlaying()` / `Stop()` / `SetGain()`：单个声音的控制；
  播完的一次性声音自动回收（`Audio.ActiveVoices()` 顺带触发回收）。

例子不带音频素材：它先合成一段 440 Hz 正弦音（内存里构造 WAV 字节），
再从内存与文件两条路加载播放，所以顺带也是一份最小的 WAV 写出代码。

在仓库根目录编译运行：

```powershell
build\zanc.exe examples\audio\audio_demo.zan --auto-stdlib -o build\audio_demo.exe
build\audio_demo.exe
```

输出形如：

```text
driver: wasapi
clip: 44100 Hz, 1 ch, 700 ms (from file: ok)
played through
voices: 3
voices after stop: 0
```

混音由运行时的后台音频线程完成：采样线性重采样到设备混音格式后叠加，
循环 voice 到达采样末尾回卷，因此主线程阻塞时播放也不会断。同时播放的
声音上限是 64 个。voice 句柄带世代号：句柄存活比声音长也不会碰到被
回收的槽位，`IsPlaying()` 老实返回 false。

没有可用音频设备时 `Audio.Open()` 返回 false，原因见 `Audio.LastError()`；
其他平台的原生音频后端（CoreAudio/ALSA/AAudio/OH Audio）落地前，
`Open()` 会返回 false 并在 `LastError()` 说明。
