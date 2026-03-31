# 数据库备份目录

此目录用于存储数据库的备份文件，以便在数据库损坏时恢复。

## 备份文件命名规则

- 格式：`database_YYYYMMDD_HHMMSS.db`
- 示例：`database_20260315_123949.db`

## 如何恢复数据库

如果数据库损坏，可以使用以下命令恢复：

```bash
# 停止应用
# 复制备份文件到数据目录
cp backups/database_YYYYMMDD_HHMMSS.db data/database.db

# 重启应用
```

## 注意事项

1. 定期备份：建议每天备份一次
2. 备份文件较大，不要频繁提交到git
3. 恢复前请先停止应用，避免数据冲突
