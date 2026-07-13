# AIMD/example — MVP 示例占位

将测试体系放到：

```
example/<A>/AIMD/XDATCAR
example/<A>/AIMD/INCAR     # 必须含 POTIM = <fs>
```

## 删减 XDATCAR（最快跑通）

1. **保留**前 7 行结构头（scale、晶格、元素、计数）及坐标块格式。  
2. 只留 **20–50 个** ionic 帧即可验证脚本链。  
3. 不要改元素顺序；`POTIM` 保持与完整计算一致，便于对照。

## 跑 MVP

```bash
source ../deploy.env   # 或临时:
export AIMD_SCRIPTS_ROOT="$(cd ../scripts && pwd)"
export AIMD_WORK_ROOT="$(pwd)/_mvp_work"
mkdir -p "$AIMD_WORK_ROOT/<A>/AIMD"
cp -r <A>/AIMD/* "$AIMD_WORK_ROOT/<A>/AIMD/"

$AIMD_PYTHON $AIMD_SCRIPTS_ROOT/MSD_RMSD/extract_msd_flex.py \
  "$AIMD_WORK_ROOT/<A>/AIMD/XDATCAR"
ls "$AIMD_WORK_ROOT/MSD_data_for_origin/"
```

把完整 `XDATCAR` 放到本目录后告知 Agent，可再帮你裁帧。
