"""Registry of verified IAVE national exam URLs (2024-2025).

Deliberately outside pt_exams/PHEB's coverage (2006-2023, six subjects:
Mathematics, Portuguese, History, Geography, Biology/Geology, Philosophy) —
see PLANO-MELHORIA-AMALIA.md's decontamination note. Using post-2023 years
makes every entry here disjoint from those benchmarks by construction, for
all 24 subjects IAVE publishes (not just the six).

URLs were fetched and verified directly from
https://iave.pt/provas-e-exames/arquivo/arquivo-provas-e-exames-finais-nacionais-es/?ano=YYYY
on 2026-07-07. IAVE's upload filenames carry inconsistent manual suffixes
(_net, -V1, -VD, -2, occasional embedded dates) — not a predictable pattern,
so entries are hardcoded from confirmed links rather than URL-guessed. When
adding a new year, re-fetch that ?ano= page and extend EXAMS below; don't
guess filenames.

Each entry: (year, subject, code, phase, exam_pdf_url, marking_scheme_pdf_url)
phase is one of: "F1" (1a Fase), "F2" (2a Fase), "EE" (Epoca Especial)
"""

EXAMS = [
    # ---------------------------------------------------------------- 2025, 1a Fase
    (2025, "Portugues Lingua Segunda", 138, "F1", "https://iave.pt/wp-content/uploads/2025/06/EX-Port138-F1-2025_net-1.pdf", "https://iave.pt/wp-content/uploads/2025/06/EX-Port138-F1-2025-CC-VD_net.pdf"),
    (2025, "Alemao", 501, "F1", "https://iave.pt/wp-content/uploads/2025/06/EX-Alm501-F1-2025_net.pdf", "https://iave.pt/wp-content/uploads/2025/06/EX-Alm501-F1-2025-CC-VD_net_2.pdf"),
    (2025, "Frances", 517, "F1", "https://iave.pt/wp-content/uploads/2025/06/EX-Fr517-F1-2025_net.pdf", "https://iave.pt/wp-content/uploads/2025/06/EX-Fr517-F1-2025-CC-VD_net.pdf"),
    (2025, "Espanhol", 547, "F1", "https://iave.pt/wp-content/uploads/2025/06/EX-Esp547-F1-2025_net.pdf", "https://iave.pt/wp-content/uploads/2025/06/EX-Esp547-F1-2025-CC-VD_net.pdf"),
    (2025, "Ingles", 550, "F1", "https://iave.pt/wp-content/uploads/2025/06/EX-Ing550-F1-2025_net.pdf", "https://iave.pt/wp-content/uploads/2025/06/EX-Ing550-F1-2025-CC-VD_net.pdf"),
    (2025, "Historia A", 623, "F1", "https://iave.pt/wp-content/uploads/2025/06/EX-HistA623-F1-2025-V1_net.pdf", "https://iave.pt/wp-content/uploads/2025/06/EX-HistA623-F1-2025-CC-VD_net.pdf"),
    (2025, "Matematica A", 635, "F1", "https://iave.pt/wp-content/uploads/2025/06/EX-MatA635-F1-2025_net-1.pdf", "https://iave.pt/wp-content/uploads/2025/07/EX-MatA635-F1-2025-CC-VD_net.pdf"),
    (2025, "Portugues", 639, "F1", "https://iave.pt/wp-content/uploads/2025/06/EX-Port639-F1-2025-V1_net.pdf", "https://iave.pt/wp-content/uploads/2025/06/EX-Port639-F1-2025-CC-VD_net.pdf"),
    (2025, "Biologia e Geologia", 702, "F1", "https://iave.pt/wp-content/uploads/2025/06/EX-BG702-F1-2025-V1_net.pdf", "https://iave.pt/wp-content/uploads/2025/07/EX-BG702-F1-2025-CC-VD_net_2.pdf"),
    (2025, "Desenho A", 706, "F1", "https://iave.pt/wp-content/uploads/2025/06/EX-DesA706-F1-2025_net.pdf", "https://iave.pt/wp-content/uploads/2025/06/EX-DesA706-F1-2025-CC-VD_net.pdf"),
    (2025, "Geometria Descritiva A", 708, "F1", "https://iave.pt/wp-content/uploads/2025/06/EX-GDA708-F1-2025_net.pdf", "https://iave.pt/wp-content/uploads/2025/07/EX-GDA708-F1-2025-CC-VD_net.pdf"),
    (2025, "Economia A", 712, "F1", "https://iave.pt/wp-content/uploads/2025/06/EX-EconA712-F1-2025-V1_net.pdf", "https://iave.pt/wp-content/uploads/2025/07/EX-EconA712-F1-2025-CC-VD_net.pdf"),
    (2025, "Filosofia", 714, "F1", "https://iave.pt/wp-content/uploads/2025/06/EX-Fil714-F1-2025_V1_net.pdf", "https://iave.pt/wp-content/uploads/2025/06/EX-Fil714-F1-2025-CC-VD_net.pdf"),
    (2025, "Fisica e Quimica A", 715, "F1", "https://iave.pt/wp-content/uploads/2025/06/EX-FQA715-F1-2025-V1_net.pdf", "https://iave.pt/wp-content/uploads/2025/07/EX-FQA715-F1-2025-CC-VD_net.pdf"),
    (2025, "Geografia A", 719, "F1", "https://iave.pt/wp-content/uploads/2025/06/EX-GeoA719-F1-2025-V1_net-1.pdf", "https://iave.pt/wp-content/uploads/2025/06/EX-GeoA719-F1-2025-CC-VD_net.pdf"),
    (2025, "Historia B", 723, "F1", "https://iave.pt/wp-content/uploads/2025/06/EX-HistB723-F1-2025-V1_net.pdf", "https://iave.pt/wp-content/uploads/2025/07/EX-HistB723-F1-2025-CC-VD_net.pdf"),
    (2025, "Historia da Cultura e das Artes", 724, "F1", "https://iave.pt/wp-content/uploads/2025/06/EX-HCA724-F1-2025_net.pdf", "https://iave.pt/wp-content/uploads/2025/06/EX-HCA724-F1-2025-CC-VD_net.pdf"),
    (2025, "Latim A", 732, "F1", "https://iave.pt/wp-content/uploads/2025/06/EX-LatA732-1F-2025_net.pdf", "https://iave.pt/wp-content/uploads/2025/07/EX-LatA732-1F-2025-CC-VD_net.pdf"),
    (2025, "Literatura Portuguesa", 734, "F1", "https://iave.pt/wp-content/uploads/2025/06/EX-LitP734-F1-2025_net.pdf", "https://iave.pt/wp-content/uploads/2025/06/EX-LitP734-F1-2025-CC-VD_net.pdf"),
    (2025, "Matematica B", 735, "F1", "https://iave.pt/wp-content/uploads/2025/06/EX-MatB735-F1-2025_net-1.pdf", "https://iave.pt/wp-content/uploads/2025/07/EX-MatB735-F1-2025-CC-VD_net.pdf"),
    (2025, "Matematica Aplicada as Ciencias Sociais", 835, "F1", "https://iave.pt/wp-content/uploads/2025/06/EX-Macs835-F1-2025_net.pdf", "https://iave.pt/wp-content/uploads/2025/07/EX-Macs835-F1-2025-CC-VD_net.pdf"),
    (2025, "Portugues Lingua Nao Materna", 839, "F1", "https://iave.pt/wp-content/uploads/2025/06/EX-PLNM839-F1-2025_net.pdf", "https://iave.pt/wp-content/uploads/2024/06/EX-PLNM839-F1-2025-CC-VD_net.pdf"),
    (2025, "Espanhol (847)", 847, "F1", "https://iave.pt/wp-content/uploads/2025/06/EX-Esp847-F1-2025_net.pdf", "https://iave.pt/wp-content/uploads/2025/06/EX-Esp847-F1-2025-CC-VD_net.pdf"),
    (2025, "Mandarim", 848, "F1", "https://iave.pt/wp-content/uploads/2025/06/EX-Mand848-F1-2025_net.pdf", "https://iave.pt/wp-content/uploads/2025/06/EX-Mand848-F1-2025-CC-VD_net.pdf"),
    (2025, "Italiano", 849, "F1", "https://iave.pt/wp-content/uploads/2025/06/EX-Ita849-F1-2025_net.pdf", "https://iave.pt/wp-content/uploads/2025/06/EX-Ita849-F1-2025-CC-VD_net.pdf"),
    # ---------------------------------------------------------------- 2025, 2a Fase
    (2025, "Portugues Lingua Segunda", 138, "F2", "https://iave.pt/wp-content/uploads/2025/07/EX-Port138-F2-2025_net.pdf", "https://iave.pt/wp-content/uploads/2025/07/EX-Port138-F2-2025-CC-VD_net.pdf"),
    (2025, "Alemao", 501, "F2", "https://iave.pt/wp-content/uploads/2025/07/EX-Alm501-F2-2025_net-1.pdf", "https://iave.pt/wp-content/uploads/2025/07/EX-Alm501-F2-2025-CC-VD_net.pdf"),
    (2025, "Frances", 517, "F2", "https://iave.pt/wp-content/uploads/2025/07/EX-Fr517-F2-2025_net-1.pdf", "https://iave.pt/wp-content/uploads/2025/07/EX-Fr517-F2-2025-CC-VD_net.pdf"),
    (2025, "Espanhol", 547, "F2", "https://iave.pt/wp-content/uploads/2025/07/EX-Esp547-F2-2025_net-1.pdf", "https://iave.pt/wp-content/uploads/2025/07/EX-Esp547-F2-2025-CC-VD_net.pdf"),
    (2025, "Ingles", 550, "F2", "https://iave.pt/wp-content/uploads/2025/07/EX-Ing550-F2-2025_net.pdf", "https://iave.pt/wp-content/uploads/2025/07/EX-Ing550-F2-2025-CC-VD_net.pdf"),
    (2025, "Historia A", 623, "F2", "https://iave.pt/wp-content/uploads/2025/07/EX-HistA623-F2-2025-V1_net.pdf", "https://iave.pt/wp-content/uploads/2025/07/EX-HistA623-F2-2025-CC-VD_net.pdf"),
    (2025, "Matematica A", 635, "F2", "https://iave.pt/wp-content/uploads/2025/07/EX-MatA635-F2-2025_net.pdf", "https://iave.pt/wp-content/uploads/2025/07/EX-MatA635-F2-2025-CC-VD_net.pdf"),
    (2025, "Portugues", 639, "F2", "https://iave.pt/wp-content/uploads/2025/07/EX-Port639-F2-2025-V1_net.pdf", "https://iave.pt/wp-content/uploads/2025/07/EX-Port639-F2-2025-CC-VD_net.pdf"),
    (2025, "Biologia e Geologia", 702, "F2", "https://iave.pt/wp-content/uploads/2025/07/EX-BG702-F2-2025-V1_net.pdf", "https://iave.pt/wp-content/uploads/2025/07/EX-BG702-F2-2025-CC-VD_net.pdf"),
    (2025, "Desenho A", 706, "F2", "https://iave.pt/wp-content/uploads/2025/07/EX-DesA706-F2-2025_net-1.pdf", "https://iave.pt/wp-content/uploads/2025/07/EX-DesA706-F2-2025-CC-VD_net.pdf"),
    (2025, "Geometria Descritiva A", 708, "F2", "https://iave.pt/wp-content/uploads/2025/07/EX-GDA708-F2-2025_net.pdf", "https://iave.pt/wp-content/uploads/2025/07/EX-GDA708-F2-2025-CC-VD_net.pdf"),
    (2025, "Economia A", 712, "F2", "https://iave.pt/wp-content/uploads/2025/07/EX-EconA712-F2-2025-V1_net.pdf", "https://iave.pt/wp-content/uploads/2025/07/EX-EconA712-F2-2025-CC-VD_net.pdf"),
    (2025, "Filosofia", 714, "F2", "https://iave.pt/wp-content/uploads/2025/07/EX-Fil714-F2-2025_V1_net.pdf", "https://iave.pt/wp-content/uploads/2025/07/EX-Fil714-F2-2025-CC-VD_net.pdf"),
    (2025, "Fisica e Quimica A", 715, "F2", "https://iave.pt/wp-content/uploads/2025/07/EX-FQA715-F2-2025-V1_net.pdf", "https://iave.pt/wp-content/uploads/2025/07/EX-FQA715-F2-2025-CC-VD_net.pdf"),
    (2025, "Geografia A", 719, "F2", "https://iave.pt/wp-content/uploads/2025/07/EX-GeoA719-F2-2025-V1_net-1.pdf", "https://iave.pt/wp-content/uploads/2025/07/EX-GeoA719-F2-2025-CC-VD_net.pdf"),
    (2025, "Historia B", 723, "F2", "https://iave.pt/wp-content/uploads/2025/07/EX-HistB723-F2-2025-V1_net.pdf", "https://iave.pt/wp-content/uploads/2025/07/EX-HistB723-F2-2025-CC-VD_net.pdf"),
    (2025, "Literatura Portuguesa", 734, "F2", "https://iave.pt/wp-content/uploads/2025/07/EX-LitP734-F2-2025_net.pdf", "https://iave.pt/wp-content/uploads/2025/07/EX-LitP734-F2-2025-CC-VD_net-1.pdf"),
    (2025, "Historia da Cultura e das Artes", 724, "F2", "https://iave.pt/wp-content/uploads/2025/07/EX-HCA724-F2-2025_net.pdf", "https://iave.pt/wp-content/uploads/2025/07/EX-HCA724-F2-2025-CC-VD_net.pdf"),
    (2025, "Matematica B", 735, "F2", "https://iave.pt/wp-content/uploads/2025/07/EX-MatB735-F2-2025_net.pdf", "https://iave.pt/wp-content/uploads/2025/07/EX-MatB735-F2-2025-CC-VD_net.pdf"),
    (2025, "Matematica Aplicada as Ciencias Sociais", 835, "F2", "https://iave.pt/wp-content/uploads/2025/07/EX-Macs835-F2-2025_net.pdf", "https://iave.pt/wp-content/uploads/2025/07/EX-Macs835-F2-2025-CC-VD_net.pdf"),
    (2025, "Portugues Lingua Nao Materna", 839, "F2", "https://iave.pt/wp-content/uploads/2025/07/EX-PLNM839-F2-2025_net.pdf", "https://iave.pt/wp-content/uploads/2025/07/EX-PLNM839-F2-2025-CC-VD_net.pdf"),
    (2025, "Espanhol (847)", 847, "F2", "https://iave.pt/wp-content/uploads/2025/07/EX-Esp847-F2-2025_net-2.pdf", "https://iave.pt/wp-content/uploads/2025/07/EX-Esp847-F2-2025-CC-VD_net.pdf"),
    (2025, "Italiano", 849, "F2", "https://iave.pt/wp-content/uploads/2025/07/EX-Ita849-F2-2025_net-1.pdf", "https://iave.pt/wp-content/uploads/2025/07/EX-Ita849-F2-2025-CC-VD_net.pdf"),
    (2025, "Mandarim", 848, "F2", "https://iave.pt/wp-content/uploads/2025/07/EX-Mand848-F2-2025_net-1.pdf", "https://iave.pt/wp-content/uploads/2025/07/EX-Mand848-F2-2025-CC-VD_net.pdf"),
    # ---------------------------------------------------------------- 2025, Epoca Especial
    (2025, "Economia A", 712, "EE", "https://iave.pt/wp-content/uploads/2025/11/EX-EconA712-EE-2025.pdf", "https://iave.pt/wp-content/uploads/2025/11/EX-EconA712-EE-2025-CC.pdf"),
    (2025, "Ingles", 550, "EE", "https://iave.pt/wp-content/uploads/2025/11/EX-Ing550-EE-2025.pdf", "https://iave.pt/wp-content/uploads/2025/11/EX-Ing550-EE-2025-CC.pdf"),
    (2025, "Desenho A", 706, "EE", "https://iave.pt/wp-content/uploads/2025/11/EX-DesA706-EE-2025.pdf", "https://iave.pt/wp-content/uploads/2025/11/EX-DesA706-EE-2025-CC-VD.pdf"),
    (2025, "Matematica Aplicada as Ciencias Sociais", 835, "EE", "https://iave.pt/wp-content/uploads/2025/11/EX-Macs835-EE-2025.pdf", "https://iave.pt/wp-content/uploads/2025/11/EX-Macs835-EE-2025-CC.pdf"),
    (2025, "Historia A", 623, "EE", "https://iave.pt/wp-content/uploads/2025/08/EX-HistA623-EE-2025.pdf", "https://iave.pt/wp-content/uploads/2025/08/EX-HistA623-EE-2025-CC.pdf"),
    (2025, "Geografia A", 719, "EE", "https://iave.pt/wp-content/uploads/2025/08/EX-GeoA719-EE-2025.pdf", "https://iave.pt/wp-content/uploads/2025/08/EX-GeoA719-EE-2025-CC.pdf"),
    (2025, "Biologia e Geologia", 702, "EE", "https://iave.pt/wp-content/uploads/2025/08/EX-BG702-EE-2025.pdf", "https://iave.pt/wp-content/uploads/2025/08/EX-BG702-EE-2025-CC.pdf"),
    (2025, "Filosofia", 714, "EE", "https://iave.pt/wp-content/uploads/2025/08/EX-Fil714-EE-2025.pdf", "https://iave.pt/wp-content/uploads/2025/08/EX-Fil714-EE-2025-CC.pdf"),
    (2025, "Portugues", 639, "EE", "https://iave.pt/wp-content/uploads/2025/08/EX-Port639-EE-2025.pdf", "https://iave.pt/wp-content/uploads/2025/08/EX-Port639-EE-2025-CC.pdf"),
    (2025, "Geometria Descritiva A", 708, "EE", "https://iave.pt/wp-content/uploads/2025/08/EX-GDA708-EE-2025.pdf", "https://iave.pt/wp-content/uploads/2025/08/EX-GDA708-EE-2025-CC.pdf"),
    (2025, "Matematica A", 635, "EE", "https://iave.pt/wp-content/uploads/2025/08/EX-MatA635-EE-2025.pdf", "https://iave.pt/wp-content/uploads/2025/08/EX-MatA635-EE-2025-CC.pdf"),
    (2025, "Matematica B", 735, "EE", "https://iave.pt/wp-content/uploads/2025/08/EX-MatB735-EE-2025.pdf", "https://iave.pt/wp-content/uploads/2025/08/EX-MatB735-EE-2025-CC.pdf"),
    (2025, "Fisica e Quimica A", 715, "EE", "https://iave.pt/wp-content/uploads/2025/08/EX-FQA715-EE-2025.pdf", "https://iave.pt/wp-content/uploads/2025/08/EX-FQA715-EE-2025-CC.pdf"),
    # ---------------------------------------------------------------- 2024, 1a Fase
    (2024, "Portugues Lingua Segunda", 138, "F1", "https://iave.pt/wp-content/uploads/2024/06/EX-Port138-F1-2024_net.pdf", "https://iave.pt/wp-content/uploads/2024/06/EX-Port138-F1-2024-CC_VD_net.pdf"),
    (2024, "Frances", 517, "F1", "https://iave.pt/wp-content/uploads/2024/06/EX-Fr517-F1-2024-1.pdf", "https://iave.pt/wp-content/uploads/2024/06/EX-Fr517-F1-2024-CC-VD_net.pdf"),
    (2024, "Espanhol", 547, "F1", "https://iave.pt/wp-content/uploads/2024/06/EX-Esp547-F1-2024_net.pdf", "https://iave.pt/wp-content/uploads/2024/06/EX-Esp547-F1-2024-CC-VD_net.pdf"),
    (2024, "Alemao", 501, "F1", "https://iave.pt/wp-content/uploads/2024/06/EX-Alm501-F1-2024_net.pdf", "https://iave.pt/wp-content/uploads/2024/07/EX-Alm501-F1-2024-CC-VD_net.pdf"),
    (2024, "Ingles", 550, "F1", "https://iave.pt/wp-content/uploads/2024/06/EX-Ing550-F1-2024_net.pdf", "https://iave.pt/wp-content/uploads/2024/07/EX-Ing550-F1-2024-CC-VD_net.pdf"),
    (2024, "Historia A", 623, "F1", "https://iave.pt/wp-content/uploads/2024/06/EX-HistA623-F1-2024-V1_net-3.pdf", "https://iave.pt/wp-content/uploads/2024/06/EX-HistA623-F1-2024-CC-VD_net.pdf"),
    (2024, "Portugues", 639, "F1", "https://iave.pt/wp-content/uploads/2024/06/EX-Port639-F1-2024-V1_net.pdf", "https://iave.pt/wp-content/uploads/2024/06/EX-Port639-F1-2024-CC-VD_net.pdf"),
    (2024, "Matematica A", 635, "F1", "https://iave.pt/wp-content/uploads/2024/06/EX-MatA635-F1-2024_net.pdf", "https://iave.pt/wp-content/uploads/2024/07/EX-MatA635-F1-2024-CC-VD_net.pdf"),
    (2024, "Biologia e Geologia", 702, "F1", "https://iave.pt/wp-content/uploads/2024/06/EX-BG702-F1-2024-V1_net.pdf", "https://iave.pt/wp-content/uploads/2024/07/EX-BG702-F1-2024-CC-VD_04-07.pdf"),
    (2024, "Desenho A", 706, "F1", "https://iave.pt/wp-content/uploads/2024/06/EX-DesA706-F1-2024_net.pdf", "https://iave.pt/wp-content/uploads/2024/07/EX-DesA706-F1-2024-CC-VD_net.pdf"),
    (2024, "Geometria Descritiva A", 708, "F1", "https://iave.pt/wp-content/uploads/2024/06/EX-GDA708-F1-2024_net.pdf", "https://iave.pt/wp-content/uploads/2024/07/EX-GDA708-F1-2024-CC-VD_net.pdf"),
    (2024, "Economia A", 712, "F1", "https://iave.pt/wp-content/uploads/2024/06/EX-EconA712-F1-2024-V1_net.pdf", "https://iave.pt/wp-content/uploads/2024/07/EX-EconA712-F1-2024-CC-VD_net.pdf"),
    (2024, "Fisica e Quimica A", 715, "F1", "https://iave.pt/wp-content/uploads/2024/06/EX-FQA715-F1-2024-V1_net-3.pdf", "https://iave.pt/wp-content/uploads/2024/07/EX-FQA715-F1-2024-CC-VD_net.pdf"),
    (2024, "Filosofia", 714, "F1", "https://iave.pt/wp-content/uploads/2024/06/EX-Fil714-F1-2024_V1_net.pdf", "https://iave.pt/wp-content/uploads/2024/06/EX-Fil714-F1-2024-CC-VD_net.pdf"),
    (2024, "Geografia A", 719, "F1", "https://iave.pt/wp-content/uploads/2024/06/EX-GeoA719-F1-2024-V1_net-2.pdf", "https://iave.pt/wp-content/uploads/2024/06/EX-GeoA719-F1-2024-CC-VD_net.pdf"),
    (2024, "Historia da Cultura das Artes", 724, "F1", "https://iave.pt/wp-content/uploads/2024/06/EX-HCA724-F1-2024_net.pdf", "https://iave.pt/wp-content/uploads/2024/06/EX-HCA724-F1-2024-CC-VD_27-6.pdf"),
    (2024, "Historia B", 723, "F1", "https://iave.pt/wp-content/uploads/2024/06/EX-HistB723-F1-2024-V1_net.pdf", "https://iave.pt/wp-content/uploads/2024/07/EX-HistB723-F1-2024-CC-VD_net.pdf"),
    (2024, "Latim A", 732, "F1", "https://iave.pt/wp-content/uploads/2024/06/EX-LatA732-1F-2024_net.pdf", "https://iave.pt/wp-content/uploads/2024/07/EX-LatA732-1F-2024-CC-VD_net.pdf"),
    (2024, "Literatura Portuguesa", 734, "F1", "https://iave.pt/wp-content/uploads/2024/06/EX-LitP734-F1-2024.pdf", "https://iave.pt/wp-content/uploads/2024/07/EX-LitP734-F1-2024-CC-VD_net.pdf"),
    (2024, "Matematica B", 735, "F1", "https://iave.pt/wp-content/uploads/2024/06/EX-MatB735-F1-2024_net.pdf", "https://iave.pt/wp-content/uploads/2024/07/EX-MatB735-F1-2024-CC-VD_net.pdf"),
    (2024, "Matematica Aplicada as Ciencias Sociais", 835, "F1", "https://iave.pt/wp-content/uploads/2024/06/EX-Macs835-F1-2024_net.pdf", "https://iave.pt/wp-content/uploads/2024/07/EX-Macs835-F1-2024-Adp-Br-CC-VD_net.pdf"),
    (2024, "Portugues Lingua Nao Materna", 839, "F1", "https://iave.pt/wp-content/uploads/2024/06/PF-PLNM839-F1-2024_net.pdf", "https://iave.pt/wp-content/uploads/2024/06/PF-PLNM94-839-F1-2024-CC-VD_net.pdf"),
    (2024, "Espanhol (847)", 847, "F1", "https://iave.pt/wp-content/uploads/2024/06/EX-Esp847-F1-2024_net.pdf", "https://iave.pt/wp-content/uploads/2024/06/EX-Esp847-F1-2024-CC-VD_net.pdf"),
    (2024, "Italiano", 849, "F1", "https://iave.pt/wp-content/uploads/2024/06/EX-Ita849-F1-2024_net.pdf", "https://iave.pt/wp-content/uploads/2024/06/EX-Ita849-F1-2024-CC-VD_net.pdf"),
    (2024, "Mandarim", 848, "F1", "https://iave.pt/wp-content/uploads/2024/06/EX-Mand848-F1-2024_net.pdf", "https://iave.pt/wp-content/uploads/2024/06/EX-Mand848-F1-2024-CC-VD_net-1.pdf"),
    # ---------------------------------------------------------------- 2024, 2a Fase
    (2024, "Portugues Lingua Segunda", 138, "F2", "https://iave.pt/wp-content/uploads/2024/07/EX-Port138-F2-2024_net-1.pdf", "https://iave.pt/wp-content/uploads/2024/07/EX-Port138-F2-2024-CC-VD.pdf"),
    (2024, "Alemao", 501, "F2", "https://iave.pt/wp-content/uploads/2024/07/EX-Alm501-F2-2024_net.pdf", "https://iave.pt/wp-content/uploads/2024/07/EX-Alm501-F2-2024-CC-VD_net.pdf"),
    (2024, "Frances", 517, "F2", "https://iave.pt/wp-content/uploads/2024/07/EX-Fr517-F2-2024_net.pdf", "https://iave.pt/wp-content/uploads/2024/07/EX-Fr517-F2-2024-CC-VD_net.pdf"),
    (2024, "Ingles", 550, "F2", "https://iave.pt/wp-content/uploads/2024/07/EX-Ing550-F2-2024_net.pdf", "https://iave.pt/wp-content/uploads/2024/07/EX-Ing550-F2-2024-CC-VD_net.pdf"),
    (2024, "Espanhol", 547, "F2", "https://iave.pt/wp-content/uploads/2024/07/EX-Esp547-F2-2024_net.pdf", "https://iave.pt/wp-content/uploads/2024/07/EX-Esp547-F2-2024-CC-VD_net.pdf"),
    (2024, "Historia A", 623, "F2", "https://iave.pt/wp-content/uploads/2024/07/EX-HistA623-F2-2024-V1_net-4.pdf", "https://iave.pt/wp-content/uploads/2024/07/EX-HistA623-F2-2024-CC-VD_net.pdf"),
    (2024, "Matematica A", 635, "F2", "https://iave.pt/wp-content/uploads/2024/07/EX-MatA635-F2-2024_net.pdf", "https://iave.pt/wp-content/uploads/2024/07/EX-MatA635-F2-2024-CC-VD_net.pdf"),
    (2024, "Portugues", 639, "F2", "https://iave.pt/wp-content/uploads/2024/07/EX-Port639-F2-2024-V1_net.pdf", "https://iave.pt/wp-content/uploads/2024/07/EX-Port639-F2-2024-CC-VD_net.pdf"),
    (2024, "Biologia e Geologia", 702, "F2", "https://iave.pt/wp-content/uploads/2024/07/EX-BG702-F2-2024-V1_net.pdf", "https://iave.pt/wp-content/uploads/2024/07/EX-BG702-F2-2024-CC-VD_net.pdf"),
    (2024, "Desenho A", 706, "F2", "https://iave.pt/wp-content/uploads/2024/07/EX-DesA706-F2-2024_net.pdf", "https://iave.pt/wp-content/uploads/2024/07/EX-DesA706-F2-2024-CC-VD_net.pdf"),
    (2024, "Geometria Descritiva A", 708, "F2", "https://iave.pt/wp-content/uploads/2024/07/EX-GDA708-F2-2024_net.pdf", "https://iave.pt/wp-content/uploads/2024/07/EX-GDA708-F2-2024-CC-VD_net.pdf"),
    (2024, "Economia A", 712, "F2", "https://iave.pt/wp-content/uploads/2024/07/EX-EconA712-F2-2024-V1_net.pdf", "https://iave.pt/wp-content/uploads/2024/07/EX-EconA712-F2-2024-CC-VD_net.pdf"),
    (2024, "Filosofia", 714, "F2", "https://iave.pt/wp-content/uploads/2024/07/EX-Fil714-F2-2024_V1_net.pdf", "https://iave.pt/wp-content/uploads/2024/07/EX-Fil714-F2-2024-CC_VD_net.pdf"),
    (2024, "Fisica e Quimica A", 715, "F2", "https://iave.pt/wp-content/uploads/2024/07/EX-FQA715-F2-2024-V1-1.pdf", "https://iave.pt/wp-content/uploads/2024/07/EX-FQA715-F2-2024-CC-VD_net.pdf"),
    (2024, "Historia da Cultura e das Artes", 724, "F2", "https://iave.pt/wp-content/uploads/2024/07/EX-HCA724-F2-2024_net.pdf", "https://iave.pt/wp-content/uploads/2024/07/EX-HCA724-F2-2024-CC-VD_net.pdf"),
    (2024, "Geografia A", 719, "F2", "https://iave.pt/wp-content/uploads/2024/07/EX-GeoA719-F2-2024-V1_net.pdf", "https://iave.pt/wp-content/uploads/2024/07/EX-GeoA719-F2-2024-CC-VD_net-1.pdf"),
    (2024, "Historia B", 723, "F2", "https://iave.pt/wp-content/uploads/2024/07/EX-HistB723-F2-2024-V1_net.pdf", "https://iave.pt/wp-content/uploads/2024/07/EX-HistB723-F2-2024-CC-VD_net.pdf"),
    (2024, "Matematica B", 735, "F2", "https://iave.pt/wp-content/uploads/2024/07/EX-MatB735-F2-2024_net.pdf", "https://iave.pt/wp-content/uploads/2024/07/EX-MatB735-F2-2024-CC-VD_net.pdf"),
    (2024, "Literatura Portuguesa", 734, "F2", "https://iave.pt/wp-content/uploads/2024/07/EX-LitP734-F2-2024_net.pdf", "https://iave.pt/wp-content/uploads/2024/07/EX-LitP734-F2-2024-CC-VD.pdf"),
    (2024, "Latim A", 732, "F2", "https://iave.pt/wp-content/uploads/2024/07/EX-LatA732-2F-2024_net.pdf", "https://iave.pt/wp-content/uploads/2024/07/EX-LatA732-2F-2024-CC-VD.pdf"),
    (2024, "Matematica Aplicada as Ciencias Sociais", 835, "F2", "https://iave.pt/wp-content/uploads/2024/07/EX-Macs835-F2-2024_net.pdf", "https://iave.pt/wp-content/uploads/2024/07/EX-Macs835-F2-2024-CC-VD_net.pdf"),
    (2024, "Portugues Lingua Nao Materna", 839, "F2", "https://iave.pt/wp-content/uploads/2024/07/PF-PLNM839-F2-2024_net.pdf", "https://iave.pt/wp-content/uploads/2024/07/PF-PLNM94-839-F2-2024-CC-VD_net.pdf"),
    (2024, "Espanhol (847)", 847, "F2", "https://iave.pt/wp-content/uploads/2024/07/EX-Esp847-F2-2024_net.pdf", "https://iave.pt/wp-content/uploads/2024/07/EX-Esp847-F2-2024-CC-VD_net.pdf"),
    (2024, "Italiano", 849, "F2", "https://iave.pt/wp-content/uploads/2024/07/EX-Ita849-F2-2024.pdf", "https://iave.pt/wp-content/uploads/2024/07/EX-Ita849-F2-2024-CC-VD_net.pdf"),
    # ---------------------------------------------------------------- 2024, Epoca Especial
    (2024, "Matematica Aplicada as Ciencias Sociais", 835, "EE", "https://iave.pt/wp-content/uploads/2025/10/EX-Macs835-EE-2024_1out_net.pdf", "https://iave.pt/wp-content/uploads/2024/08/EX-Macs835-EE-2024-CC_net-1.pdf"),
    (2024, "Fisica e Quimica A", 715, "EE", "https://iave.pt/wp-content/uploads/2024/08/EX-FQA715-EE-2024_net.pdf", "https://iave.pt/wp-content/uploads/2024/08/EX-FQA715-EE-2024-CC_net.pdf"),
    (2024, "Biologia e Geologia", 702, "EE", "https://iave.pt/wp-content/uploads/2024/08/EX-BG702-EE-2024_net.pdf", "https://iave.pt/wp-content/uploads/2024/08/EX-BG702-EE-2024-CC_net.pdf"),
    (2024, "Portugues", 639, "EE", "https://iave.pt/wp-content/uploads/2024/08/EX-Port639-EE-2024.pdf", "https://iave.pt/wp-content/uploads/2024/08/EX-Port639-EE-2024-CC.pdf"),
    (2024, "Filosofia", 714, "EE", "https://iave.pt/wp-content/uploads/2024/08/EX-Fil714-EE-2024_net.pdf", "https://iave.pt/wp-content/uploads/2024/08/EX-Fil714-EE-2024-CC-VD_net.pdf"),
    (2024, "Geografia A", 719, "EE", "https://iave.pt/wp-content/uploads/2024/08/EX-GeoA719-EE-2024.pdf", "https://iave.pt/wp-content/uploads/2024/08/EX-GeoA719-EE-2024-CC.pdf"),
    (2024, "Matematica B", 735, "EE", "https://iave.pt/wp-content/uploads/2024/08/EX-MatB735-EE-2024.pdf", "https://iave.pt/wp-content/uploads/2024/08/EX-MatB735-EE-2024-CC.pdf"),
    (2024, "Matematica A", 635, "EE", "https://iave.pt/wp-content/uploads/2024/08/EX-MatA635-EE-2024_net.pdf", "https://iave.pt/wp-content/uploads/2024/08/EX-MatA635-EE-2024-CC_net.pdf"),
    (2024, "Espanhol (847)", 847, "EE", "https://iave.pt/wp-content/uploads/2024/08/EX-Esp847-EE-2024_net.pdf", "https://iave.pt/wp-content/uploads/2024/08/EX-Esp847-EE-2024-CC_net.pdf"),
    (2024, "Economia A", 712, "EE", "https://iave.pt/wp-content/uploads/2024/08/EX-EconA712-EE-2024_net.pdf", "https://iave.pt/wp-content/uploads/2024/08/EX-EconA712-EE-2024-CC_net.pdf"),
    (2024, "Geometria Descritiva A", 708, "EE", "https://iave.pt/wp-content/uploads/2024/08/EX-GDA708-EE-2024.pdf", "https://iave.pt/wp-content/uploads/2024/08/EX-GDA708-EE-2024-CC.pdf"),
]

# Subjects also covered by pt_exams/PHEB (2006-2023 only) — informational,
# not excluded here, since year alone (2024-2025) already guarantees
# disjointness from that benchmark's coverage.
PT_EXAMS_SUBJECTS = {"Matematica A", "Portugues", "Historia A", "Geografia A",
                     "Biologia e Geologia", "Filosofia"}

if __name__ == "__main__":
    from collections import Counter
    years = Counter(e[0] for e in EXAMS)
    subjects = {e[1] for e in EXAMS}
    print(f"{len(EXAMS)} exam sittings registered")
    print(f"years: {dict(years)}")
    print(f"{len(subjects)} distinct subjects")
    print(f"{len(subjects - PT_EXAMS_SUBJECTS)} subjects entirely outside pt_exams/PHEB coverage")
