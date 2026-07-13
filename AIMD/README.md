# AIMD — 从头算分子动力学后处理

独立于 VASP opt/ELF 脚本包。当前聚焦 **MSD / RMSD**。

## 先读这个

**[`../AIMD_QUICKSTART.md`](../AIMD_QUICKSTART.md)**：MVP → 高通量 → 分脚本（主目录范式上手样例）。

## 强制流程

新功能开发遵守仓库根 [`README.md`](../README.md) 四步；规格见 [`AIMD_DEPLOY_SPEC.md`](AIMD_DEPLOY_SPEC.md)。

## 快速部署

```bash
cd AIMD
cp deploy.env.example deploy.env
source deploy.env
echo "SCR=[$AIMD_SCRIPTS_ROOT] WR=[$AIMD_WORK_ROOT]"
pip install numpy matplotlib
```

其余命令见 Quickstart；详细路径与回答范式见 [`AIMD_WORKFLOW.md`](AIMD_WORKFLOW.md)。  
脚本说明：[scripts/MSD_RMSD/README.md](scripts/MSD_RMSD/README.md) · 样例：[example/](example/)
