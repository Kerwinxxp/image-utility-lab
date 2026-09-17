# 分步运行与常见问题

以下命令在代码根目录执行，使用 Windows 虚拟环境中的 Python。macOS / Linux 将 `.venv\Scripts\python.exe` 替换为 `.venv/bin/python`。

## 单独运行某一步

完整运行：

```powershell
.venv\Scripts\python.exe run.py
```

只测量：

```powershell
.venv\Scripts\python.exe run.py --step measure
```

修改绘图样式后，只重新画图：

```powershell
.venv\Scripts\python.exe run.py --step plot
```

最后重新打包：

```powershell
.venv\Scripts\python.exe run.py --step package
```

详细参数：`.venv\Scripts\python.exe run.py --help`。

## 常见问题

**找不到图片或 `data/` 目录。**

确认四个数据 ZIP 全部解压，并且 `data/statue/` 与 `run.py` 位于同一代码目录下。不要让路径多套一层 `image-utility-lab-main/`。

**内存占用较高。**

默认同时处理两张图片，可以改成一次一张：

```powershell
.venv\Scripts\python.exe run.py --workers 1
```

**运行中断了。**

重新执行相同命令。测量程序会复用已完成且通过数据、代码、设置校验的结果。完成前不要修改输入图片或指标定义。

**想先试 3 张。**

```powershell
.venv\Scripts\python.exe run.py --limit-images 3
```

试跑保存到 `results/check3/`。正式提交需再执行 `.venv\Scripts\python.exe run.py`，生成完整的 `results/draw0_submission.zip`。

**如何检查代码？**

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

**如何检查下载是否完整？**

数据 Release 中的 `SHA256SUMS.txt` 给出了四个 ZIP 的校验值。Windows 可以运行：

```powershell
Get-FileHash im2gps200_base.zip -Algorithm SHA256
```

与文本中的对应值比较。测量程序也会逐个核验图片与 mask 的哈希。

**图画出来了，只交截图可以吗？**

请提交完整的 `results/draw0_submission.zip`。导师需要原始 CSV/JSONL 数值进行后续分析，截图不包含完整信息。
