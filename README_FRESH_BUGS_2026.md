# LiveSWE-2026: 1,000 Fresh Uncontaminated Bug-Fix Tasks from Live GitHub (October 2026)

[![Kaggle Dataset](https://img.shields.io/badge/Kaggle-Dataset-20BEFF?logo=kaggle)](https://www.kaggle.com)
[![Freshness](https://img.shields.io/badge/Harvested-October_2026-green)](https://github.com)
[![Zero Contamination](https://img.shields.io/badge/Contamination-0%25-brightgreen)](https://github.com)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

---

## 📌 Context & Motivation: The AI Benchmark Contamination Crisis

Standard AI code evaluation benchmarks (such as **HumanEval**, **MBPP**, and original **SWE-bench**) were compiled between 2021 and 2023. As frontier models (such as GPT-4o, Claude 3.5, and Meta Llama 3) expand their pre-training corpora into the multi-trillion token scale, **nearly all historical benchmark code has already leaked into the training sets**.

Reported high resolution rates on older benchmarks reflect **pre-training memorization rather than true algorithmic reasoning**.

To solve this, **LiveSWE-2026** was crawled and harvested directly from live GitHub open-source repositories, strictly filtering for **real-world Python bug-fix Pull Requests merged in late October 2026** (up to October 29, 2026).

Because these bugs and human patches were written and merged within the past 1–9 days, they represent **100% uncontaminated ground truth** that no existing pre-trained foundation model has ever seen.

---

## 📊 Dataset Summary

* **Total Samples**: 1,000 merged bug-fix tasks.
* **Repositories**: 416 distinct open-source Python repositories.
* **Temporal Window**: Merged between **October 20, 2026 and October 29, 2026**.
* **Ground Truth**: Each entry contains the human-verified `diff_url` and `patch_url` representing the definitive code fix.

---

## 📁 Data Schema & Dictionary

| Column Name | Type | Description |
| :--- | :--- | :--- |
| `pr_id` | `int` | Unique GitHub Pull Request ID. |
| `repo_name` | `string` | Target open-source repository (e.g. `astronomer/astronomer-cosmos`). |
| `pr_number` | `int` | The specific PR issue number in the repository. |
| `title` | `string` | The bug fix title and summary. |
| `bug_description` | `string` | Problem statement and issue description written by the author. |
| `author` | `string` | Contributor or AI agent who proposed the fix. |
| `author_association` | `string` | Relationship (`CONTRIBUTOR`, `MEMBER`, `OWNER`). |
| `labels` | `string` | Associated tags (e.g., `bug`, `fix`, `python`). |
| `created_at` | `timestamp` | Creation timestamp (October 2026). |
| `closed_at` | `timestamp` | Merge/Close timestamp. |
| `html_url` | `string` | Direct link to the Pull Request on GitHub. |
| `diff_url` | `string` | Direct link to the raw code diff patch. |
| `patch_url` | `string` | Direct link to the git patch format. |
| `comments_count` | `int` | Number of review comments exchanged during merge. |
| `data_harvest_timestamp` | `string` | Timestamp when the crawler extracted the record (`2026-10-29`). |

---

## 🚀 Research & Meta Hackathon Applications

1. **Uncontaminated LLM Coding Evaluation**: Feed `bug_description` to Meta Llama-3-70B/405B and evaluate whether it can generate the correct patch matching `diff_url`.
2. **Benchmark Drift Monitoring**: Compare Llama's resolve rate on SWE-bench (2023) vs LiveSWE (October 2026) to prove the memorization drop mathematically.
3. **Automated Continuous Benchmarking**: Use Llama Stack to build continuous agent auditing pipelines for live GitHub repositories.

---

## 📄 BibTeX Citation

```bibtex
@dataset{liveswe_october_2026,
  title={LiveSWE-2026: 1,000 Fresh Uncontaminated Bug-Fix Tasks from Live GitHub},
  author={Dataset Kaggle Community},
  year={2026},
  month={October},
  publisher={Kaggle},
  howpublished={\url{https://www.kaggle.com}}
}
```

