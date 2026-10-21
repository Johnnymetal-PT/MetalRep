"""
Testes da ficha da revisão de sexta-feira.

O que se fixa aqui são as REGRAS do manual (fronteiras dos semáforos, o que é um projeto A,
B, C ou Parado, quando uma tarefa vai ao Backlog), não a rede: tudo o que se testa é puro.
Se alguém mudar um limiar, o teste falha e obriga a mudar também o manual.

Correr da raiz do repositório:
    python -m unittest scripts.tests.test_pg_revisao_sexta
"""

import unittest
from datetime import date

from scripts import pg_revisao_sexta as mod

HOJE = date(2026, 10, 9)  # sexta-feira


def tarefa(**kw):
    base = {
        "stage_id": [1, "Sprint in Progress"],
        "write_date": "2026-10-08 10:00:00",
        "date_last_stage_update": "2026-10-01 10:00:00",
        "allocated_hours": 4.0,
        "effective_hours": 1.0,
        "date_deadline": "2026-10-20 00:00:00",
        "user_ids": [7],
    }
    base.update(kw)
    return base


class TestEtapas(unittest.TestCase):
    def test_variantes_de_nome_caem_no_mesmo_grupo(self):
        self.assertEqual("sprint_backlog", mod.grupo_etapa("Lista de pendências da sprint"))
        self.assertEqual("sprint_em_curso", mod.grupo_etapa("Sprint em andamento"))
        self.assertEqual("sprint_completa", mod.grupo_etapa("Old Completed Sprint"))
        self.assertEqual("backlog", mod.grupo_etapa("Backlog"))

    def test_etapa_desconhecida_nao_e_sprint(self):
        # Uma etapa que não conhecemos não pode ser tratada como compromisso.
        self.assertEqual("outra", mod.grupo_etapa("Em estudo"))
        self.assertFalse(mod.em_sprint(mod.grupo_etapa("Em estudo")))
        self.assertFalse(mod.em_sprint(mod.grupo_etapa(None)))


class TestClassificarTarefa(unittest.TestCase):
    def test_tarefa_em_ordem_nao_pede_acao(self):
        c = mod.classificar_tarefa(tarefa(), HOJE)
        self.assertEqual("Sem ação.", c["acao"])
        self.assertTrue(c["completa_tres_campos"])

    def test_parada_ha_mais_de_30_dias_pede_as_sete_perguntas(self):
        c = mod.classificar_tarefa(tarefa(write_date="2026-08-20 10:00:00"), HOJE)
        self.assertTrue(c["parada_30"])
        self.assertFalse(c["parada_90"])
        self.assertIn("sete perguntas", c["acao"])

    def test_fronteira_dos_30_dias(self):
        # 30 dias exatos ainda não é «mais de 30».
        c30 = mod.classificar_tarefa(tarefa(write_date="2026-09-09 10:00:00"), HOJE)
        c31 = mod.classificar_tarefa(tarefa(write_date="2026-09-08 10:00:00"), HOJE)
        self.assertFalse(c30["parada_30"])
        self.assertTrue(c31["parada_30"])

    def test_parada_ha_mais_de_90_dias_devolve_ao_backlog(self):
        c = mod.classificar_tarefa(tarefa(write_date="2026-06-01 10:00:00"), HOJE)
        self.assertTrue(c["parada_90"])
        self.assertIn("Backlog", c["acao"])

    def test_sprint_complete_aberta_manda_fechar(self):
        c = mod.classificar_tarefa(tarefa(stage_id=[2, "Sprint Complete"]), HOJE)
        self.assertIn("Fechar", c["acao"])

    def test_backlog_nao_recebe_acao(self):
        # O Backlog não é compromisso: a revisão não o toca.
        c = mod.classificar_tarefa(tarefa(stage_id=[3, "Backlog"], allocated_hours=0,
                                          date_deadline=False, user_ids=[]), HOJE)
        self.assertEqual("", c["acao"])

    def test_sem_horas_sem_prazo_e_vencida(self):
        c = mod.classificar_tarefa(tarefa(allocated_hours=0), HOJE)
        self.assertIn("Estimar", c["acao"])
        c = mod.classificar_tarefa(tarefa(date_deadline=False), HOJE)
        self.assertIn("prazo", c["acao"])
        c = mod.classificar_tarefa(tarefa(date_deadline="2026-10-01 00:00:00"), HOJE)
        self.assertTrue(c["vencida"])
        self.assertIn("Replanear", c["acao"])

    def test_prazo_hoje_nao_esta_vencido(self):
        c = mod.classificar_tarefa(tarefa(date_deadline="2026-10-09 00:00:00"), HOJE)
        self.assertFalse(c["vencida"])


class TestSemaforos(unittest.TestCase):
    def test_horas_fronteiras(self):
        self.assertEqual("verde", mod.semaforo_horas(80, 100)[0])
        self.assertEqual("amarelo", mod.semaforo_horas(80.1, 100)[0])
        self.assertEqual("amarelo", mod.semaforo_horas(110, 100)[0])
        self.assertEqual("vermelho", mod.semaforo_horas(110.1, 100)[0])

    def test_sem_horas_alocadas_nao_inventa_cor(self):
        self.assertEqual(("sem_dados", None), mod.semaforo_horas(50, 0))

    def test_atividade(self):
        self.assertEqual("verde", mod.semaforo_atividade(10))
        self.assertEqual("amarelo", mod.semaforo_atividade(9.9))
        self.assertEqual("vermelho", mod.semaforo_atividade(0))

    def test_quadro(self):
        self.assertEqual("verde", mod.semaforo_quadro(9, 10))
        self.assertEqual("amarelo", mod.semaforo_quadro(55, 100))
        self.assertEqual("vermelho", mod.semaforo_quadro(54, 100))
        self.assertEqual("sem_dados", mod.semaforo_quadro(0, 0))

    def test_prazo_provisorio(self):
        self.assertEqual("sem_dados", mod.semaforo_prazo(None, HOJE))
        self.assertEqual("verde", mod.semaforo_prazo("2026-10-09 00:00:00", HOJE))
        self.assertEqual("amarelo", mod.semaforo_prazo("2026-09-25 00:00:00", HOJE))
        self.assertEqual("vermelho", mod.semaforo_prazo("2026-09-24 00:00:00", HOJE))

    def test_cor_global_e_a_pior_com_dados(self):
        self.assertEqual("vermelho", mod.cor_global(["verde", "vermelho", "amarelo"]))
        self.assertEqual("amarelo", mod.cor_global(["sem_dados", "verde", "amarelo"]))
        self.assertEqual("sem_dados", mod.cor_global(["sem_dados"]))
        self.assertEqual("sem_dados", mod.cor_global([]))


class TestTipoDeProjeto(unittest.TestCase):
    def test_tipos(self):
        self.assertEqual("Parado", mod.tipo_projeto(0, 500))
        self.assertEqual("A", mod.tipo_projeto(40, 10))
        self.assertEqual("A", mod.tipo_projeto(5, 300))
        self.assertEqual("B", mod.tipo_projeto(10, 100))
        self.assertEqual("B", mod.tipo_projeto(39.9, 100))
        self.assertEqual("C", mod.tipo_projeto(9.9, 100))


class TestTimesheet(unittest.TestCase):
    def test_dias_uteis_ignoram_fim_de_semana(self):
        dias = mod.dias_uteis(date(2026, 10, 5), date(2026, 10, 11))
        self.assertEqual(5, len(dias))
        self.assertEqual(date(2026, 10, 5), mod.segunda_da_semana(HOJE))

    def test_dia_sem_horas_linha_sem_tarefa_e_excesso_por_cliente(self):
        dias = mod.dias_uteis(date(2026, 10, 5), HOJE)
        linhas = [
            {"date": "2026-10-05", "unit_amount": 4.0, "task_id": [1, "t"], "project_id": [10, "p"]},
            {"date": "2026-10-05", "unit_amount": 4.0, "task_id": False, "project_id": [11, "q"]},
            {"date": "2026-10-06", "unit_amount": 3.0, "task_id": [2, "t"], "project_id": [12, "r"]},
        ]
        # Os projetos 10 e 11 são do mesmo cliente: somam-se (4 + 4 = 8 > 7,5).
        r = mod.verificar_timesheet(linhas, dias, {10: "ACME", 11: "ACME", 12: "Outro"})
        self.assertEqual(["2026-10-07", "2026-10-08", "2026-10-09"], r["dias_sem_horas"])
        self.assertEqual(1, r["linhas_sem_tarefa"])
        self.assertEqual([("2026-10-05", "ACME", 8.0)], r["excesso_por_cliente_dia"])

    def test_clientes_diferentes_nao_se_somam(self):
        dias = mod.dias_uteis(date(2026, 10, 5), date(2026, 10, 5))
        linhas = [
            {"date": "2026-10-05", "unit_amount": 7.5, "task_id": [1, "t"], "project_id": [10, "p"]},
            {"date": "2026-10-05", "unit_amount": 7.5, "task_id": [2, "t"], "project_id": [12, "r"]},
        ]
        r = mod.verificar_timesheet(linhas, dias, {10: "A", 12: "B"})
        self.assertEqual([], r["excesso_por_cliente_dia"])
        self.assertEqual([], r["dias_sem_horas"])


class TestFicha(unittest.TestCase):
    def test_ficha_minima_renderiza_e_nao_traz_emojis(self):
        ctx = {"hoje": "2026-10-09", "hoje_dia_semana": 4, "nome": "Pessoa", "login": "p@x.pt",
               "url": "https://exemplo.odoo.com",
               "a": {"contagem": {"abertas": 3, "em_sprint": 2, "sprint_completa_abertas": 1,
                                  "sprint_parada_30": 1, "sprint_parada_90": 0,
                                  "sprint_sem_horas": 1, "sprint_sem_prazo": 1,
                                  "sprint_vencidas": 0, "sprint_completas_3_campos": 1},
                     "para_rever": [], "para_rever_total": 0,
                     "timesheet": {"por_dia": {}, "dias_sem_horas": [], "linhas_sem_tarefa": 0,
                                   "excesso_por_cliente_dia": [], "total_linhas": 0},
                     "dias_semana": ["2026-10-05"]},
               "b": {"projetos": [], "sem_gestor_em_curso": [], "quadro_na_cor": False}}
        md = mod.render_markdown(ctx)
        self.assertIn("Parte A", md)
        self.assertIn("Parte B", md)
        self.assertIn("Nenhuma linha sai do bloco sem dono e sem hora", md)
        # A consola do Windows (cp1252) rebenta com emojis; a ficha usa palavras.
        self.assertTrue(all(ord(ch) < 0x1F000 for ch in md))

    def test_aviso_quando_nao_e_sexta(self):
        ctx = {"hoje": "2026-10-07", "hoje_dia_semana": 2, "nome": "P", "login": "p@x.pt",
               "url": "https://exemplo.odoo.com"}
        self.assertIn("Hoje não é sexta-feira", mod.render_markdown(ctx))


if __name__ == "__main__":
    unittest.main()
