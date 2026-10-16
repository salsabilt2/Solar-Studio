# AI evaluation

`eval/questions.json` contains 40 controlled questions: 20 whose answers are present in a synthetic panel PDF, and 20 whose answers are absent. `eval/run.py` uploads that PDF and checks the live answer text and cited sources. It writes every answer and failure to `eval/results.json`.

Run it with an **administrator** account, because ordinary accounts have a five-request daily allowance:

```sh
SOLAR_EVAL_URL=http://localhost:8000 \
SOLAR_EVAL_EMAIL=admin@example.com \
SOLAR_EVAL_PASSWORD='your-admin-password' \
python eval/run.py
```

This evaluation needs a configured OpenAI API key. No live result is published yet because this workspace has no key. The fixture tests source grounding and unsupported-question refusal; it does not prove accuracy on every real manufacturer's PDF. A later public case study should include the actual `results.json`, qualitative failure review, and model/version used. The checker intentionally uses simple expected terms and citation/refusal signals, so human review of failures remains necessary.
