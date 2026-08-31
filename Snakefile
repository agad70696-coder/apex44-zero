rule official_eval:
    input:
        qrels="official_quranqa/Task A/data/qrels/QQA23_TaskA_qrels_dev.gold",
        run="APEX44/09-experiments/quranqa_task_a/run.trec"
    output:
        "APEX44/04-evaluation/official/map_mrr.json"
    shell:
        'python "official_quranqa/Task A/eval/QQA23_TaskA_eval.py" "{input.qrels}" "{input.run}" > "{output}"'
