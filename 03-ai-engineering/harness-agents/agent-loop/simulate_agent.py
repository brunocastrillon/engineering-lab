"""Roda o agente contra uma API *simulada* (sem chave, sem custo), usando o SDK oficial de verdade.

Uso:  python simulate_agent.py
"""
import json, shutil
from pathlib import Path
import anthropic
try:                      # versões recentes do SDK usam httpx2; as anteriores, httpx
    import httpx2 as httpx
except ImportError:
    import httpx
import agent

BUGGY = "def media(valores):\n    return sum(valores) / (len(valores) - 1)\n"
FIXED = "def media(valores):\n    return sum(valores) / len(valores)\n"

def reset():
    (agent.WORKDIR / "calc.py").write_text(BUGGY)
    for d in (agent.ROOT / "memory", agent.ROOT / "traces"):
        shutil.rmtree(d, ignore_errors=True)
    shutil.rmtree(agent.WORKDIR / ".pytest_cache", ignore_errors=True)

def text(t): return {"type": "text", "text": t}
def tool(i, name, **inp): return {"type": "tool_use", "id": f"toolu_{i}", "name": name, "input": inp}

def mock_client(script):
    requests, it = [], iter(script)
    def handler(request):
        body = json.loads(request.content); requests.append(body)
        stop, blocks = next(it)
        return httpx.Response(200, json={"id": "msg_x", "type": "message", "role": "assistant",
            "model": body["model"], "content": blocks, "stop_reason": stop, "stop_sequence": None,
            "usage": {"input_tokens": 10, "output_tokens": 5}})
    client = anthropic.Anthropic(api_key="test", http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    return client, requests

def last_results(requests):
    return requests[-1]["messages"][-1]["content"]

# A) caminho feliz
reset()
client, reqs = mock_client([
    ("tool_use", [text("Vou olhar os arquivos."), tool(1, "list_files")]),
    ("tool_use", [tool(2, "read_file", path="calc.py")]),
    ("tool_use", [tool(3, "run_command", command="pytest")]),
    ("tool_use", [tool(4, "write_file", path="calc.py", content=FIXED)]),
    ("tool_use", [tool(5, "run_command", command="pytest")]),
    ("end_turn", [text("Corrigi: o divisor era len(valores) - 1.")]),
])
ok, final = agent.run("Faça o pytest passar.", client)
print("A) feliz:", ok, "|", final, "| passos:", len(reqs))
assert ok and (agent.WORKDIR / "calc.py").read_text() == FIXED
r1 = reqs[1]["messages"][-1]["content"][0]
assert r1["type"] == "tool_result" and "calc.py" in r1["content"]          # list_files voltou ao modelo
assert reqs[0]["tools"][0]["name"] == "list_files" and "Procedimento" in reqs[0]["system"]
print("   system prompt (resumo):", reqs[0]["system"].splitlines()[3:5])

# F) memória episódica: a próxima execução enxerga a anterior
print("   episodes.jsonl:", (agent.EPISODES.read_text().strip()))

# B) guardrails
reset()
client, reqs = mock_client([
    ("tool_use", [tool(1, "run_command", command="rm -rf /")]),
    ("tool_use", [tool(2, "read_file", path="../agent.py")]),
    ("tool_use", [tool(3, "write_file", path="calc.py", content=FIXED)]),
    ("end_turn", [text("Feito.")]),
])
ok, final = agent.run("Faça o pytest passar.", client)
res1 = reqs[1]["messages"][-1]["content"][0]; res2 = reqs[2]["messages"][-1]["content"][0]
print("B) guardrail comando :", res1.get("is_error"), "|", res1["content"])
print("B) guardrail caminho :", res2.get("is_error"), "|", res2["content"])
assert res1["is_error"] and res2["is_error"] and ok

# C) "terminei" prematuro: o harness confere e recusa
reset()
client, reqs = mock_client([
    ("end_turn", [text("Pronto, já corrigi!")]),
    ("tool_use", [tool(1, "write_file", path="calc.py", content=FIXED)]),
    ("end_turn", [text("Agora sim.")]),
])
ok, final = agent.run("Faça o pytest passar.", client)
injected = reqs[1]["messages"][-1]["content"]
print("C) prematuro:", ok, "| mensagem do harness:", injected.splitlines()[0])
assert ok and "Verificação independente" in injected

# D) repetição sem progresso
reset()
client, reqs = mock_client([("tool_use", [tool(i, "list_files")]) for i in range(1, 6)] +
                           [("end_turn", [text("Não sei mais o que fazer.")])] * 3)
ok, final = agent.run("Faça o pytest passar.", client)
rep = reqs[4]["messages"][-1]["content"][0]
print("D) repetição:", rep.get("is_error"), "|", rep["content"], "| resultado final:", ok)
assert rep["is_error"] and not ok

# E) orçamento
reset()
client, reqs = mock_client([("tool_use", [tool(i, "read_file", path="calc.py")]) for i in range(1, 40)])
ok, final = agent.run("Faça o pytest passar.", client)
print("E) orçamento:", ok, "|", final, "| chamadas à API:", len(reqs))
assert not ok and len(reqs) == agent.MAX_STEPS

# F) segunda execução enxerga o episódio anterior
reset()
agent.save_episode("Faça o pytest passar.", "sucesso", 6)
client, reqs = mock_client([("end_turn", [text("ok")])] * 3)
agent.run("Outra tarefa", client)
print("F) memória episódica no system prompt:", reqs[0]["system"].splitlines()[-1])
assert "sucesso" in reqs[0]["system"]

# traces
t = sorted(agent.TRACES.glob("*.jsonl"))[-1]
print("\ntrace (última execução):"); print(t.read_text()[:600])

# G) decodificação: UTF-8 legível e bytes inválidos nunca derrubam
assert agent.decode("Execução → falhou".encode("utf-8")) == "Execução → falhou"
assert isinstance(agent.decode(b"\x81\x8d\x8f\x90\x9d"), str)
print("G) decode: UTF-8 legível e bytes inválidos viram texto, sem exceção")

# H) timeout na verificação vira 'reprovado', não exceção
import subprocess as _sp
_orig = agent.subprocess.run
def _timeout(*a, **k): raise _sp.TimeoutExpired(cmd="pytest", timeout=60)
agent.subprocess.run = _timeout
ok, report = agent.verify()
agent.subprocess.run = _orig
print("H) timeout em verify():", ok, "|", report)
assert ok is False and "tempo limite" in report

reset()   # deixa o workspace de volta com o bug original

print("\nTODOS OS TESTES PASSARAM (8 cenários)")
