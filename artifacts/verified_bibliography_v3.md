# Verified Bibliography v3 — Umwelt Paper
**Vérification date**: 2026-11-24 (arXiv API live + DOI content-negotiation live)
**Méthode**: chaque ID interrogé sur `export.arxiv.org/api/query`; chaque DOI résolu via `doi.org` avec content negotiation. Toute entrée ci-dessous a un titre réel confirmé contre la source.

## Historique des corrections (v2 → v3)

| Slot v2 | Claim v2 | Statut vérification v2 | Correction v3 |
|---|---|---|---|
| [2] van Dijk & Kiverstein, M&M, DOI 10.1007/s11023-023-09612-3 | Umwelt in AI | **DOI 404 = halluciné** | DROPPÉE (claim recadré: Umwelt = emprunt thématique, citation de von Uexküll seul) |
| [3] Gershenson & Rosenblueth, Artificial Life DOI 10.1162/artl_a_00412 | Umwelt multi-agent | **DOI 404 = halluciné** | DROPPÉE |
| [5] Chen et al., Science Robotics eade9520 | robot proprioception | **DOI 404 = halluciné** | Remplacée par Wolpert & Kawato 1998 (DOI vérifié) |
| [6] Hohwy, Phil Tech DOI 10.1007/s13347-024-00678-9 | forward models as proprioception | **DOI 404 = halluciné** | Remplacée par Wolpert & Kawato 1998 |
| [8] Hsieh — arXiv:2402.14811 («Found in the Middle») | position bias calibration | ID existe, **MÊME AUTEUR MAIS PAPIER DIFFÉRENT** (titre réel: «Fine-Tuning Enhances Existing Mechanisms») | Corrigée: **arXiv:2406.16008**, titre exact «Found in the Middle: Calibrating Positional Attention Bias Improves Long Context Utilization» |
| [9] Wu et al. — arXiv:2502.01234 | emergence of position bias | **ID halluciné** (résolu = papier RL MDP) | Corrigée: **arXiv:2502.01951** (Xinyi Wu, titre exact) |
| [10] Du et al. — arXiv:2503.01234 | context length hurts | **ID halluciné** (résolu = papier astrophysique) | Corrigée: **arXiv:2510.05381** (Yufeng Du, «Context Length Alone Hurts LLM Performance Despite Perfect Retrieval») |
| [11] Chen et al. — arXiv:2501.05678 | attention scaling laws | **ID halluciné** (résolu = papier physique); papier non retrouvé | DROPPÉE (claim fusionné dans [12] Barbero + RULER) |
| [12] Barbero et al. — arXiv:2502.09876 | attend to first token | **ID probablement halluciné (motif séquentiel)** | Corrigée: **arXiv:2504.02732** (Federico Barbero, «Why do LLMs attend to the first token?») |
| [13] Wang et al. Y. — arXiv:2406.01234 | position bias mechanistic | **ID halluciné** (résolu = papier MDP) | Corrigée: **arXiv:2407.01100** (Ziqi Wang, «Eliminating Position Bias of Language Models: A Mechanistic Approach») |
| [15] Berglund et al. — arXiv:2405.11234 | situational awareness | **ID halluciné** (résolu = papier astron.) | Corrigée: **arXiv:2309.00667** (Lukas Berglund, «Taken out of context: On measuring situational awareness in LLMs», **2023 pas 2024**) |
| [16] Heo et al. — arXiv:2406.01234 (doublon de [13]) | instruction-following awareness | **doublon + halluciné** | Corrigée: **arXiv:2410.14516** (Juyeon Heo, «Do LLMs „know" internally when they follow instructions?») |
| [17] Laban et al. — arXiv:2501.05678 (doublon de [11]) | multi-turn lost | **doublon + halluciné** | Corrigée: **arXiv:2505.06120** (Philippe Laban, «LLMs Get Lost In Multi-Turn Conversation») |
| [18] Anagnostidis — arXiv:2402.01234 | prompt susceptibility | **ID halluciné** (motif 01234, NON-flaggé par le relecteur) | Corrigée: **arXiv:2408.11865** (Sotiris Anagnostidis, titre exact) |
| [20] Hui et al. — arXiv:2402.01234 | PLeak | **ID halluciné** (résolu = bio-stats) | Corrigée: **arXiv:2405.06823** (Bo Hui, «PLeakPrompt Leaking Attacks against Large Language Model Applications») |
| [21] Carlini — arXiv:2401.01234 | training data extraction | **ID halluciné** (résolu = biostat) | Corrigée: **arXiv:2012.07805** (Nicholas Carlini, «Extracting Training Data from Large Language Models», USENIX Security) |
| [22] Perez et al. — arXiv:2401.01234 (doublon [21]) | red teaming | **doublon + halluciné** | Corrigée: **arXiv:2202.03286** (Ethan Perez, «Red Teaming Language Models with Language Models») |
| [26] Nasr & Carlini — arXiv:2510.09023 | attacker moves second | **NOTRE ID ÉTAIT BON** (l'«ID vrai» proposé par le relecteur 2410.05295 résout = AutoDAN-Turbo, faux) | Inchangée, CONFIRMÉE |
| [27] SecOPD — arXiv:2608.21500 | adaptive injection defense | **NOTRE ID ÉTAIT BON** (vérifié = Yibo Peng, titre exact) | Inchangée, CONFIRMÉE |
| [33] Hou MCP security — arXiv:2503.01234 | MCP security analysis | **ID halluciné** (doublon avec [10] v2, motif 01234, NON-flaggé) | Corrigée: **arXiv:2503.23278** (Xinyi Hou, «Model Context Protocol (MCP): Landscape, Security Threats, and Future Research Directions») |
| — Bongard Science (proposé en remplacement [5]) | self-modeling robots | **le DOI testé résolvait vers un autre papier (Kussell 2005)** | DROPPÉ (Wolpert + Chatila suffisent) |

## Réfs vérifiées OK dans v2 (aucun changement)

| Ref | ID | Vérifié |
|---|---|---|
| [7] Liu et al. Lost in the Middle | arXiv:2307.03172 | API arXiv: OK, titre exact |
| [14] NVIDIA RULER | arXiv:2404.06654 | OK (titre complet réel: «RULER: What's the Real Context Size of Your Long-Context Language Models?») |
| [19] Burns et al. weak-to-strong | arXiv:2312.09390 | OK |
| [23] Liu et al. prompt injection benchmark | arXiv:2310.12815 | OK |
| [24] Greshake et al. indirect injection | arXiv:2302.12173 | OK (titre complet: «Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection») |
| [26] Nasr & Carlini | arXiv:2510.09023 | OK (Milad Nasr — confirmé, contrairement au relecteur) |
| [27] Peng SecOPD | arXiv:2608.21500 | OK |
| [28] Yao ReAct | arXiv:2210.03629 | OK |
| [29] Shinn Reflexion | arXiv:2303.11366 | OK |
| [30] Wang Voyager | arXiv:2305.16291 | OK |
| [31] Liu AgentBench | arXiv:2308.03688 | OK |
| [4] Chatila et al. Toward Self-Aware Robots | DOI 10.3389/frobt.2018.00088 | OK (Frontiers in Robotics and AI, 2018) |
| Wolpert & Kawato forward models (nouveau) | DOI 10.1016/S0893-6080(98)00066-5 | OK (Neural Networks, 1998) |

## Références non-arXiv

- OWASP (2025). LLM01:2025 Prompt Injection; LLM07:2025 System Prompt Leakage. https://genai.owasp.org (réintégrée — étaient dans v1, dropées par accident en v2)
- Schulhoff et al., «The Sandwich Defense», LearnPrompting.org (source web, pas arXiv)
- Model Context Protocol specification https://modelcontextprotocol.io
- Hermes Agent source, commits: `0461da8e6f3` (2026-09-07, «fix(gateway): retain original source fields in busy injections»), `fd2125de40` (2026-11-11, «fix(gateway): a mid-turn message in a shared chat names its sender»), `f4bc5ab478` (2026-11-23, «fix(steer): per-part steer origins + mechanical sentinel containment»)
- DeepSeek-Harness (Cordis) source, commit `99f6f02fecdb7dff40c3fbc9470f5907c29f74ca` (merge PR #2620, release/dsh-0.1.0-rc.7, 2026-08-17)

## Leçon (documentée pour l'atelier)

Motif d'hallucination pattern confirmé: IDs arXiv en séquences (01234, 05678, 09876), doublons exacts entre slots différents, DOIs Springer/Elsevier plausibles mais 404. La vérification arXiv-API+DOI-content-negotiation cost ~10 min pour 35 refs et élimine la classe de défaut au complet. La règle reste: JAMAIS insérer un ID/DOI non résolu live avant soumission.
