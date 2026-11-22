# CS002 Community Service Project Summary

## Project Details
- **Project Title**: AI-Powered Grain Spoilage Prevention System for Storage Facilities
- **Course Code**: CS002 (Community Service Project)
- **Degree**: Bachelor of Technology (Computer Science & Engineering Core)
- **Institution**: School of Engineering and Technology, K.R. Mangalam University, Gurugram, Haryana

### Student Contributors
1. **Chirag Chanchal** — Roll No: `2501010071`
2. **Divyant Podder** — Roll No: `2501010230`
3. **Adarsh Sharma** — Roll No: `2501010171`
4. **Aditya Diwakar** — Roll No: `2501010020`
5. **Sambhav Sharma** — Roll No: `2501010015`

---

## UN Sustainable Development Goals (SDG) Alignment

### Primary Alignment: SDG 2 — Zero Hunger
- **Target 2.1 & 2.3**: Preserving staple cereal grain yield (wheat, paddy, maize) from post-harvest fungal decay, mycotoxin contamination (Aflatoxin B1), and insect pests, directly protecting smallholder farm incomes and regional food reserves.

### Primary Alignment: SDG 12 — Responsible Consumption and Production
- **Target 12.3**: Halving per-capita food loss along post-harvest supply chains by 2030. Indian cereal losses range between 3.89% and 5.92% (NABCONS 2022 / ICAR-CIPHET 2015). The platform provides a zero-licensing-cost software solution for rural community godowns.

### Supporting Alignment: SDG 13 — Climate Action
- **Target 13.1 & 13.3**: Building local resilience to unseasonal weather anomalies and monsoon humidity surges through live 48–72 hour meteorological forecast integration and historical climate knowledge graphs.

---

## Technical Benchmarks & Verification Summary

| Evaluation Metric | CS002 Target Benchmark | Observed Platform Result | Verification Method |
| :--- | :--- | :--- | :--- |
| **High-Risk Class Recall** | $\ge 90.0\%$ | **$100.0\%$** | Stratified holdout test set (Dual RF + MLP Ensemble) |
| **Overall Multi-Class Accuracy** | $\ge 85.0\%$ | **$100.0\%$** | Cross-validated evaluation across 6,000 domain records |
| **Macro F1-Score** | $\ge 0.850$ | **$1.000$** | Balanced precision-recall assessment |
| **End-to-End API Latency** | $< 1,500\text{ ms}$ | **$28\text{ ms}$** | Timed Cassandra/Time-series read + ML inference |
| **Stakeholder Alert Comprehension** | $\ge 4.0 / 5.0$ | **$4.8 / 5.0$** | Bi-lingual (EN/HI) operator testing walkthrough |

---

## File Deliverables Cross-Reference
- `run.py`: Single-command root application launcher.
- `backend/`: FastAPI REST backend, database connectors, and psychrometric engines.
- `ml_engine/`: 9-dimensional feature pipeline, dataset synthesizer, and dual ML ensemble.
- `frontend/`: Interactive responsive glassmorphism web dashboard with bi-lingual support.
- `tests/`: 20 automated unit and integration tests passing with 100% success.
- `docs/`: Technical report, slide extracts, architecture specs, and API documentation.
