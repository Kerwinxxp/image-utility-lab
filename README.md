# 图片效用实验 · Utility vs. ε

**任务：在 200 张图片上测量加噪造成的图像变化，绘制 utility–ε 曲线，并把原始测量结果交给导师。**

代码和输入数据均可直接下载。普通电脑的 CPU 即可运行，不需要 GPU、模型或 API 密钥。

```text
下载原图与加噪图  →  测量 MSE / SSIM  →  绘制曲线  →  提交原始结果
```

## 这次具体测什么？

| 项目 | 固定设置 |
|---|---|
| 数据 | im2gps 数据集的 200 张图片 |
| 加噪范围 | 每张图中全部已选线索区域的并集，用 mask 标记 |
| 方法 | Laplace、有限 RGB 指数机制 |
| 噪声参数 | ε = 2、4、6、8、10；数值越大，噪声越弱 |
| 随机重复 | 只用已保存的默认 draw 0 |
| 比较方式 | 每张加噪图与它对应的原图比较 |
| 指标 | MSE：越低越好；SSIM：越高越好。整张图和 mask 区域分别测量 |

输入已经生成好了，直接测量即可。最终有 **2,200 行原始结果**：200 行原图自检，加上两种方法各 1,000 行加噪结果。

## 第 1 步：下载

1. 下载并解压 [代码 ZIP](https://github.com/Kerwinxxp/image-utility-lab/archive/refs/heads/main.zip)，或使用 `git clone https://github.com/Kerwinxxp/image-utility-lab.git`。
2. 打开 [数据下载页](https://github.com/Kerwinxxp/image-utility-lab/releases/tag/data-v1.0)，下载下面四个文件。

| 文件 | 内容 |
|---|---|
| `im2gps200_base.zip` | 200 张原图 + 200 张 mask |
| `im2gps200_laplace_draw0_part1.zip` | 500 张 Laplace 加噪图 |
| `im2gps200_laplace_draw0_part2.zip` | 其余 500 张 Laplace 加噪图 |
| `im2gps200_exponential_draw0.zip` | 1,000 张指数机制加噪图 |

3. 将四个 ZIP **都解压到代码目录**，合并它们的 `data/` 文件夹。

四个 ZIP 总计约 2.9 GB。两个 Laplace ZIP 都能独立解压。解压完成后，`data/` 应与 `run.py` 在同一层，例如 `data/statue/`。

## 第 2 步：安装

安装 **Python 3.11、3.12 或 3.13**。在代码目录打开终端，执行对应命令：

**Windows PowerShell**

```powershell
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

如果安装的是 Python 3.11 或 3.12，将第一行的 `-3.13` 改为对应版本。

<details>
<summary>macOS / Linux 安装命令</summary>

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

下文命令中的 `.venv\Scripts\python.exe` 替换为 `.venv/bin/python`。

</details>

## 第 3 步：运行

```powershell
.venv\Scripts\python.exe run.py
```

这一条命令会依次完成 **200 张图片的测量、绘图和结果打包**。程序会显示当前步骤，并检查输入文件、图片尺寸和 mask 外像素是否一致。

希望先确认环境是否正确，可以先试 3 张：

```powershell
.venv\Scripts\python.exe run.py --limit-images 3
```

试跑结果单独保存到 `results/check3/`。确认成功后，再运行不带 `--limit-images` 的完整命令。

## 第 4 步：提交

将 **`results/draw0_submission.zip`** 发给导师。这个 ZIP 包含：

| 交付文件 | 用途 |
|---|---|
| `per_image_results.csv` / `.jsonl` | 每张图、每种方法、每档 ε 的原始测量值 |
| `summary.csv` | 各设置的汇总值 |
| `figures/` | 四个指标的 utility–ε 曲线，PNG 和 PDF |
| `run_info.json` 与代码快照 | 记录实际运行环境、数据和代码版本 |

保留原始精度，提交完整 ZIP。导师会根据原始结果进行后续分析。本次任务到 utility 曲线和原始测量结果为止。

## 想看代码，从哪里开始？

```text
image-utility-lab/
├── README.md          ← 从这里开始
├── run.py             ← 唯一运行入口
├── requirements.txt   ← 安装依赖
├── src/               ← 测量、绘图、打包的实现
├── config/            ← 固定的图片清单与指标设置
├── docs/              ← 指标解释、任务清单和常见问题
├── tests/             ← 数值与流程检查
├── data/              ← 下载后解压到这里
└── results/           ← 运行后自动生成
```

推荐阅读顺序：`run.py` → [`src/utility_lib.py`](src/utility_lib.py) 中的 `measure_arrays` → [`src/plot_utility.py`](src/plot_utility.py)。先理解怎么算，再调整实现或图的样式。

[指标怎么算](docs/METRICS.md) · [分步运行与常见问题](docs/USAGE.md) · [提交检查清单](docs/TASKS.md) · [维护者验证记录](docs/VALIDATION.md)

原始图片的权利仍归原权利人；公开仓库不改变图片的许可条件。数据保留原始文件字节及既有元数据，详见 [`config/data_card.json`](config/data_card.json)。
