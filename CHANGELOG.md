# Changelog

## [0.2.16] - 2026-08-17

### Changed
- 默认可执行文件输出名称改为入口文件名（如 `aether.py` → `aether.exe`），无需手动指定 `-n` 参数

## [0.2.15] - 2026-08-16

### Changed
- 自动依赖检测改为精确导入模式：`.pyi` 解析时保留完整子模块路径（如 `sqlalchemy.orm` 而非 `sqlalchemy`）
- 所有检测到的模块作为 `--hidden-import` 添加，不再使用 `--collect-submodules` 全量导入
- 移除 `COLLECT_PACKAGES` 硬编码列表，避免暴力引入整个包

## [0.2.14] - 2026-08-16

### Fixed
- 内部子模块（如 `conf.i18n`、`core.executor`）现在被正确添加为 `--hidden-import`，修复了 PyInstaller 打包后运行时 `ModuleNotFoundError` 的问题
- `shutil.rmtree` 的 `onexc` 参数改为 `onerror`，兼容 Python 3.8+
- `verified_hidden` 验证步骤不再过滤内部子模块，即使 `find_spec()` 在当前环境找不到也保留

## [0.2.13] - 2026-08-16

### Fixed
- 标准库子模块过滤修复：使用 `top_module in stdlib_modules` 替代 `module_name in stdlib_modules`，正确检测 `xml.dom`、`collections.abc` 等标准库子模块

### Changed
- 移除 PyInstaller 命令中冗余的 `--add-binary`（`.pyd`/`.so` 文件）和 `--add-data`（`__init__.py` 文件）标志，PyInstaller 的 modulegraph 分析可自动发现这些文件
- 避免 Windows 8191 字符命令行长度限制

## [0.2.12] - 2026-08-16

### Fixed
- 标准库子模块（如 `xml.dom`）现在作为 hidden-import 保留，而非被过滤掉

## [0.2.11] - 2026-08-16

### Fixed
- Linux/macOS 上收集 `.so` 文件（跨平台 `.pyd`/`.so` 支持）
- 日志信息从 `Found N .pyd files` 更新为 `Found N .pyd/.so files`

## [0.2.10] - 2026-08-16

### Fixed
- `--add-data`/`--add-binary` 分隔符跨平台兼容：Windows 使用 `;`，Linux/macOS 使用 `:`（`os.pathsep`）

## [0.2.9] - 2026-08-16

### Changed
- 将 PyInstaller 添加到 Poetry 依赖中

## [0.2.8] - 2026-08-16

### Fixed
- Test PyPI 安装命令修复：使用 `--extra-index-url` 替代 `--index-url`，确保能同时从 Test PyPI 和官方 PyPI 解析依赖

## [0.2.7] - 2026-08-16

### Changed
- 添加 PyInstaller 依赖

## [0.2.6] - 2026-08-16

### Changed
- 重构为包布局（`pysack/` 目录）
- 添加彩色输出支持
- 使用 `sys.executable -m PyInstaller` 确保 Nuitka 和 PyInstaller 使用相同 Python 解释器

## [0.2.5] - 2026-08-16

### Added
- 自动依赖检测：解析 Nuitka 生成的 `.pyi` 文件，提取第三方依赖
- 传递依赖映射：`httpx→httpcore`、`sqlalchemy→aiosqlite`、`sentence_transformers→transformers,torch,tokenizers` 等
- 添加 `--hidden-imports` 和 `--collect-submodules` 命令行参数

## [0.2.0] - 2026-08-16

### Added
- 初始发布到 Test PyPI
- 支持 `pysack full` 一键加密 + 打包工作流
- 支持 `pysack encrypt` 和 `pysack pack` 分步操作
- 自动过滤标准库模块和项目内部模块
- 支持 `.pysack.cfg` 配置文件