#!/data/data/com.termux/files/usr/bin/bash
set -e
EVAL=$(find official_quranqa -type f -name "QQA23_TaskA_eval.py" | head -1)
if [ -z "$EVAL" ]; then
  echo "FAIL: official scorer not found - official repo contains datasets, format checkers and scorers"
  exit 1
fi
echo "Using official scorer: $EVAL"
QRELS=$(find official_quranqa -name "QQA23_TaskA_qrels_dev.gold" | head -1)
RUN="APEX44/09-experiments/quranqa_task_a/run.trec"
python "$EVAL" "$QRELS" "$RUN"
