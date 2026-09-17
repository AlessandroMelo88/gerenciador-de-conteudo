"""Testes da escolha justa de vídeos por canal de origem na fila de download."""
from src.fair_queue import channel_cap, fair_pick


def _c(cid, vid):
    return {'channel_id': cid, 'youtube_video_id': vid}


def _ids(videos):
    return [v['youtube_video_id'] for v in videos]


class TestChannelCap:
    def test_divide_a_janela_entre_os_canais_ativos(self):
        # 10 vagas, 4 canais -> 3 por canal (arredonda pra cima, senão sobra vaga sem dono)
        assert channel_cap(window=10, active_channels=4) == 3

    def test_canal_demais_pra_janela_ainda_tem_uma_vaga(self):
        assert channel_cap(window=10, active_channels=50) == 1

    def test_sem_canal_ativo_nao_limita_a_janela(self):
        assert channel_cap(window=10, active_channels=0) == 10

    def test_teto_explicito_vence_o_calculo(self):
        assert channel_cap(window=10, active_channels=4, override=1) == 1


class TestFairPick:
    def test_um_canal_prolifico_nao_leva_todas_as_vagas(self):
        candidates = [_c(1, 'a1'), _c(1, 'a2'), _c(1, 'a3'), _c(2, 'b1'), _c(3, 'c1')]

        picked = _ids(fair_pick(candidates, occupancy={}, deficit=3, cap=1))

        assert picked == ['a1', 'b1', 'c1']

    def test_intercala_canais_respeitando_a_ordem_de_cada_um(self):
        candidates = [_c(1, 'a1'), _c(1, 'a2'), _c(2, 'b1'), _c(2, 'b2')]

        picked = _ids(fair_pick(candidates, occupancy={}, deficit=4, cap=2))

        assert picked == ['a1', 'b1', 'a2', 'b2']

    def test_quem_ja_ocupa_vaga_entra_depois_de_quem_nao_ocupa(self):
        candidates = [_c(1, 'a1'), _c(2, 'b1')]

        picked = _ids(fair_pick(candidates, occupancy={1: 2, 2: 0}, deficit=2, cap=5))

        assert picked == ['b1', 'a1']

    def test_ocupacao_atual_conta_contra_o_teto_do_canal(self):
        candidates = [_c(1, 'a1'), _c(1, 'a2'), _c(2, 'b1')]

        picked = _ids(fair_pick(candidates, occupancy={1: 1}, deficit=3, cap=2))

        assert picked == ['b1', 'a1']

    def test_canal_no_teto_e_ignorado_por_completo(self):
        candidates = [_c(1, 'a1'), _c(2, 'b1')]

        picked = _ids(fair_pick(candidates, occupancy={1: 3}, deficit=2, cap=3))

        assert picked == ['b1']

    def test_nunca_devolve_mais_que_o_deficit(self):
        candidates = [_c(1, 'a1'), _c(2, 'b1'), _c(3, 'c1')]

        picked = _ids(fair_pick(candidates, occupancy={}, deficit=2, cap=5))

        assert picked == ['a1', 'b1']

    def test_sobra_de_vaga_volta_pra_quem_tem_fila(self):
        # canal 2 só tem 1 vídeo; as vagas restantes voltam para o canal 1 até o teto
        candidates = [_c(1, 'a1'), _c(1, 'a2'), _c(1, 'a3'), _c(2, 'b1')]

        picked = _ids(fair_pick(candidates, occupancy={}, deficit=4, cap=3))

        assert picked == ['a1', 'b1', 'a2', 'a3']

    def test_video_sem_canal_nao_quebra(self):
        candidates = [{'channel_id': None, 'youtube_video_id': 'x1'}]

        assert _ids(fair_pick(candidates, occupancy={}, deficit=1, cap=1)) == ['x1']
