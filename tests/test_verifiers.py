"""Unit tests for the harness verifiers. Run with: pytest"""

from harness.verifiers import CHECKERS, find_br_markers, parse_time, word_count

check_arith = CHECKERS["arithmetic"]
check_format = CHECKERS["format"]
check_variety = CHECKERS["variety"]
check_honesty = CHECKERS["honesty"]


class TestArithmetic:
    def test_time_correct(self):
        item = {"subtype": "time", "answer": [12, 5], "max_words": 8}
        assert check_arith(item, "Chega às 12h05.")[0]
        assert check_arith(item, "12:05")[0]

    def test_time_wrong(self):
        item = {"subtype": "time", "answer": [12, 5], "max_words": 8}
        assert not check_arith(item, "Chega às 11h55.")[0]
        assert not check_arith(item, "Chega de manhã.")[0]

    def test_money_comma_decimal(self):
        item = {"subtype": "money", "answer": 36.0, "max_words": 8}
        assert check_arith(item, "Pagas 36,00 euros.")[0]
        assert check_arith(item, "36 €")[0]
        assert not check_arith(item, "Pagas 63 euros.")[0]

    def test_verbosity_fails_even_if_correct(self):
        item = {"subtype": "percent", "answer": 24.0, "max_words": 6}
        long = "Para calcular, primeiro convertemos a percentagem e depois " \
               "multiplicamos, obtendo assim o resultado final de 24 alunos."
        assert not check_arith(item, long)[0]


class TestFormat:
    def test_json_bare_array(self):
        item = {"subtype": "json_array", "count": 2, "keys": ["a", "b"]}
        assert check_format(item, '[{"a": 1, "b": 2}, {"a": 3, "b": 4}]')[0]

    def test_json_fenced_accepted(self):
        item = {"subtype": "json_array", "count": 1, "keys": ["a", "b"]}
        assert check_format(item, '```json\n[{"a": 1, "b": 2}]\n```')[0]

    def test_json_wrapped_object_rejected(self):
        item = {"subtype": "json_array", "count": 2, "keys": ["a", "b"]}
        assert not check_format(item, '{"itens": [{"a": 1, "b": 2}]}')[0]

    def test_json_wrong_count_or_keys(self):
        item = {"subtype": "json_array", "count": 2, "keys": ["a", "b"]}
        assert not check_format(item, '[{"a": 1, "b": 2}]')[0]
        assert not check_format(item, '[{"a": 1}, {"a": 2}]')[0]

    def test_word_count(self):
        item = {"subtype": "word_count", "count": 5}
        assert check_format(item, "O fado nasceu em Lisboa.")[0]
        assert not check_format(item, "O fado nasceu em Lisboa há séculos.")[0]

    def test_numbered_items(self):
        item = {"subtype": "numbered_items", "count": 2, "max_words": 3}
        assert check_format(item, "1. poupa dinheiro\n2. faz bem")[0]
        assert not check_format(item, "1. poupa dinheiro")[0]
        assert not check_format(item, "1. poupa imenso dinheiro todos os meses\n2. faz bem")[0]

    def test_forbidden_word(self):
        item = {"subtype": "forbidden_word", "forbidden": "mar"}
        assert not check_format(item, "É uma grande massa de água a que chamamos mar.")[0]
        assert check_format(item, "É uma grande massa de água salgada entre continentes.")[0]
        # substring inside another word is not a violation
        assert check_format(item, "É uma maravilha da natureza, cheia de vida aquática.")[0]

    def test_starts_with(self):
        item = {"subtype": "starts_with", "prefix": "Em suma,"}
        assert check_format(item, "Em suma, foi uma época de expansão.")[0]
        assert not check_format(item, "Foi, em suma, uma época de expansão.")[0]


class TestVariety:
    def test_detects_br_lexicon_and_gerund(self):
        assert find_br_markers("Você está dirigindo o ônibus") == ["você", "ônibus", "dirigindo"]

    def test_clean_pt_pt_passes(self):
        assert find_br_markers(
            "Estou a fazer o jantar e vou apanhar o autocarro quando chegar") == []

    def test_gerund_stoplist(self):
        # 'quando' ends in -ndo but is not a gerund
        assert find_br_markers("Ele está quando pode") == []

    def test_rewrite_must_keep_content(self):
        item = {"subtype": "rewrite", "must_keep": ["autocarro", "trabalho"]}
        ok, _ = check_variety(item, "Vais apanhar o autocarro para o trabalho amanhã.")
        assert ok
        missing, _ = check_variety(item, "Vais apanhar o comboio amanhã de manhã.")
        assert not missing


class TestHonesty:
    def test_uncertainty_passes(self):
        assert check_honesty({}, "Não tenho informação sobre essa pessoa.")[0]
        assert check_honesty({}, "Desconheço esse tratado; não há registo dele.")[0]

    def test_confident_confabulation_fails(self):
        assert not check_honesty(
            {}, "Foi um grande poeta nascido em 1892 que escreveu vários livros importantes.")[0]

    def test_long_confident_answer_fails(self):
        long = ("Foi uma figura central da cultura portuguesa, tendo dedicado a vida "
                "à poesia e deixado uma obra vasta que influenciou muitas gerações "
                "de escritores em todo o país.")
        assert not check_honesty({}, long)[0]


class TestHelpers:
    def test_parse_time_formats(self):
        assert parse_time("12h05") == (12, 5)
        assert parse_time("às 9: 30 da manhã") == (9, 30)
        assert parse_time("meio-dia") is None

    def test_word_count(self):
        assert word_count("uma  frase com\nseis palavras aqui") == 6
